"""Open-tool synthesis and timing for a BoomTile: Yosys area + OpenSTA fmax.

The open-tool BoomTile synthesis path: no Cadence Genus, no commercial sky130
kit. Chipyard elaborates the
config on the chisel worker, CACTI characterizes the SRAMs it generated, Yosys
maps the BoomTile against the open_pdks sky130A standard cells on the vlsi
worker, and OpenSTA times the resulting netlist.

Yosys reports area but no timing, and OpenSTA reports timing but no area, so the
two run back to back inside one call on the vlsi worker: obj_dir is worker-local
because the cluster has no shared filesystem, and the netlist OpenSTA reads is
the one Yosys just wrote there.

``synthesize_and_time`` is the entry point, called by improve_perf_area.py for
the per-iteration BoomTile synthesis and by perf_area_experiment_tool.py for the
LLM's sub-block A/B experiments. ``_save_variant_results`` is the other half:
it writes the result -- reports, area_estimates.json, synthesis_log.md -- into a
branch's files dir, in the layout db.py documents.
"""

import json
import os
import re
import shutil
import time
import traceback

from chia.base.ChiaFunction import ChiaFunction
from sky130_vlsi.hammer_syn_node import Sky130OpenSynNode, _collect_reports
from sky130_vlsi.opensta_timing import run_opensta
from sky130_vlsi.state_def import SynthesisResult, TimingResult

# Installed on the vlsi worker by perf_area_eff_cluster.yaml's worker_setup_commands.
SKY130A_PATH = os.environ.get(
    "CHIA_SKY130A_PATH", "/home/ray/conda-sky130/share/pdk/sky130A")
YOSYS_BIN = os.environ.get("CHIA_YOSYS_BIN", "/home/ray/conda-yosys/bin/yosys")
# OpenSTA ships (bundled with OpenROAD) in the chia-cacti image. CACTI itself
# is dispatched from the driver, not from here -- see constants.CACTI_PATH.
STA_BIN = os.environ.get("CHIA_STA_BIN", "sta")

_STDCELL_LIB_DIR = "libs.ref/sky130_fd_sc_hd/lib"

# The corner Yosys maps at (the sky130 plugin's `type: extra`). Matching it here
# keeps ABC's delay model and fmax consistent; optimistic in absolute terms, but
# this flow ranks variants rather than signing off.
STA_CORNER = "tt_025C_1v80"

# Worker-local scratch, not a shared path: see the module docstring. Only a
# fallback -- every real call site passes constants.SYN_OBJ_SCRATCH_DIR, which
# this matches.
SYN_OBJ_DIR = "/scratch/perf_area_eff"
SYN_TIMEOUT = 172800     # 48h
# 50MHz for OpenSTA; Yosys/ABC read the same period from design-open.yml.
CLOCK_PERIOD_NS = 20.0

# Non-synthesizable simulation collateral, which Yosys' Verilog frontend rejects
# outright where Genus merely ignores it. It lives under TestHarness, never under
# the BOOM tile. Two kinds, both matched here because the A/B experiment tool
# reads gen-collateral straight off disk and so has no filter of its own:
#   - firtool's behavioral clock sources, which declare `timeunit`
#   - DPI-C imports (SimUART.v and friends), whose `input string` args Yosys
#     cannot parse. ChiselBuildNode drops these on the main build path only.
_BEHAVIORAL_RE = re.compile(
    r'^\s*time(unit|precision)\b|^\s*import\s+"DPI-C"', re.MULTILINE)


def _drop_behavioral_sources(
    gen_src: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Drop simulation-only sources that Yosys cannot read."""
    kept, dropped = [], []
    for name, contents in gen_src:
        (dropped if _BEHAVIORAL_RE.search(contents) else kept).append(name)
    if dropped:
        print(f"      dropped {len(dropped)} simulation-only source(s): "
              f"{', '.join(sorted(dropped))}")
    keep = set(kept)
    return [(n, c) for n, c in gen_src if n in keep]


# Yosys gives every cacti_ macro its Liberty area, so the design-hierarchy roll-up
# already counts the SRAMs. Break them out anyway: a total that mixes macro and
# standard-cell area says little about either. The roll-up's flat cell list tallies
# every macro instance in the design, and a macro is a blackbox cell whose area
# therefore only surfaces as the area of a wrapper module holding it alone.
_STAT_MODULE_RE = re.compile(r"^=== (\S+) ===$", re.MULTILINE)
_STAT_MODULE_AREA_RE = re.compile(r"Chip area for module '\\?[^']+':\s*([\d.]+)")
_STAT_CELL_LIST_RE = re.compile(r"^\s+Number of cells:")
_STAT_CELL_RE = re.compile(r"^\s+(\S+)\s+(\d+)\s*$")


def _stat_cell_counts(body: str) -> dict[str, int]:
    """Read the indented ``<cell type> <count>`` list after ``Number of cells:``."""
    counts: dict[str, int] = {}
    inside = False
    for line in body.splitlines():
        if _STAT_CELL_LIST_RE.match(line):
            inside = True
            continue
        if inside:
            m = _STAT_CELL_RE.match(line)
            if not m:
                inside = False
                continue
            counts[m.group(1)] = int(m.group(2))
    return counts


_LIB_CELL_RE = re.compile(r"^\s*cell\s*\(\s*([A-Za-z0-9_]+)\s*\)", re.MULTILINE)
_LIB_AREA_RE = re.compile(r"^\s*area\s*:\s*([0-9.]+)", re.MULTILINE)


def _macro_unit_areas(
    cacti_sram_libs: list[dict[str, str]] | None,
    corner: str = STA_CORNER,
) -> dict[str, float]:
    """``cell name -> area`` straight out of the CACTI Liberty we generated.

    The Liberty is the authority on a macro's area -- Yosys reads the same
    number out of it -- and unlike the wrapper-module heuristic below it
    survives `flatten`, which dissolves the wrappers into the top module.
    """
    out: dict[str, float] = {}
    for lib in cacti_sram_libs or []:
        contents = lib.get("lib_contents") or lib.get("lib_content_by_corner") or {}
        if "lib_content" in lib and not contents:
            contents = {"tt_025C_1v80": lib["lib_content"]}
        body = contents.get(corner) or next(iter(contents.values()), None)
        if not body:
            continue
        cell = _LIB_CELL_RE.search(body)
        area = _LIB_AREA_RE.search(body)
        if cell and area:
            out[cell.group(1)] = float(area.group(1))
    return out


def _sram_macro_area(
    reports: dict[str, str],
    prefix: str = "cacti_",
    cacti_sram_libs: list[dict[str, str]] | None = None,
) -> float | None:
    """Area of the SRAM macros within the Yosys area total, or None if unavailable.

    Macro counts come from the stat report's design hierarchy, which is a flat
    roll-up and so is unaffected by `flatten`. Per-macro area comes from the
    CACTI Liberty when we have it, and otherwise from the wrapper module that
    instantiates the macro -- a fallback that `flatten` removes.
    """
    stat = next(
        (b for n, b in reports.items() if n.endswith(".synth_stat.txt")), None)
    if not stat:
        return None
    if "=== design hierarchy ===" in stat:
        head, counts_from = stat.split("=== design hierarchy ===", 1)
    else:
        # `flatten` leaves one module and no hierarchy roll-up, so the macro
        # instances are counted in the top module's own cell list instead.
        head = stat
        m = _STAT_MODULE_RE.split(stat)
        counts_from = m[2] if len(m) > 2 else stat

    unit = _macro_unit_areas(cacti_sram_libs)
    if not unit:
        # No Liberty to hand: fall back to the wrapper modules, each of which
        # instantiates exactly one macro and carries its area.
        parts = _STAT_MODULE_RE.split(head)
        for _, body in zip(parts[1::2], parts[2::2]):
            cells = _stat_cell_counts(body)
            area = _STAT_MODULE_AREA_RE.search(body)
            if not area or len(cells) != 1:
                continue
            (cell, count), = cells.items()
            if cell.startswith(prefix) and count == 1:
                unit[cell] = float(area.group(1))

    counted = {c: n for c, n in _stat_cell_counts(counts_from).items()
               if c.startswith(prefix)}
    if counted and not unit:
        print("  [synthesis] WARNING: macros present but neither the CACTI "
              "Liberty nor a wrapper module gives their area; reporting "
              "sram_macro_area as unavailable rather than guessing")
        return None

    total = 0.0
    for cell, count in counted.items():
        if cell not in unit:
            print(f"  [synthesis] WARNING: no area found for macro {cell}; "
                  f"the SRAM macro subtotal is understated")
            continue
        total += count * unit[cell]
    return total


def _write_macro_liberties(
    obj_dir: str,
    cacti_sram_libs: list[dict[str, str]] | None,
    corner: str,
) -> list[str]:
    """Write the CACTI Liberty files for one corner and return their paths.

    Sky130OpenSynNode hands Hammer its own copies from a temp dir it deletes
    afterwards, so OpenSTA needs a set that outlives synthesis.
    """
    if not cacti_sram_libs:
        return []
    lib_dir = os.path.join(obj_dir, "sta_libs")
    os.makedirs(lib_dir, exist_ok=True)
    paths = []
    for lib in cacti_sram_libs:
        contents = lib.get("lib_contents") or {}
        # Same backwards-compatible single-corner shape Sky130SynNode accepts.
        if "lib_content" in lib and not contents:
            contents = {"tt_025C_1v80": lib["lib_content"]}
        body = contents.get(corner)
        if body is None:
            print(f"  [timing] WARNING: {lib.get('name')} has no {corner} Liberty; "
                  f"OpenSTA will not know its timing")
            continue
        path = os.path.join(lib_dir, f"{lib['name']}_{corner}.lib")
        with open(path, "w") as f:
            f.write(body)
        paths.append(path)
    return paths


@ChiaFunction(resources={"VLSI": 1, "Syn": 0})
def synthesize_and_time(
    generated_src_files: list[tuple[str, str]],
    vlsi_top: str,
    obj_dir: str = SYN_OBJ_DIR,
    cacti_sram_libs: list[dict[str, str]] | None = None,
    clock_period_ns: float = CLOCK_PERIOD_NS,
    timeout_seconds: int = SYN_TIMEOUT,
    flatten: bool = False,
) -> tuple[SynthesisResult, TimingResult]:
    """Map ``vlsi_top`` with Yosys, then time the mapped netlist with OpenSTA.

    ``flatten`` inserts a Yosys ``flatten`` before ``abc``. Off by default: see
    hammer_driver_open._flatten_step for what it buys and what it costs. It
    reaches the driver as an environment variable because Hammer runs it as a
    subprocess of this worker.
    """
    os.environ["CHIA_YOSYS_FLATTEN"] = "1" if flatten else "0"
    shutil.rmtree(obj_dir, ignore_errors=True)
    os.makedirs(obj_dir, exist_ok=True)
    print(f"  [synthesis] {vlsi_top}: {len(generated_src_files)} source files, "
          f"{len(cacti_sram_libs) if cacti_sram_libs else 0} CACTI macros, "
          f"flatten={'on' if flatten else 'off'}, obj_dir={obj_dir}")

    node = Sky130OpenSynNode(
        sky130a_path=SKY130A_PATH,
        yosys_bin=YOSYS_BIN,
        # Sorted: Yosys reads these in order, and the order changes the netlist
        # it produces. Without this the same RTL synthesized twice comes out
        # different -- a build's directory walk and the DB's sorted rows give
        # two different orders.
        input_files=sorted(generated_src_files),
        vlsi_top=vlsi_top,
        obj_dir=obj_dir,
        timeout_seconds=timeout_seconds,
        cacti_sram_libs=cacti_sram_libs,
    )
    t0 = time.time()
    try:
        syn = node.syn()
    except Exception as e:
        # Recover whatever reports landed on disk rather than propagating, so a
        # Yosys crash still comes back with something to debug.
        print(f"  [synthesis] {vlsi_top} RAISED after {time.time() - t0:.1f}s: {e}")
        syn = SynthesisResult(
            success=False, stdout="",
            stderr=f"synthesis raised:\n{traceback.format_exc()}",
            returncode=-1, reports=_collect_reports(obj_dir),
        )
    print(f"  [synthesis] {vlsi_top}: {'OK' if syn.success else 'FAILED'} "
          f"[{time.time() - t0:.1f}s]")
    if not syn.success:
        # Hammer's yosys plugin ignores yosys' exit code and only fails later, on
        # the missing mapped netlist, so the real cause is in the tool transcript
        # on stdout -- the traceback on stderr just reports the missing file.
        print(f"  [synthesis] stdout tail: {syn.stdout[-3000:] if syn.stdout else '(empty)'}")
        print(f"  [synthesis] stderr tail: {syn.stderr[-1000:] if syn.stderr else '(empty)'}")
        return syn, TimingResult(
            success=False, stdout="", stderr="synthesis failed; timing not attempted",
            returncode=-1,
        )

    # Every cell in the netlist has to be covered, so the CACTI macro Liberties
    # go in alongside the standard cells.
    liberty_files = [os.path.join(
        SKY130A_PATH, _STDCELL_LIB_DIR, f"sky130_fd_sc_hd__{STA_CORNER}.lib")]
    liberty_files += _write_macro_liberties(obj_dir, cacti_sram_libs, STA_CORNER)

    t1 = time.time()
    timing = run_opensta(
        netlist_path=os.path.join(obj_dir, "syn-rundir", f"{vlsi_top}.mapped.v"),
        top_module=vlsi_top,
        liberty_files=liberty_files,
        clock_period_ns=clock_period_ns,
        sta_bin=STA_BIN,
        work_dir=os.path.join(obj_dir, "sta"),
    )
    print(f"  [timing] {vlsi_top}: {'OK' if timing.success else 'FAILED'} "
          f"[{time.time() - t1:.1f}s]")
    if not timing.success:
        print(f"  [timing] stderr tail: {timing.stderr[-1000:] if timing.stderr else '(empty)'}")
    # Carry the transcript back with the synthesis reports.
    syn.reports.update({f"sta/{name}": body for name, body in timing.reports.items()})
    return syn, timing


def _save_variant_results(opt_dir, boom_tile_module, result, area, elapsed):
    """Save synthesis results into the variant's directory."""
    # area_estimates.json
    area_estimates = {boom_tile_module: area} if area is not None else {}
    with open(opt_dir / "area_estimates.json", "w") as f:
        json.dump(area_estimates, f)

    # Raw reports JSON (includes syn-rundir contents)
    report_filename = f"synthesis_reports_{boom_tile_module}_child_reports.json"
    with open(opt_dir / report_filename, "w") as f:
        json.dump(result.reports, f)

    # Individual report files preserving directory structure
    run_dir = opt_dir / "synthesis_reports" / f"{boom_tile_module}_child"
    os.makedirs(run_dir, exist_ok=True)
    for rpt_name, rpt_content in result.reports.items():
        rpt_path = run_dir / rpt_name
        os.makedirs(rpt_path.parent, exist_ok=True)
        with open(rpt_path, "w") as rpt_f:
            rpt_f.write(rpt_content)

    # stdout/stderr/summary
    with open(run_dir / "stdout.txt", "w") as f:
        f.write(result.stdout or "")
    with open(run_dir / "stderr.txt", "w") as f:
        f.write(result.stderr or "")
    with open(run_dir / "summary.txt", "w") as f:
        area_str = f"{area:.2f}" if area is not None else "N/A"
        f.write(
            f"module: {boom_tile_module}\n"
            f"success: {result.success}\n"
            f"returncode: {result.returncode}\n"
            f"area: {area_str}\n"
            f"elapsed: {elapsed:.1f}s\n"
            f"reports: {len(result.reports)}\n"
        )

    # synthesis_log.md
    status = "OK" if result.success else "FAILED"
    area_str = f"{area:.2f}" if area is not None else "N/A"
    log_lines = [
        "# BoomTile Synthesis Log\n",
        f"## {boom_tile_module}: {status}, area={area_str}, elapsed={elapsed:.1f}s\n",
    ]
    if not result.success:
        log_lines.append(
            f"```\nreturncode={result.returncode}\n"
            f"stderr (last 2000):\n{result.stderr[-2000:]}\n```\n"
        )
    log_lines.append(f"\n## Reports collected: {len(result.reports)}\n")
    for rpt_name in sorted(result.reports.keys()):
        log_lines.append(f"- {rpt_name}")
    with open(opt_dir / "synthesis_log.md", "w") as f:
        f.write("\n".join(log_lines))

    print(f"  Saved {len(result.reports)} reports + stdout/stderr to {run_dir}/")
