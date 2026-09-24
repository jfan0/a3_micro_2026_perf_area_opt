"""Chia loop that improves BoomTile performance-area efficiency.

Each iteration loads a parent variant, asks an LLM to edit Chisel, rebuilds, then
synthesizes and simulates in parallel and records the result as a child branch.

Objective:

    maximize   perf_area_eff = embench_speed_score / total_cell_area

subject to two hard gates, measured every iteration:

    * perf_area_eff must not fall below the PARENT's
    * every riscv-test that passed on the SEED must still pass

Frequency needs no gate of its own: the speed score is
``fmax x geomean(reference_cycles / our_cycles)``, so fmax is already a factor of
the objective and a separate floor would price it twice.

Every term comes from open tools: Yosys reports area (including the CACTI SRAM
macros), OpenSTA reports fmax (tt_025C_1v80, the same corner Yosys maps at), and
embench's ROI cycle counters give the per-benchmark times the speed score is
built from. Cycle counts come from those ROI counters and NOT from the TMA
performance counters: the WithBoomTMACounters mixin is applied only by
MegaBoomChiaBigCacheConfig, so on this flow's MediumBoomV3Config target TMA
would silently yield no signal at all.

When the DB is empty there is no parent to optimize, so the flow first runs
``seed_flow()``: it resets chipyard to the unmodified base RTL, builds,
synthesizes and benchmarks it, and stores that as the seed ("baseline") branch --
the first DB entry. It is the reference the riscv-test gate measures against.

Usage -- submitted as a Ray job from the REPO ROOT on the head (README.md's
"Running" section lists every flag):
    chia job submit --working-dir . \\
        -- python examples/perf_area_eff_opt/improve_perf_area.py --seed-only
    chia job submit --working-dir . \\
        -- python examples/perf_area_eff_opt/improve_perf_area.py --branch baseline
    chia job stop --kill-tracked-pids <submission id>
"""

import argparse
import difflib
import json
import os
import re
import shutil
import signal
import sys
import time
from pathlib import Path
from uuid import uuid4

# Put ``examples/`` on sys.path for the sibling-package imports below
# (``common.*``, ``perf_area_eff_opt.*``). Run from the checkout, it is this file's
# grandparent. Submitted with ``chia job submit --working-dir .``, this file is
# Ray's uploaded copy instead, and the imports must still come from the checkout
# the installed ``chia`` belongs to (env.yml installs it editable from this repo):
# the modules resolve the benchmark ELFs and RUNTIME_ENV's py_modules from their
# own ``__file__``, and an upload holds only what .gitignore let through.
if __package__ in (None, ""):
    _here = Path(__file__).resolve()
    _examples_dir = _here.parent.parent
    if "runtime_resources" in _here.parts:
        # The checkout is read from the editable install's record, not from
        # find_spec("chia"): the job puts its working_dir on PYTHONPATH, ahead of
        # the editable finder, so find_spec resolves back into the upload.
        import json
        from importlib.metadata import PackageNotFoundError, distribution
        from urllib.parse import unquote, urlparse
        try:
            _url = json.loads(distribution("chialoops").read_text("direct_url.json") or "{}")
        except PackageNotFoundError:
            _url = {}
        if _url.get("dir_info", {}).get("editable"):
            _examples_dir = Path(unquote(urlparse(_url["url"]).path)) / "examples"
    sys.path.insert(0, str(_examples_dir))

import ray
from ray.util.placement_group import placement_group, remove_placement_group
from ray.util.scheduling_strategies import (
    NodeAffinitySchedulingStrategy,
    PlacementGroupSchedulingStrategy,
)

from chia.base.ChiaFunction import ChiaFunction, chia_cancel, get

# Build / verilator / synthesis-prep primitives now live in common (the old
# standalone timing_backend.py is gone — its verbatim-shared helpers and the
# non-debug build/verilator variants were folded into common.*).
from common.build import build_all_thread_variants, build_with_debug_retry
from common.verilator import dispatch_verilator_tests
from common.common_nodes import (
    _parse_verilog_modules,
    _resolve_boom_tile_module,
    collect_diff,
    load_prompt,
    parse_area_from_reports,
    reset_and_apply_diff,
    run_cacti_macrocompiler_prep,
)
from common.common_helpers import format_test_error

from perf_area_eff_opt.constants import (
    AREA_REPORT_LLM_PATH,
    AREA_REPORT_SUFFIXES,
    BOOM_REPO_PATH,
    BUILD_CONFIG,
    BUILD_CONFIG_PACKAGE,
    CACTI_PATH,
    CHIPYARD_PATH,
    DB_DIR,
    IMPROVE_PERF_AREA_PROMPT_PATH,
    IPC_REPORT_LLM_PATH,
    LLM_BACKEND,
    LLM_DEFAULT_MODELS,
    LLM_EFFORT,
    LLM_EFFORT_LEVELS,
    LLM_ENV,
    STA_REPORT_LLM_PATH,
    HISTORY_REPORTS_LLM_DIR,
    HISTORY_REPORT_BRANCHES,
    STA_REPORT_SUFFIXES,
    SYN_OBJ_SCRATCH_DIR,
    resolve_report,
)
from perf_area_eff_opt.common_constants import RUNTIME_ENV
from perf_area_eff_opt.db import PerfAreaEffDB, parse_worst_slack
from perf_area_eff_opt.boom_tile_syn_open import _save_variant_results
from perf_area_eff_opt.llm_backend import LLMDebugger, LLMSpec, prompt_llm
from perf_area_eff_opt.perf_area_experiment_tool import (
    ChipyardBashTool,
    PerfAreaExperimentTool,
)

# Synthesis + timing in one call, and the SRAM-macro area split. Yosys reports
# area but no timing and OpenSTA the reverse, so synthesize_and_time runs both
# back to back on the vlsi worker and returns (SynthesisResult, TimingResult) --
# the area and fmax this objective needs.
from perf_area_eff_opt.boom_tile_syn_open import (
    CLOCK_PERIOD_NS,
    STA_CORNER,
    _drop_behavioral_sources,
    _sram_macro_area,
    synthesize_and_time,
)

# Cycle counts + correctness measurement, from the embench_isa_tests module, so
# every branch's files_dir comes out in the same shape and two branches are
# directly diffable.
from perf_area_eff_opt.embench_isa_tests import (
    EMBENCH_DIR,
    EMBENCH_TIMEOUT_SCALE,
    ISA_DIR,
    ISA_TIMEOUT_CYCLES,
    classify_outcome,
    load_embench,
    load_isa,
    parse_roi,
    write_embench_results,
    write_isa_results,
)


def load_and_configure_test_binaries(
    include_asm: bool = True,
    include_embench: bool = True,
) -> tuple[list, list]:
    """Load the embench benchmarks and the riscv-tests ISA suite.

    Returns ``(embench, isa)`` separately, because the two are consumed
    differently: embench supplies the cycle counts the objective is built from,
    while the ISA tests are purely the correctness gate. The caller concatenates
    them for dispatch and re-splits the results by name.

    The binaries come from the ``examples/benchmarks`` submodule through
    embench_isa_tests' loaders: 19 embench benchmarks and 239 rv64gc ISA tests.

    Every binary runs 1-threaded (embench_isa_tests.VERILATOR_THREADS), which
    keeps ``build_all_thread_variants`` to a single build rather than one per
    distinct thread count.
    """
    embench = load_embench(None, EMBENCH_TIMEOUT_SCALE) if include_embench else []
    isa = load_isa(None, ISA_TIMEOUT_CYCLES) if include_asm else []
    # The loaders only warn about a missing directory, and an empty suite would
    # otherwise surface much later as a build that produced no variants.
    for wanted, tests, where in ((include_embench, embench, EMBENCH_DIR),
                                 (include_asm, isa, ISA_DIR)):
        if wanted and not tests:
            raise FileNotFoundError(
                f"no test binaries under {where}; build examples/benchmarks first "
                f"(see examples/benchmarks/README.md)")
    return embench, isa

PRELIMINARY_GENERATED_SRC_DIR = "/home/ray/chipyard/preliminary-generated-src/"

# make -j for the chisel build: the one chisel_build worker has its 16-vCPU VM
# to itself (perf_area_eff_cluster.yaml). Keep the two in step -- this is the
# only thing that turns extra cores on that VM into a shorter build.
MAKE_JOBS = 16

# Per-flow synthesis ceiling. Yosys on a BoomTile runs in under an hour, so this
# is generous rather than load-bearing, but the verilator-failure retry loop can
# repeat the synth dispatch up to max_debug_retries+1 times per run.
SYNTHESIS_TIMEOUT_SECONDS = 172800  # 48 hours

# Name of the seed (baseline) branch created from unmodified RTL.
SEED_BRANCH_NAME = "baseline"

# riscv-tests that fail on this config's UNMODIFIED RTL, from the baseline
# (237/239). Both exercise misaligned data accesses, which BOOM does not
# implement -- the -p variant asserts, the -v variant times out in the trap
# handler. They are excused from the debug-retry loop so it does not spend every
# attempt, plus a full rebuild and re-simulation each time, chasing RTL no agent
# edit caused. The seed re-derives this set by measurement; it is only a
# fallback for the seed run itself, where there is no parent to compare against.
BASELINE_KNOWN_FAILURES = {"rv64ui-p-ma_data", "rv64ui-v-ma_data"}

# dispatch_verilator_tests defaults to cancelling the whole queue after 4
# failures, or 600 s after the first one. Both have to be off here, exactly as
# the baseline driver turned them off: the baseline already fails the ma_data
# tests, so the defaults would early-exit the 258-run queue partway through and
# _measure would then see a truncated result set -- a mean IPC over whichever
# benchmarks happened to finish, which reads as a design change rather than as a
# cancelled dispatch. A failing test here is a result to record, not a reason to
# abandon the measurement.
_DISPATCH_LIMITS = {
    "max_failures": 10_000,
    "failure_timeout_seconds": float("inf"),
}


def _artifact_refs(artifacts_by_threads: dict) -> dict:
    """``ray.put`` each build artifact so the test fan-out shares one copy.

    ``dispatch_verilator_tests`` forwards whatever it is handed into every
    task's argument list, and Ray serializes a by-value argument once per
    submission. At this suite's size that is 258 tests x a ~43 MB simulator
    binary — ~11 GB of driver-owned objects against the head's 6.4 GB object
    store, which spills and then leaves every later fetch queued "waiting for
    available memory". The synthesis dispatched just before the suite is what
    pays for it: its Verilog and CACTI liberty arguments cannot be moved to the
    VLSI worker, so it sits in PENDING_NODE_ASSIGNMENT behind the whole queue
    instead of running alongside it.

    Ray dereferences a top-level ObjectRef argument before the task body runs,
    so ``run_verilator_test`` still receives a ``BuildArtifact``. This is the
    same trick the baseline measurement uses.
    """
    return {n: ray.put(a) for n, a in artifacts_by_threads.items()}

# What embench_isa_tests' writers emit into a branch's files dir, registered
# so the artifacts are reachable from the DB.
_MEASUREMENT_FILES = (
    ("embench_results", "perf.json"),
    ("riscv_tests_results", "riscv_tests.json"),
)

# write_isa_results only creates this when something failed, and it is a
# directory rather than a file, so it is registered separately.
_MEASUREMENT_DIRS = (("riscv_tests_failures", "riscv_tests_failures"),)


def _register_measurements(db, branch, out_dir) -> None:
    """Register the measurement artifacts that were actually produced."""
    for role, key in _MEASUREMENT_FILES:
        if (out_dir / key).is_file():
            db.register_file(branch, role, out_dir / key)
    for role, key in _MEASUREMENT_DIRS:
        if (out_dir / key).is_dir():
            db.register_dir(branch, role, out_dir / key)

# Inline debugger prompt: shipped in this package (no /debugging slash command
# installed in LLM_ENV required). The full markdown is read in Python and
# sent inline to debug_failure as prompt_text; the aux reference files it tells
# the LLM to read are shipped as {filename: content} and written onto the LLM
# machine per call (the {AUX_DIR} placeholder), then deleted after the call.
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DEBUG_AUX_FILE_NAMES = ("common_debugging.md", "chisel_debugging.md")


def _load_debug_prompt() -> tuple[str, dict[str, str]]:
    """Return (debug_prompt_text, debug_aux_files) for inline debug_failure calls."""
    text = load_prompt(PROMPTS_DIR / "debugging.md")
    aux = {name: (PROMPTS_DIR / name).read_text() for name in DEBUG_AUX_FILE_NAMES}
    return text, aux


# ---------------------------------------------------------------------------
# Remote helpers
# ---------------------------------------------------------------------------

@ChiaFunction(resources={"chipyard": 1.0})
def stage_preliminary_generated_src(
    generated_src: list[tuple[str, str]],
    dest_dir: str = PRELIMINARY_GENERATED_SRC_DIR,
) -> int:
    """Write each (filename, contents) from generated_src into dest_dir.

    Clears dest_dir first so the staging directory reflects exactly the
    input branch's generated Verilog with no leftover files.
    """
    shutil.rmtree(dest_dir, ignore_errors=True)
    os.makedirs(dest_dir, exist_ok=True)
    for fname, contents in generated_src:
        path = os.path.join(dest_dir, fname)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w") as f:
            f.write(contents)
    return len(generated_src)


@ChiaFunction(resources={"chipyard": 1.0})
def stage_reports_for_llm(reports: dict[str, str]) -> dict[str, int]:
    """Write ``{dest_path: text}`` onto the chipyard worker for the agent to grep.

    Must be scheduled on the same chipyard PG slot as chipyard_bash so the writes
    land on the host the agent's bash commands run on.

    All three of the objective's terms have to be visible to the agent: where
    the area is (Yosys' per-module roll-up), which paths are critical (OpenSTA),
    and which benchmarks are cycle-sensitive.
    """
    written: dict[str, int] = {}
    for dest_path, text in reports.items():
        if not text:
            continue
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w") as f:
            f.write(text)
        written[dest_path] = len(text)
    return written


def _short_branch(n: str) -> str:
    """`baseline_area_v7_1` -> `v7_1`, `baseline` -> `seed`.

    The tables, the diff headings and the staged history directories all name
    branches this way, so they have to agree: the agent greps a directory it
    read the name of in a table.
    """
    return n.replace("baseline_area_", "").replace("baseline", "seed")


def format_ipc_report(perf_rows: list[dict], mean_ipc: float | None,
                      area: float | None, sram_area: float | None,
                      fmax_mhz: float | None,
                      title: str = "Parent design") -> str:
    """Render a design's per-benchmark IPC + area/fmax headline as markdown.

    This is the third staged report and the one with no analogue in the timing
    flow. A single mean IPC tells the agent nothing about *which* structures to
    leave alone; the per-benchmark spread does. The baseline saw a 2.4x spread
    across embench on this config (nettle-aes and nettle-sha256 scale hardest
    with issue width, crc32 and nsichneu barely at all), so a change that only
    hurts the low-IPC tail costs far less mean than one that hurts the head.
    """
    # db.get_perf_results nests the measurements under "counters"; flatten so the
    # same formatter works on a freshly measured list and on a DB round-trip.
    perf_rows = [
        {"test_name": r["test_name"], **(r.get("counters") or {}), **{
            k: v for k, v in r.items() if k not in ("test_name", "counters")}}
        for r in perf_rows
    ]
    lines = [
        f"# {title}: measured performance, area and timing",
        "",
        "## Headline",
        "",
        f"- mean embench IPC : {'n/a' if mean_ipc is None else f'{mean_ipc:.6f}'}",
        f"- total cell area  : {'n/a' if area is None else f'{area:,.0f} um2'}"
        " (Yosys, includes the CACTI SRAM macros)",
        f"- SRAM macro area  : {'n/a' if sram_area is None else f'{sram_area:,.0f} um2'}",
        f"- standard cells   : "
        f"{'n/a' if (area is None or sram_area is None) else f'{area - sram_area:,.0f} um2'}",
        f"- fmax             : {'n/a' if fmax_mhz is None else f'{fmax_mhz} MHz'}"
        f" ({STA_CORNER}, OpenSTA)",
        f"- ipc_area_eff     : {format_eff(ipc_area_eff(mean_ipc, area), 'IPC/mm2')}",
        "",
        "## Per-benchmark IPC",
        "",
        "Sorted by IPC. The objective is built from the cycle counts, not this",
        "column, so every benchmark counts equally regardless of its length.",
        "",
        "| benchmark | IPC | ROI cycles | ROI instret |",
        "|---|---|---|---|",
    ]
    rows = [r for r in perf_rows if r.get("ipc") is not None]
    for r in sorted(rows, key=lambda r: r["ipc"], reverse=True):
        lines.append(
            f"| {r['test_name']} | {r['ipc']:.6f} | "
            f"{r.get('roi_cycles', 0):,} | {r.get('roi_instret', 0):,} |")
    missing = [r["test_name"] for r in perf_rows if r.get("ipc") is None]
    if missing:
        lines += ["", f"No IPC measured for: {', '.join(sorted(missing))}"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# The objective
# ---------------------------------------------------------------------------

def embench_speed_score(embench_speed_score_per_mhz: float | None,
                fmax_mhz: float | None) -> float | None:
    """The Embench speed score: its per-MHz figure times the clock rate.

    ``embench_speed_score_per_mhz`` comes from embench_isa_tests.embench_speed_score_per_mhz, which
    can compute it from cycle counts alone; the frequency it is missing arrives
    later, from synthesis. Multiplying here is exactly Embench's own formula
    rearranged -- see that function for the derivation.
    """
    if not embench_speed_score_per_mhz or not fmax_mhz:
        return None
    return embench_speed_score_per_mhz * fmax_mhz


def embench_speed_score_area_eff(embench_speed_score_per_mhz: float | None, area: float | None,
                   fmax_mhz: float | None) -> float | None:
    """**The objective**: Embench speed score per um2, or None if a term is missing.

    Area is total cell area INCLUDING the SRAM macros, which is what
    parse_area_from_reports returns for the Yosys flow.

    Frequency is inside the speed score by construction, so this one figure
    covers both halves of delivered performance. That is why there is no
    separate fmax floor: it would double-count what the objective already
    prices in.

    Against a mean-IPC objective this differs twice over. It weighs benchmarks
    geometrically, so a regression on one benchmark cannot be averaged away by
    a gain on another; and it is relative to a fixed reference platform, so the
    number means the same thing across configs.
    """
    score = embench_speed_score(embench_speed_score_per_mhz, fmax_mhz)
    if not score or not area:
        return None
    return score / area


def ipc_area_eff(mean_ipc: float | None, area: float | None) -> float | None:
    """``mean_ipc / area`` in IPC per um2 -- reported alongside, not optimized.

    Not to be confused with perf_area_eff, the objective: that is
    embench_speed_score / area. This one holds the IPC numerator fixed instead.

    Recorded on every run because it isolates the per-cycle half of a change
    from the frequency half, which the objective on its own cannot show.
    """
    if not mean_ipc or not area:
        return None
    return mean_ipc / area


def format_eff(eff: float | None, unit: str = "speed/mm2") -> str:
    """Per-um2 figures are unreadably small; humans get them per mm2."""
    if eff is None:
        return "n/a"
    return f"{eff * 1e6:.6f} {unit}"


def _changed_files(db, name: str, parent_name: str | None) -> list[str]:
    """Files this branch touched that its parent did not.

    diff.json holds the cumulative diff against the base commit, so the files a
    single iteration introduced are its set minus its parent's.
    """
    def files_of(b: str) -> set[str]:
        try:
            d = db.load_diff(b)
        except Exception:
            return set()
        out: set[str] = set()
        for body in (d or {}).values():
            if body:
                out |= set(re.findall(r"^diff --git a/(\S+)", body, re.M))
        return out
    mine = files_of(name)
    return sorted(mine - (files_of(parent_name) if parent_name else set()))


def _own_diff(db, name: str, parent_name: str | None) -> str:
    """The hunks this branch added on top of its parent.

    Same subtraction as :func:`_changed_files`, but keeping the bodies: a
    branch's own edit is its cumulative diff minus the lines its parent already
    had. The cumulative diff is the wrong thing to show -- everything but the
    last edit is already visible in the parent's checkout.
    """
    def lines_of(b: str | None) -> list[str]:
        if not b:
            return []
        try:
            d = db.load_diff(b)
        except Exception:
            return []
        return "".join(v for v in (d or {}).values() if v).splitlines()

    added = [l[2:] for l in difflib.ndiff(lines_of(parent_name), lines_of(name))
             if l.startswith("+ ")]
    return "\n".join(added).strip()


def _delta_summary(b: dict, parent: dict | None) -> str:
    """`area -5.5%  cycles -5.2%  fmax -1.6%` -- which factor an edit moved.

    The table's absolute columns do not say where a rejected edit lost: an area
    win cancelled by a cycle loss reads the same as a plain area regression.
    """
    if not parent:
        return ""
    def pct(key: str, invert: bool = False) -> str | None:
        a, c = parent.get(key), b.get(key)
        if not a or c is None:
            return None
        d = (c / a - 1.0) * 100.0
        return f"{-d if invert else d:+.1f}%"
    parts = []
    for label, key in (("area", "area"), ("cycles", "embench_speed_score_per_mhz"),
                       ("fmax", "fmax_mhz")):
        # cycles: speed/MHz rises when cycle counts fall, so report the speed
        # sense directly -- "cycles +2%" here means 2% more work per second.
        v = pct(key)
        if v:
            parts.append(f"{label} {v}")
    return "  ".join(parts)


def format_history_table(db, branch_name: str) -> str:
    """The lineage that produced *branch_name*, plus the attempts that failed.

    The agent only ever sees the parent's code and reports, so without this it
    cannot tell which structures earlier iterations already took apart, nor
    which directions were tried and rejected. Both are things it would
    otherwise rediscover by spending a whole iteration on them.
    """
    try:
        chain = db.ancestry(branch_name)
    except Exception:
        return "(history unavailable)"
    if not chain:
        return "(no history: this is the first iteration)"

    short = _short_branch

    def row(b: dict, parent_name: str | None, tag: str = "") -> str:
        area = b.get("area")
        ipc = b.get("mean_ipc")
        fmax = b.get("fmax_mhz")
        spm = b.get("embench_speed_score_per_mhz")
        eff = b.get("embench_speed_score_area_eff")
        touched = _changed_files(db, b["name"], parent_name)
        names = ", ".join(os.path.basename(f) for f in touched[:4]) or "--"
        if len(touched) > 4:
            names += f", +{len(touched) - 4} more"
        return (f"| {short(b['name'])}{tag} "
                f"| {short(parent_name) if parent_name else '--'} "
                f"| {'n/a' if area is None else f'{area / 1e6:.3f}'} "
                f"| {'n/a' if fmax is None else f'{fmax:.2f}'} "
                f"| {'n/a' if ipc is None else f'{ipc:.6f}'} "
                f"| {'n/a' if spm is None else f'{spm:.6f}'} "
                f"| {'n/a' if eff is None else f'{eff * 1e6:.6f}'} "
                f"| {b.get('status') or 'n/a'} | {names} |")

    # `built on` matters in the second table, where the rows do not share a
    # parent: a delta is against that row's own parent, not against this branch.
    header = ("| branch | built on | area mm2 | fmax MHz | IPC | speed/MHz "
              "| speed/mm2 | status | files this step touched |")
    divider = "|---|---|---|---|---|---|---|---|---|"
    lines = [header, divider]
    # (branch, parent) for every row printed, so the diff section below covers
    # exactly what the tables name and nothing else.
    shown: list[tuple[dict, dict | None]] = []
    for i, b in enumerate(chain):
        par = chain[i - 1] if i else None
        shown.append((b, par))
        lines.append(row(b, par["name"] if par else None))

    def section(title: str, branches: list[dict]) -> None:
        if not branches:
            return
        lines.extend(["", title, ""])
        lines.append(header)
        lines.append(divider)
        for b in branches:
            pid = b.get("parent_id")
            prow = None
            if pid is not None:
                prow = db.query_one(
                    "SELECT * FROM branches WHERE id = ?", (pid,))
            shown.append((b, dict(prow) if prow else None))
            lines.append(row(b, prow["name"] if prow else None))

    # A _synth_only branch is the SAME RTL re-synthesized, not another edit, so it
    # belongs in its own section: filed with the rejected attempts it reads as a
    # direction someone tried and abandoned, which is the opposite of what it is.
    off_lineage = list(db.siblings(branch_name)) + list(db.children(branch_name))
    # Substring, not endswith: `_synth_only_flatten` is a re-measurement too,
    # and filed as an attempt it reads as an edit that won on area and fmax.
    remeasures = [b for b in off_lineage if "_synth_only" in b["name"]]
    attempts = [b for b in off_lineage if "_synth_only" not in b["name"]]

    section("Edits off the lineage -- rejected attempts, and alternatives tried "
            "from a different starting point. Read `built on`: these do not all "
            "branch from the same place, so each row's deltas are against its own "
            "parent, not against yours.", attempts)
    section("Re-measurements: the same RTL synthesized again, no edit and no "
            "simulation, so they carry no cycle counts and no objective.",
            remeasures)
    if any(_own_diff(db, b["name"], p["name"] if p else None)
           for b, p in shown if "_synth_only" not in b["name"]):
        lines.append("")
        lines.append("The edit behind each row is at the end of this document.")
    return "\n".join(lines)


def format_history_diffs(db, branch_name: str) -> str:
    """Each branch's own hunk, for the end of the prompt.

    Kept out of the table so the reasoning up front stays readable; the diffs
    are reference material the agent comes back to once it has a candidate
    direction.
    """
    try:
        chain = db.ancestry(branch_name)
    except Exception:
        return ""
    if not chain:
        return ""

    short = _short_branch

    shown: list[tuple[dict, dict | None]] = [
        (b, chain[i - 1] if i else None) for i, b in enumerate(chain)]
    for b in list(db.siblings(branch_name)) + list(db.children(branch_name)):
        pid = b.get("parent_id")
        prow = db.query_one("SELECT * FROM branches WHERE id = ?",
                            (pid,)) if pid is not None else None
        shown.append((b, dict(prow) if prow else None))

    bodies = []
    for b, par in shown:
        if "_synth_only" in b["name"]:
            continue
        d = _own_diff(db, b["name"], par["name"] if par else None)
        if not d:
            continue
        verdict = b.get("status") or "n/a"
        delta = _delta_summary(b, par)
        on = f", on {short(par['name'])}" if par else ""
        head = f"### {short(b['name'])} ({verdict}{on})"
        if delta:
            head += f" -- {delta}"
        bodies.append(f"{head}\n\n```diff\n{d}\n```")
    if not bodies:
        return ""
    return "\n\n".join([
        "Each branch's own hunk, on top of its parent -- not the cumulative "
        "diff, which for the lineage is already in the checkout you are "
        "editing. `area`/`cycles`/`fmax` after the status say which factor the "
        "edit moved (`cycles` in the speed sense: + is faster).",
        "A rejected edit is not automatically a dead direction. Read its hunk "
        "and its three factors before avoiding it: an area win cancelled by a "
        "cycle loss is an implementation to fix, not a structure to leave "
        "alone, and it reads the same in the table as a plain regression.",
        *bodies,
    ])


def history_reports_for_llm(
    db, exclude: set[str], limit: int = HISTORY_REPORT_BRANCHES,
) -> tuple[dict[str, str], list[str]]:
    """``({dest_path: text}, [short names])`` for the last *limit* branches.

    A hunk says what an edit changed; these say what it did. v12 read v10's hunk,
    inferred it had lengthened the FP register-read cone, and designed around
    that -- v10's STA report contains no FP path at all.

    Branches with nothing measured are skipped and do not count against *limit*.
    """
    rows = db.query("SELECT * FROM branches ORDER BY id DESC")
    staged: dict[str, str] = {}
    names: list[str] = []
    for b in rows:
        if len(names) >= limit:
            break
        if b["name"] in exclude:
            continue

        def load(fn, *a):
            try:
                return fn(*a)
            except Exception:
                return ""

        area = load(db.load_area_report, b["name"])
        sta = load(db.load_timing_report, b["name"])
        if not (area or sta):
            continue
        short = _short_branch(b["name"])
        d = f"{HISTORY_REPORTS_LLM_DIR}/{short}"
        staged[f"{d}/area_report.txt"] = area
        staged[f"{d}/sta_report.rpt"] = sta
        staged[f"{d}/ipc_report.md"] = format_ipc_report(
            load(db.get_perf_results, b["name"]) or [],
            b.get("mean_ipc"), b.get("area"), b.get("sram_macro_area"),
            b.get("fmax_mhz"),
            title=f"Branch {short} ({b.get('status') or 'n/a'})",
        )
        names.append(short)
    return staged, names


def format_both_eff(mean_ipc: float | None, area: float | None,
                    embench_speed_score_per_mhz: float | None, fmax_mhz: float | None) -> str:
    """The objective and the IPC figure on one line, the objective marked."""
    return (f"{format_eff(embench_speed_score_area_eff(embench_speed_score_per_mhz, area, fmax_mhz))}"
            f" <- gates; {format_eff(ipc_area_eff(mean_ipc, area), 'IPC/mm2')}")


def evaluate_gates(
    parent: dict,
    child_fmax: float | None,
    child_isa: dict[str, dict],
    parent_isa: dict[str, dict] | None,
    seed_isa: dict[str, dict] | None = None,
    child_eff: float | None = None,
    best: dict | None = None,
) -> tuple[bool, list[str]]:
    """Check the child against the proposal's two hard gates.

    Returns ``(passed, reasons)``; ``reasons`` explains every gate, met or not, so
    the run log records why a result was accepted rather than only why it was
    rejected.

    The riscv-test gate is a per-test set comparison rather than a count
    comparison: an edit that fixes one test while breaking another keeps the
    count identical, and that is a regression this objective must not accept.

    The two gates use different references, because they are different kinds of
    thing.

    The objective gate is on the objective itself (*child_eff*, passed in because
    it needs the measured cycle counts) and measures against the BEST figure any
    branch has reached (*best*, from db.best_eff_branch), not the parent: the
    parent is only wherever this run was pointed, so starting from a rejected
    branch lowers the bar. v11 cleared v10 (1.5415e-5) by reverting to v9 and was
    recorded `ok` at v9's own 1.9333e-5, for a round that added nothing.

    Frequency needs no gate of its own -- it is already a factor of the speed
    score, so an fmax floor would price the same thing twice.

    The riscv-test gate measures against the SEED. Correctness is a constraint,
    not a term of the objective: an iteration that happened to fix a test the
    seed never passed should not hand every later iteration a higher bar than
    the design ever had to meet. It falls back to the parent when the seed has
    no per-test record.
    """
    reasons: list[str] = []
    passed = True

    floor_row, floor_label = parent, "parent"
    if best and best.get("embench_speed_score_area_eff") is not None:
        floor_row = best
        floor_label = f"best so far ({_short_branch(best['name'])})"
    floor_eff = floor_row.get("embench_speed_score_area_eff")
    if child_eff is None:
        passed = False
        reasons.append(
            "FAIL perf_area_eff: the child has no figure "
            "(missing embench speed, area or fmax)")
    elif floor_eff is None:
        reasons.append(
            f"SKIP perf_area_eff: {floor_label} has none recorded; child is "
            f"{format_eff(child_eff)}")
    elif child_eff > floor_eff:
        reasons.append(
            f"PASS perf_area_eff: {format_eff(child_eff)} > "
            f"{floor_label} {format_eff(floor_eff)} "
            f"(child fmax {child_fmax} MHz)")
    else:
        passed = False
        # Strictly greater: the flow is bit-deterministic, so an exact tie means
        # the RTL came back to a design the tree already has.
        reasons.append(
            f"FAIL perf_area_eff: {format_eff(child_eff)} "
            f"{'==' if child_eff == floor_eff else '<'} "
            f"{floor_label} {format_eff(floor_eff)} -- "
            f"{'no gain over a result the tree already has' if child_eff == floor_eff else 'Embench speed per area regressed'} "
            f"(child fmax {child_fmax} MHz)")

    isa_ref, isa_label = (seed_isa, "seed") if seed_isa else (parent_isa, "parent")
    if isa_ref is None:
        n_fail = sum(1 for e in child_isa.values() if e.get("outcome") != "pass")
        reasons.append(
            f"SKIP riscv-tests: no seed or parent per-test record to compare "
            f"against; child has {len(child_isa) - n_fail}/{len(child_isa)} passing")
    else:
        regressed = sorted(
            name for name, e in isa_ref.items()
            if e.get("outcome") == "pass"
            and child_isa.get(name, {}).get("outcome") != "pass"
        )
        fixed = sorted(
            name for name, e in child_isa.items()
            if e.get("outcome") == "pass"
            and isa_ref.get(name, {}).get("outcome") != "pass"
        )
        if regressed:
            passed = False
            reasons.append(
                f"FAIL riscv-tests: {len(regressed)} test(s) that passed on the "
                f"{isa_label} now fail: {', '.join(regressed[:12])}"
                f"{' ...' if len(regressed) > 12 else ''}")
        else:
            reasons.append(
                f"PASS riscv-tests: no regressions against the {isa_label}'s "
                f"{len(isa_ref)} tests")
        if fixed:
            reasons.append(f"NOTE riscv-tests: newly passing: {', '.join(fixed[:12])}")

    return passed, reasons


# ---------------------------------------------------------------------------
# Shared pipeline helpers (used by both run_perf_area_loop and seed_flow)
# ---------------------------------------------------------------------------


def _save_cacti_libs(db, branch, out_dir, cacti_libs) -> int:
    """Write the CACTI-generated LEF + Liberty files into out_dir/cacti_libs/ on
    the head, BEFORE synthesis runs.

    These are the exact macro views Yosys and OpenSTA consume: filenames mirror
    what the synth node writes on the worker (``cacti_<name>.lef`` and
    ``<name>_<corner>.lib``). They are worth keeping per branch because the SRAM
    macros are ~19% of this config's area, so an edit that changes a cache
    geometry shows up here before it shows up in the area total.
    Returns the number of files written; no-op on empty cacti_libs.
    """
    if not cacti_libs:
        print("  (no cacti_libs to save)")
        return 0
    lib_dir = out_dir / "cacti_libs"
    lib_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for lp in cacti_libs:
        name = lp.get("name")
        if not name:
            continue
        lef = lp.get("lef_content")
        if lef:
            (lib_dir / f"cacti_{name}.lef").write_text(lef)
            n += 1
        lib_contents = lp.get("lib_contents") or (
            {"tt_025C_1v80": lp["lib_content"]} if lp.get("lib_content") else {})
        for corner, content in lib_contents.items():
            (lib_dir / f"{name}_{corner}.lib").write_text(content)
            n += 1
    db.register_dir(branch, "cacti_libs", lib_dir)
    print(f"  saved {n} CACTI lib/lef files -> {lib_dir}")
    return n


def _save_synthesis_to_db(db, branch, out_dir, new_boom_tile, syn_result, area,
                          syn_elapsed):
    """Write synthesis artifacts into the branch's files dir and register them.

    ``_save_variant_results`` writes area_estimates.json, synthesis_log.md and
    the synthesis_reports/ tree into ``out_dir`` (head-node disk) from the
    in-memory ``syn_result.reports``.

    There is no syn_obj tarball to extract on this flow. The Genus path tarred
    its whole obj_dir on the worker and shipped the bytes back; synthesize_and_time
    returns its reports in memory instead, and those reports already carry
    everything the objective reads -- the Yosys area roll-up and the OpenSTA
    transcript -- so the obj_dir stays on the worker's /scratch.
    """
    _save_variant_results(out_dir, new_boom_tile, syn_result, area, syn_elapsed)
    db.register_dir(branch, "synthesis_reports", out_dir / "synthesis_reports")
    db.register_file(branch, "area_estimates", out_dir / "area_estimates.json")
    db.register_file(branch, "synthesis_log", out_dir / "synthesis_log.md")


def _split_results(verilator_outcome, embench_names: set[str]):
    """Split one dispatch's results into (embench, isa) by binary name."""
    emb, isa = [], []
    for r in verilator_outcome.results:
        (emb if r.test_binary_name in embench_names else isa).append(r)
    return emb, isa


def _collect_perf(verilator_outcome, embench_names: set[str]):
    """Build the per-test IPC rows for db.save_perf_results.

    Counts come from embench's own ROI counters (rdcycle/rdinstret around the
    benchmark kernel, see examples/benchmarks/embench/roi.h), not from the TMA
    performance counters: ``WithBoomTMACounters`` is applied only by
    MegaBoomChiaBigCacheConfig, so on this flow's target parse_tma_counters would
    return an empty dict for every test and the loop would run to completion
    having measured nothing. The ROI counters are config-independent and are what
    the baseline used.

    Only embench rows carry IPC; the ISA tests are the correctness gate and are
    recorded with their outcome alone.
    """
    perf = []
    for r in verilator_outcome.results:
        if r.test_binary_name not in embench_names:
            continue
        outcome, detail = classify_outcome(r)
        counters = {"outcome": outcome}
        if detail:
            counters["detail"] = detail
        roi = parse_roi(r)
        if roi:
            counters.update(roi)
        perf.append({
            "test_name": r.test_binary_name,
            "passed": outcome == "pass",
            "counters": counters,
        })
    return perf


def _measure(out_dir, config, verilator_outcome, embench_tests):
    """Write perf.json + riscv_tests.json and return the measured metrics.

    Reuses embench_isa_tests' writers verbatim, so every branch's files_dir
    comes out in the same shape and any two can be diffed straight against each
    other.

    Returns ``(metrics, isa_per_test, perf_rows, error)``. ``error`` is a string
    when the measurement is not trustworthy enough to persist as a comparable
    result -- specifically when any embench benchmark yielded no IPC, because a
    mean over a silently smaller set reads as a faster core.
    """
    embench_names = {tb.name for tb in embench_tests}
    emb_results, isa_results = _split_results(verilator_outcome, embench_names)

    emb_summary = write_embench_results(
        out_dir, config, emb_results, sorted(embench_names))
    isa_summary = write_isa_results(out_dir, config, isa_results)
    isa_json = out_dir / "riscv_tests.json"
    isa_per_test = (json.loads(isa_json.read_text()).get("per_test", {})
                    if isa_json.is_file() else {})
    perf_rows = _collect_perf(verilator_outcome, embench_names)

    metrics = {
        "mean_ipc": emb_summary["embench_mean_ipc"],
        "embench_speed_score_per_mhz": emb_summary["embench_speed_score_per_mhz"],
        "embench_tests": emb_summary["embench_tests"],
        "embench_expected": emb_summary["embench_expected"],
        "embench_missing_ipc": emb_summary["embench_missing_ipc"],
        "riscv_tests_passed": isa_summary["riscv_tests_passed"],
        "riscv_tests_total": isa_summary["riscv_tests_total"],
    }

    error = None
    measured = emb_summary["embench_tests"]
    if measured < emb_summary["embench_expected"]:
        error = (
            f"only {measured} of {emb_summary['embench_expected']} embench "
            f"benchmarks yielded an IPC (all are required); "
            f"missing: {', '.join(emb_summary['embench_missing_ipc']) or 'n/a'}. "
            f"The speed score is a geometric mean over a fixed benchmark set, "
            f"so a short set is not comparable and embench_speed_score_area_eff would be wrong.")
    return metrics, isa_per_test, perf_rows, error


# ---------------------------------------------------------------------------
# ExperimentLogger — head-node-pinned Ray actor for LLM-experiment DB writes
# ---------------------------------------------------------------------------

@ray.remote(num_cpus=0)
class ExperimentLogger:
    """The DB lives only on the head node (PERF_AREA_EFF_DB_DIR), but the LLM's
    experiment tool runs in a Ray actor on the chipyard worker. This actor sits
    on the head node and is the only thing that writes to the experiments
    tables — the tool calls into it via ``ray.get_actor(name)``.
    """

    def __init__(self, db_dir: str, parent_branch: str):
        self.db = PerfAreaEffDB(db_dir)
        self.parent_branch = parent_branch

    def record(self, vlsi_top, status, syn_result, timing_result,
               elapsed_seconds) -> dict:
        """Persist a single experiment (one sub-block A/B synth's outcome).

        ``syn_result`` and ``timing_result`` may be None (e.g. when the synth task
        raised) — we still record the row + status so the agent's attempt is
        traceable.

        Records area AND fmax, not slack alone: on this objective a sub-block
        result is only useful if it says both what the edit did to area and what
        it did to speed.
        """
        exp_id, files_dir = self.db.create_experiment(self.parent_branch, vlsi_top)
        area = sram_area = None
        if syn_result is not None:
            try:
                area = parse_area_from_reports(syn_result.reports)
                # No Liberty here: the A/B path caches its CACTI output inside
                # the experiment tool and does not hand it back. The wrapper
                # fallback covers the unflattened sub-block runs; under flatten
                # this reports None, which is a per-experiment figure the
                # objective does not read.
                sram_area = _sram_macro_area(syn_result.reports)
                _save_variant_results(
                    files_dir, vlsi_top, syn_result, area, elapsed_seconds)
            except Exception as e:
                print(f"  [logger] _save_variant_results failed: {e}")
        # Stash the OpenSTA transcript so the agent can grep the paths behind a
        # sub-block's fmax, not just read the headline number.
        rpt_text = resolve_report(
            syn_result.reports if syn_result is not None else {}, STA_REPORT_SUFFIXES)
        if rpt_text:
            try:
                self.db.save_experiment_timing_report(exp_id, rpt_text)
            except Exception as e:
                print(f"  [logger] save_experiment_timing_report failed: {e}")
        self.db.set_experiment_metrics(
            exp_id, status=status, area=area,
            sram_macro_area=sram_area,
            std_cell_area=(None if area is None or sram_area is None
                           else area - sram_area),
            fmax_mhz=None if timing_result is None else timing_result.fmax_mhz,
            elapsed_seconds=float(elapsed_seconds),
        )
        row = self.db.get_experiment(exp_id) or {}
        return {
            "exp_id": exp_id,
            "files_dir": str(files_dir),
            "area": area,
            "sram_macro_area": sram_area,
            "fmax_mhz": row.get("fmax_mhz"),
            "worst_slack_ns": row.get("worst_slack_ns"),
            "worst_slack_met": row.get("worst_slack_met"),
            "worst_slack_line": row.get("worst_slack_line"),
        }


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def _compute_out_branch(branch_name: str, output_suffix: str) -> str:
    """Return the output branch name with an auto-incremented version tag.

    If ``branch_name`` already ends with ``<output_suffix>_v<N>``, return the
    same prefix with ``N+1``. Otherwise append ``<output_suffix>_v1``.
    """
    m = re.match(rf'^(.*){re.escape(output_suffix)}_v(\d+)$', branch_name)
    if m:
        prefix, n = m.group(1), int(m.group(2))
        return f"{prefix}{output_suffix}_v{n + 1}"
    return f"{branch_name}{output_suffix}_v1"


def run_perf_area_loop(
    db: PerfAreaEffDB,
    branch_name: str,
    iteration: int = 1,
    max_debug_retries: int = 3,
    embench_tests: list | None = None,
    isa_tests: list | None = None,
    build_config: str = BUILD_CONFIG,
    output_suffix: str = "_area",
    skip_llm: bool = False,
    skip_verilator: bool = False,
    output_branch: str | None = None,
    prompt_path: str = IMPROVE_PERF_AREA_PROMPT_PATH,
    enable_experiment_tool: bool = True,
    llm: LLMSpec = LLMSpec(),
    diff_override: dict | None = None,
    known_failures: set[str] | None = None,
    synth_flatten: bool = False,
) -> dict:
    """Improve perf-area efficiency on an existing DB branch.

    Output branch name defaults to ``<branch_name><output_suffix>_v1``, or — if
    ``branch_name`` already ends with ``<output_suffix>_v<N>`` — the same
    prefix with ``N+1``. ``output_branch`` overrides the computed name (used
    for ablation re-synth runs that don't follow the auto-increment scheme).

    When ``skip_llm`` is set, Step 4 (the LLM edit) is bypassed; the parent
    branch's diff is applied and the rest of the pipeline (build → verilator →
    synth) runs against that RTL unchanged. Useful for ablation re-synthesis
    where the diff itself is the experiment.

    When ``skip_verilator`` is set, the design is built once (only to elaborate
    the RTL + collect generated Verilog) and verilator is never dispatched —
    just CACTI + synth. That yields area and fmax but NO IPC, so
    ``perf_area_eff`` is left null and the correctness gate cannot be evaluated;
    it is an area-only probe, not a comparable result. The chipyard placement
    group is released right after the synthesis dispatch so the build node is
    free during the synth.

    ``diff_override`` (a ``collect_diff``-format dict) is applied INSTEAD of the
    parent branch's diff; the parent then only supplies the staging
    generated_src and reports.

    ``known_failures`` are test names excused from the debug-retry loop; it
    defaults to whatever the parent branch already failed.

    ``llm`` is the agent for both the edit step and the build/test debugger.
    """
    out_branch = output_branch or _compute_out_branch(branch_name, output_suffix)
    db.create_branch(out_branch, parent=branch_name, iteration=iteration,
                     build_config=build_config)
    out_dir = db.branch_files_dir(out_branch)
    instance_log_dir = os.path.join(str(out_dir), "logs")
    os.makedirs(instance_log_dir, exist_ok=True)
    timing_path = os.path.join(instance_log_dir, "timing.csv")
    if not os.path.isfile(timing_path):
        with open(timing_path, "w") as f:
            f.write("iteration,step,duration_s\n")

    def _write_log(text: str) -> None:
        p = out_dir / "improve_perf_area_log.md"
        p.write_text(text)
        db.register_file(out_branch, "improve_perf_area_log", p)

    # Inline debugger prompt: threaded into every debugger call (build +
    # verilator failures) so the example needs no slash command installed in
    # LLM_ENV.
    debug_prompt_text, debug_aux_files = _load_debug_prompt()
    debugger = LLMDebugger(llm)

    pg = None
    pg_opts: dict | None = None
    chipyard_bash = None
    experiment_tool = None
    experiment_logger = None
    inputs: dict | None = None
    diff_applied = False
    final_result: dict | None = None
    try:
        # ---- Step 1: load inputs from the DB ----
        print(f"\n{'='*60}\nStep 1: loading inputs for '{branch_name}'\n{'='*60}")
        inputs = db.load_inputs(branch_name)
        parent_row = db.get_branch(branch_name) or {}
        parent_isa = db.load_isa_per_test(branch_name)
        parent_area_report = db.load_area_report(branch_name)
        parent_perf_rows = db.get_perf_results(branch_name)
        print(
            f"  BoomTile module: {inputs['boom_tile']}\n"
            f"  generated_src files: {len(inputs['generated_src'])}\n"
            f"  timing report: {inputs['timing_report_path']} "
            f"({len(inputs['timing_report'])} chars)\n"
            f"  area report: {len(parent_area_report)} chars\n"
            f"  parent: area={parent_row.get('area')}, "
            f"mean_ipc={parent_row.get('mean_ipc')}, "
            f"fmax={parent_row.get('fmax_mhz')} MHz, "
            f"perf_area_eff={format_eff(parent_row.get('embench_speed_score_area_eff'))}, "
            f"riscv-tests={parent_row.get('riscv_tests_passed')}/"
            f"{parent_row.get('riscv_tests_total')}"
        )
        if known_failures is None:
            known_failures = {
                name for name, e in parent_isa.items() if e.get("outcome") != "pass"
            }
        print(f"  known-failing on the parent (excused from the debug loop): "
              f"{', '.join(sorted(known_failures)) or 'none'}")
        # diff_override: synthesize an *externally supplied* diff
        # instead of the parent branch's diff.
        # The parent only provides the vestigial generated_src/reports/
        # boom_tile (Step 3b staging + the old-vs-new comparison); Step 3a
        # applies this diff and Step 5 rebuilds Chisel from it. Pair with
        # skip_llm=True to get apply-diff -> build -> verilator -> synth, no LLM.
        if diff_override is not None:
            nonempty = [k for k, v in diff_override.items() if v]
            total = sum(len(v or "") for v in diff_override.values())
            print(f"  diff override: using supplied diff "
                  f"({len(nonempty)} non-empty part(s): {nonempty}, {total} chars) "
                  f"instead of parent '{branch_name}' diff")
            inputs["diff_dict"] = diff_override

        # ---- Step 2: acquire chipyard placement group + bash tool ----
        print(f"\n{'='*60}\nStep 2: acquire chipyard placement group + bash tool\n{'='*60}")
        pg = placement_group([{"CPU": 1, "chipyard": 1}], strategy="STRICT_PACK")
        ray.get(pg.ready())
        pg_opts = {
            "scheduling_strategy": PlacementGroupSchedulingStrategy(
                placement_group=pg, placement_group_bundle_index=0,
            )
        }
        bash_name = f"chipyard_bash_perf_area_{uuid4().hex[:8]}"
        chipyard_bash = ChipyardBashTool(
            name=bash_name, work_dir=CHIPYARD_PATH, task_options=pg_opts,
            timeout_seconds=600,
        )

        # ---- Step 2b: spawn ExperimentLogger and the LLM's experiment tool,
        # both pinned to the head node (the tool takes pg_opts so the work
        # it dispatches still lands on the chipyard PG). The tool lets the
        # agent run cheap sub-block syntheses during Step 4; the logger stays
        # the only DB writer for experiments, so rows have a single author.
        if not skip_llm and enable_experiment_tool:
            head_node_id = ray.get_runtime_context().get_node_id()
            logger_name = f"experiment_logger_{uuid4().hex[:8]}"
            experiment_logger = ExperimentLogger.options(
                name=logger_name,
                scheduling_strategy=NodeAffinitySchedulingStrategy(
                    node_id=head_node_id, soft=False,
                ),
            ).remote(DB_DIR, out_branch)

            # Pin the experiment-tool actor to the head node.
            tool_head_pin_opts = {
                "scheduling_strategy": NodeAffinitySchedulingStrategy(
                    node_id=head_node_id, soft=False,
                )
            }
            experiment_tool = PerfAreaExperimentTool(
                name=f"perf_area_experiment_{uuid4().hex[:8]}",
                chipyard_path=CHIPYARD_PATH,
                build_config=build_config,
                parent_branch=out_branch,
                logger_actor_name=logger_name,
                pg_opts=pg_opts,
                head_node_id=head_node_id,
                task_options=tool_head_pin_opts,
                # Parent's unmodified RTL — already loaded by load_inputs above.
                # The actor lists its modules from this copy; the A/B
                # synthesizes the parent from Step 3b's staging of the same
                # source on the chipyard node, so no RTL crosses the head link.
                parent_generated_src=inputs["generated_src"],
                parent_src_dir=PRELIMINARY_GENERATED_SRC_DIR,
            )

        # ---- Step 3a: reset chipyard + apply diff ----
        # Reset BEFORE staging: reset_and_apply_diff runs `git clean -fd` in the
        # chipyard root, which deletes the untracked staging directory. With the
        # old stage-then-reset order the agent was pointed at an empty
        # preliminary-generated-src/ (confirmed from a trial-run transcript).
        # The staging never enters the child diff: collect_diff takes only
        # tracked changes in the chipyard root.
        print(f"\n{'='*60}\nStep 3a: reset chipyard and apply diff\n{'='*60}")
        err, msg = get(
            reset_and_apply_diff.options(**pg_opts).chia_remote(inputs["diff_dict"])
        )
        print(f"  reset_and_apply_diff: {msg}")
        if err:
            return (final_result := {"status": "diff_apply_failed", "message": msg, "out_branch": out_branch})
        diff_applied = True

        # ---- Step 3b: stage generated_src onto the chipyard node ----
        print(f"\n{'='*60}\nStep 3b: stage generated_src into {PRELIMINARY_GENERATED_SRC_DIR}\n{'='*60}")
        n_staged = get(
            stage_preliminary_generated_src.options(**pg_opts).chia_remote(
                inputs["generated_src"], PRELIMINARY_GENERATED_SRC_DIR,
            )
        )
        print(f"  Staged {n_staged} files")

        # ---- Step 4: LLM — propose a perf-area efficiency edit ----
        if skip_llm:
            print(f"\n{'='*60}\nStep 4: SKIPPED (--skip-llm) — running build+verilator+synth on parent diff unchanged\n{'='*60}")
        else:
            print(f"\n{'='*60}\nStep 4: LLM perf-area efficiency edit on {build_config}\n{'='*60}")
            # Stage the parent's three measurement reports on the chipyard node
            # so the agent can grep them via chipyard_bash -- one per term of the
            # objective.
            ipc_report = format_ipc_report(
                parent_perf_rows, parent_row.get("mean_ipc"), parent_row.get("area"),
                parent_row.get("sram_macro_area"), parent_row.get("fmax_mhz"),
            )
            # The same three reports for the last few branches, so an earlier
            # round's result can be checked instead of inferred from its hunk.
            history_reports, history_branches = history_reports_for_llm(
                db, exclude={branch_name, out_branch})
            # The bar the gate will actually apply -- not always the parent.
            best_row = db.best_eff_branch()
            staged = get(
                stage_reports_for_llm.options(**pg_opts).chia_remote({
                    AREA_REPORT_LLM_PATH: parent_area_report,
                    STA_REPORT_LLM_PATH: inputs["timing_report"],
                    IPC_REPORT_LLM_PATH: ipc_report,
                    **history_reports,
                })
            )
            for path in (AREA_REPORT_LLM_PATH, STA_REPORT_LLM_PATH,
                         IPC_REPORT_LLM_PATH):
                if path in staged:
                    print(f"  staged {path} ({staged[path]:,} chars on the chipyard node)")
            if history_branches:
                n = sum(v for k, v in staged.items()
                        if k.startswith(HISTORY_REPORTS_LLM_DIR))
                print(f"  staged {HISTORY_REPORTS_LLM_DIR}/ for "
                      f"{', '.join(history_branches)} ({n:,} chars)")
            (out_dir / "ipc_report.md").write_text(ipc_report)
            db.register_file(out_branch, "parent_ipc_report", out_dir / "ipc_report.md")
            if not parent_area_report:
                print("  WARNING: the parent has no area report — the agent will be "
                      "optimizing area with no per-module area breakdown to read")

            # Pre-expand the prompt's placeholders on the head node: the CLIs run
            # in --print mode from piped stdin, which does not expand project
            # slash commands, so an unexpanded prompt reaches the model as a
            # literal "/improve_perf_area ..." string.
            with open(prompt_path) as f:
                cmd_template = f.read()
            prompt_text = (
                cmd_template
                .replace("$ARGUMENTS", build_config)
                .replace("$AREA_REPORT_PATH", AREA_REPORT_LLM_PATH)
                .replace("$STA_REPORT_PATH", STA_REPORT_LLM_PATH)
                .replace("$IPC_REPORT_PATH", IPC_REPORT_LLM_PATH)
                .replace("$BUILD_CONFIG_PACKAGE", BUILD_CONFIG_PACKAGE)
                .replace("$PARENT_BRANCH", branch_name)
                .replace("$PARENT_AREA", f"{parent_row.get('area') or 0:,.0f}")
                .replace("$PARENT_MEAN_IPC", f"{parent_row.get('mean_ipc') or 0:.6f}")
                .replace("$PARENT_FMAX", f"{parent_row.get('fmax_mhz') or 0}")
                # The longer name first: $PARENT_SPEED is a prefix of it, so
                # replacing that one first would leave a bare "_PER_MHZ" behind.
                .replace("$PARENT_SPEED_PER_MHZ",
                         f"{parent_row.get('embench_speed_score_per_mhz') or 0:.6f}")
                .replace("$PARENT_SPEED", f"{parent_row.get('embench_speed_score') or 0:.3f}")
                .replace("$PARENT_EFF", format_eff(parent_row.get("embench_speed_score_area_eff")))
                .replace("$CLOCK_PERIOD_NS", str(CLOCK_PERIOD_NS))
                .replace("$STA_CORNER", STA_CORNER)
                .replace("$BEST_BRANCH", _short_branch(
                    (best_row or parent_row).get("name", "?")))
                .replace("$BEST_EFF", format_eff(
                    (best_row or parent_row).get("embench_speed_score_area_eff")))
                .replace("$HISTORY_REPORT_DIR", HISTORY_REPORTS_LLM_DIR)
                .replace("$HISTORY_REPORT_BRANCHES",
                         ", ".join(history_branches) or "(none)")
                .replace("$HISTORY_TABLE",
                         format_history_table(db, branch_name))
                .replace("$HISTORY_DIFFS",
                         format_history_diffs(db, branch_name))
            )
            prompt_log_path = os.path.join(instance_log_dir, "improve_perf_area_prompt.md")
            with open(prompt_log_path, "w") as f:
                f.write(prompt_text)
            print(f"  Prompt saved to {prompt_log_path} ({len(prompt_text)} chars)")

            t0 = time.time()
            llm_tools = [chipyard_bash]
            if experiment_tool is not None:
                llm_tools.append(experiment_tool)
            # Built and run on the LLM worker, not here: the claude CLI runs in
            # its process CWD, and a log_dir made on the driver does not exist in
            # the container.
            cli = prompt_llm(llm, prompt_text, llm_tools,
                             logging_name="improve_perf_area", timeout_seconds=7200)
            print(f"  LLM finished in {time.time()-t0:.1f}s (success={cli.success})")
            llm_log_path = os.path.join(instance_log_dir, "improve_perf_area_llm.md")
            with open(llm_log_path, "w") as f:
                f.write(f"# perf-area efficiency edit response\n"
                        f"LLM: {llm}\n"
                        f"Success: {cli.success}\n\n")
                f.write(cli.result or "")
                if cli.stream_result:
                    f.write("\n\n## Stream log (tool calls, file reads, bash)\n\n")
                    f.write(cli.stream_result)
                else:
                    f.write("\n\n## Stream log\n\n(cli.stream_result was empty)\n")
            db.register_file(out_branch, "llm_log", Path(llm_log_path))
            if not cli.success:
                print(f"  LLM failed — exiting (diff revert handled in finally)")
                return (final_result := {"status": "llm_failed", "out_branch": out_branch})

        # ---- Step 5: build the design with debug retry ----
        # ENABLE_YOSYS_FLOW=1 is mandatory, not an optimization: without it
        # firtool emits packed multi-dimensional arrays that Yosys' Verilog
        # front end cannot read (50 of MediumBoomV3Config's 610 sources when
        # last measured), and synthesis fails on the *generated* RTL no matter
        # what the agent's Chisel edit was. It reaches ChiselBuildNode through
        # the extra_make_args hook added to common/build.py.
        # `config` has to be passed explicitly: common/build.py defaults it to
        # MegaBoomChiaBigCacheConfig, and omitting it is invisible until that
        # default stops matching, at which point the build silently elaborates
        # the wrong core and every metric belongs to another design.
        build_kwargs = dict(
            config=build_config,
            config_package=BUILD_CONFIG_PACKAGE,
            make_jobs=MAKE_JOBS,
            extra_make_args={"ENABLE_YOSYS_FLOW": "1"},
            debug_fn=debugger,
        )
        if skip_verilator:
            # Skipping verilator: a single Chisel build is enough to elaborate
            # the RTL and collect the generated Verilog for synthesis — the
            # multiple thread variants only exist to run verilator at different
            # thread counts, which we won't do.
            print(f"\n{'='*60}\nStep 5: build {build_config} (single variant — verilator skipped)\n{'='*60}")
            artifact = build_with_debug_retry(
                chipyard_bash, iteration=iteration, log_dir=instance_log_dir,
                timing_path=timing_path, max_retries=max_debug_retries,
                label="improve_perf_area", chipyard_task_options=pg_opts,
                verilator_threads=1,
                collect_generated_src=True, debug_log_base_dir=instance_log_dir,
                branch_name=out_branch,
                debug_prompt_text=debug_prompt_text,
                debug_aux_files=debug_aux_files,
                **build_kwargs,
            )
            artifacts_by_threads = {1: artifact} if artifact is not None else None
            test_binaries = []
        else:
            print(f"\n{'='*60}\nStep 5: build {build_config} (all thread variants)\n{'='*60}")
            if embench_tests is None or isa_tests is None:
                embench_tests, isa_tests = load_and_configure_test_binaries()
            test_binaries = list(embench_tests) + list(isa_tests)
            print(f"  Loaded {len(embench_tests)} embench + {len(isa_tests)} "
                  f"riscv-tests = {len(test_binaries)} binaries")
            artifacts_by_threads = build_all_thread_variants(
                test_binaries=test_binaries,
                chipyard_bash=chipyard_bash,
                iteration=iteration,
                log_dir=instance_log_dir,
                timing_path=timing_path,
                max_debug_retries=max_debug_retries,
                label="improve_perf_area",
                chipyard_task_options=pg_opts,
                collect_generated_src_for_first=True,
                debug_log_base_dir=instance_log_dir,
                branch_name=out_branch,
                debug_prompt_text=debug_prompt_text,
                debug_aux_files=debug_aux_files,
                **build_kwargs,
            )
        if artifacts_by_threads is None:
            print(f"  Build failed after {max_debug_retries} retries")
            _write_log(
                f"# improve_perf_area\n\nBuild failed after {max_debug_retries} debug retries.\n"
                f"Parent branch: {branch_name}\n"
            )
            return (final_result := {"status": "build_failed", "out_branch": out_branch})

        first_artifact = next(iter(artifacts_by_threads.values()))
        print(f"  Built {len(artifacts_by_threads)} thread variant(s)")

        # Persist the post-LLM diff + generated_src immediately so they survive
        # any downstream failure.
        _err, fresh_diff = get(
            collect_diff.options(**pg_opts).chia_remote()
        )
        if not _err:
            db.save_diff(out_branch, fresh_diff)
        db.save_generated_src(out_branch, first_artifact.generated_src_files)

        # ---- Step 6 loop: prep → dispatch synthesis → run verilator, with
        #      verilator-failure recovery (cancel syn, debug, rebuild, retry). ----
        # Each iteration redoes CACTI + MacroCompiler because the debugger may
        # have changed RTL-generator code → different generated Verilog.
        debug_session_id = str(uuid4())
        syn_ref = None
        syn_result = None
        timing_result = None
        verilator_outcome = None
        gen_src = None
        new_boom_tile = None
        cacti_libs = None
        # obj_dir is a path on the synth worker's local /scratch (the cluster has
        # no shared filesystem). Unlike the Genus flow the tree is not tarred back
        # to the head — synthesize_and_time returns its reports in memory.
        obj_dir = os.path.join(SYN_OBJ_SCRATCH_DIR, out_branch, "syn_obj")
        t_syn = 0.0

        for retry_attempt in range(max_debug_retries + 1):
            # ---- Step 6 prep: CACTI + MacroCompiler remap ----
            print(f"\n{'='*60}\nStep 6 prep: CACTI + MacroCompiler remap (attempt {retry_attempt+1})\n{'='*60}")
            # CACTI_PATH must be passed explicitly: run_cacti_macrocompiler_prep
            # defaults it to the redacted "/path/to/cacti/cacti" placeholder.
            gen_src, cacti_libs, new_boom_tile = run_cacti_macrocompiler_prep(
                first_artifact.generated_src_files, pg_opts, CACTI_PATH,
            )
            if new_boom_tile is None:
                print(f"  ERROR: could not resolve BoomTile in new generated_src")
                return (final_result := {"status": "boom_tile_resolve_failed", "out_branch": out_branch})

            # Save the post-MacroCompiler LEF/Liberty (what Yosys and OpenSTA will
            # consume) to the head before synthesis kicks off.
            _save_cacti_libs(db, out_branch, out_dir, cacti_libs)

            # ---- Step 6a: dispatch synthesis + STA (async) ----
            # Yosys reports area but no timing, OpenSTA the reverse, so
            # synthesize_and_time runs both back to back on one vlsi worker and
            # returns (SynthesisResult, TimingResult) — this objective's
            # numerator-denominator pair, in one dispatch.
            # _drop_behavioral_sources strips the simulation-only sources (plusarg
            # readers, EICG wrappers) that have no cell mapping.
            t_syn = time.time()
            print(f"\n{'='*60}\nStep 6a: dispatching Yosys synthesis + OpenSTA (vlsi_top={new_boom_tile})\n{'='*60}")
            syn_ref = synthesize_and_time.chia_remote(
                _drop_behavioral_sources(gen_src), new_boom_tile,
                obj_dir=obj_dir,
                cacti_sram_libs=cacti_libs,
                clock_period_ns=CLOCK_PERIOD_NS,
                timeout_seconds=SYNTHESIS_TIMEOUT_SECONDS,
                flatten=synth_flatten,
            )

            # ---- Step 6b: run verilator in parallel (skipped if --skip-verilator) ----
            if skip_verilator:
                # Synthesis is already dispatched to a VLSI node (it never used
                # the chipyard PG), and with verilator skipped there is no retry
                # loop that would need the chipyard node again. So free the
                # chipyard build node NOW instead of holding it idle through
                # the (potentially many-hour) synthesis — this decouples
                # chipyard-slot count from synth time. Nulling pg /
                # chipyard_bash / pg_opts stops the finally block from
                # double-freeing; it also disables the finally diff-revert,
                # which is fine because the next run's reset_and_apply_diff
                # restores a clean tree regardless.
                print(f"\n{'='*60}\nStep 6b: SKIPPED verilator (--skip-verilator); releasing chipyard PG, then awaiting synthesis\n{'='*60}")
                verilator_outcome = None
                try:
                    if chipyard_bash is not None:
                        chipyard_bash.stop()
                except Exception as e:
                    print(f"  early-release: chipyard_bash.stop() failed: {e}")
                try:
                    if pg is not None:
                        remove_placement_group(pg)
                        print(f"  early-release: freed chipyard placement group "
                              f"(build node available for other jobs during synth)")
                except Exception as e:
                    print(f"  early-release: remove_placement_group failed: {e}")
                pg = None
                chipyard_bash = None
                pg_opts = None
                break
            print(f"\n{'='*60}\nStep 6b: dispatch verilator tests (synthesis runs in parallel)\n{'='*60}")
            t_ver = time.time()
            verilator_outcome = dispatch_verilator_tests(
                artifacts_by_threads=_artifact_refs(artifacts_by_threads),
                test_binaries=test_binaries,
                **_DISPATCH_LIMITS,
            )
            ver_elapsed = time.time() - t_ver
            print(
                f"  Verilator returned in {ver_elapsed:.1f}s: "
                f"{len(verilator_outcome.results)} total, "
                f"{len(verilator_outcome.failed)} failed, "
                f"cancelled={verilator_outcome.cancelled}"
            )

            # Only failures the PARENT did not already have are worth debugging.
            # Two riscv-tests (rv64ui-p-ma_data, rv64ui-v-ma_data) fail on this
            # config's unmodified RTL -- BOOM does not implement misaligned data
            # accesses -- so a raw "any failure" check would spend every debug
            # retry, plus a full rebuild and re-simulation each time, trying to
            # fix RTL the agent never touched, and then return verilator_failed
            # having measured nothing. Regressions relative to the parent are
            # still caught, both here and by the riscv-test gate in Step 8.
            new_failures = [
                r for r in verilator_outcome.failed
                if known_failures is None or r.test_binary_name not in known_failures
            ]
            preexisting = len(verilator_outcome.failed) - len(new_failures)
            if preexisting:
                print(f"  {preexisting} of those failure(s) are known-failing on the "
                      f"parent and are not treated as regressions")

            if len(new_failures) == 0:
                break

            # ---- Verilator regressed: cancel syn_ref, wait for it to stop, debug, rebuild, loop ----
            print(
                f"\n[improve_perf_area] Verilator has {len(new_failures)} NEW "
                f"failure(s) (attempt {retry_attempt+1}/{max_debug_retries+1}): "
                f"{', '.join(r.test_binary_name for r in new_failures[:8])}"
            )
            try:
                print(f"  Cancelling in-flight synthesis (force=False) and waiting for it to stop")
                chia_cancel(syn_ref, force=False)
                # Block until the cancelled task actually stops, so its final
                # writes don't race the next iteration's obj_dir rmtree +
                # re-dispatch.
                ray.wait([syn_ref])
            except Exception as e:
                print(f"  chia_cancel/wait failed: {e}")
            syn_ref = None

            if retry_attempt >= max_debug_retries:
                print(f"  Max debug retries exhausted — giving up on verilator")
                failed_summary = "\n".join(
                    f"- {r.test_binary_name} (rc={r.returncode})"
                    for r in new_failures
                ) or "(none listed)"
                retry_artifacts = []
                for i in range(1, max_debug_retries + 1):
                    ec = os.path.join(instance_log_dir, f"error_context_retry{i}.txt")
                    dl = os.path.join(instance_log_dir, f"debug_failure_retry{i}.md")
                    if os.path.isfile(ec) or os.path.isfile(dl):
                        retry_artifacts.append(
                            f"- retry {i}: "
                            f"{ec if os.path.isfile(ec) else '(no error_context)'}, "
                            f"{dl if os.path.isfile(dl) else '(no debug_log)'}"
                        )
                retry_artifacts_text = "\n".join(retry_artifacts) or "(none)"
                _write_log(
                    f"# improve_perf_area: {out_branch}\n"
                    f"Status: verilator_failed after {max_debug_retries} debug retries\n"
                    f"Parent branch: {branch_name}\n"
                    f"Build config: {build_config}\n"
                    f"Log dir: {instance_log_dir}\n\n"
                    f"## Final NEW verilator failures "
                    f"({len(new_failures)} new, {preexisting} pre-existing, "
                    f"of {len(verilator_outcome.results)} run)\n"
                    f"{failed_summary}\n\n"
                    f"## Debug retry artifacts\n"
                    f"{retry_artifacts_text}\n\n"
                    f"## LLM response\n"
                    f"- {os.path.join(instance_log_dir, 'improve_perf_area_llm.md')}\n"
                )
                return (final_result := {
                    "status": "verilator_failed",
                    "out_branch": out_branch,
                    "verilator_failed": len(new_failures),
                    "failed_tests": [r.test_binary_name for r in new_failures],
                    "log_dir": instance_log_dir,
                })

            # Run the debugger with a persistent session so the LLM remembers
            # prior fix attempts across retries. Only the NEW failures are shown:
            # including the known-failing pair would send the debugger after RTL
            # the agent never touched.
            error_ctx = format_test_error(
                new_failures, iteration, retry_attempt + 1, BOOM_REPO_PATH,
            )
            err_ctx_path = os.path.join(
                instance_log_dir, f"error_context_retry{retry_attempt+1}.txt"
            )
            with open(err_ctx_path, "w") as f:
                f.write(error_ctx)
            t_dbg = time.time()
            dbg_cli = get(debugger.chia_remote(
                error_ctx, chipyard_bash, retry_attempt + 1,
                session_id=debug_session_id,
                llm_env=LLM_ENV,
                prompt_text=debug_prompt_text,
                aux_files=debug_aux_files,
            ))
            dbg_log_path = os.path.join(
                instance_log_dir, f"debug_failure_retry{retry_attempt+1}.md"
            )
            with open(dbg_log_path, "w") as f:
                f.write(
                    f"# debug_failure (retry={retry_attempt+1})\n"
                    f"Success: {dbg_cli.success}\n\n"
                )
                f.write(dbg_cli.result or "")
                if dbg_cli.stream_result:
                    f.write("\n\n## Stream log\n\n")
                    f.write(dbg_cli.stream_result)
            print(f"  debug_failure finished in {time.time()-t_dbg:.1f}s "
                  f"(success={dbg_cli.success})")
            if not dbg_cli.success:
                print(f"  Debugger failed — giving up")
                return (final_result := {"status": "debug_failed", "out_branch": out_branch})

            # Rebuild after debugger edits
            print(f"\n{'='*60}\nStep 6c: rebuild after debug (retry {retry_attempt+1})\n{'='*60}")
            artifacts_by_threads = build_all_thread_variants(
                test_binaries=test_binaries,
                chipyard_bash=chipyard_bash,
                iteration=iteration,
                log_dir=instance_log_dir,
                timing_path=timing_path,
                max_debug_retries=max_debug_retries,
                label=f"improve_perf_area_retry{retry_attempt+1}",
                chipyard_task_options=pg_opts,
                collect_generated_src_for_first=True,
                debug_log_base_dir=instance_log_dir,
                branch_name=out_branch,
                debug_prompt_text=debug_prompt_text,
                debug_aux_files=debug_aux_files,
                **build_kwargs,
            )
            if artifacts_by_threads is None:
                print(f"  Rebuild failed after debug — giving up")
                return (final_result := {"status": "rebuild_failed", "out_branch": out_branch})
            first_artifact = next(iter(artifacts_by_threads.values()))

            # Refresh persisted diff + generated_src so they reflect the debugger's fix.
            _err, fresh_diff = get(collect_diff.options(**pg_opts).chia_remote())
            if not _err:
                db.save_diff(out_branch, fresh_diff)
            db.save_generated_src(out_branch, first_artifact.generated_src_files)

        # ---- Step 7: collect synthesis result (may have already finished) ----
        print(f"\n{'='*60}\nStep 7: awaiting synthesis result\n{'='*60}")
        ready, _ = ray.wait([syn_ref], timeout=0.0)
        if ready:
            print(f"  Synthesis finished before verilator")
        else:
            print(f"  Synthesis still running — waiting")
        try:
            syn_result, timing_result = get(syn_ref)
        except Exception as e:
            print(f"  Synthesis task raised: {e}")
            _write_log(
                f"# improve_perf_area\n\nSynthesis task raised: {e}\n"
                f"Parent branch: {branch_name}\n"
            )
            return (final_result := {
                "status": "synthesis_failed",
                "out_branch": out_branch,
                "error": str(e),
            })
        syn_elapsed = time.time() - t_syn
        area = parse_area_from_reports(syn_result.reports)
        sram_area = _sram_macro_area(syn_result.reports, cacti_sram_libs=cacti_libs)
        fmax_mhz = timing_result.fmax_mhz if timing_result is not None else None
        print(
            f"  Synthesis+STA done in {syn_elapsed:.1f}s: "
            f"syn_success={syn_result.success}, sta_success="
            f"{None if timing_result is None else timing_result.success}, "
            f"area={area}, sram={sram_area}, fmax={fmax_mhz} MHz, "
            f"reports={len(syn_result.reports)}"
        )

        # ---- Step 8: measure, gate and persist ----
        print(f"\n{'='*60}\nStep 8: measure, gate and persist to {out_dir}\n{'='*60}")
        _save_synthesis_to_db(db, out_branch, out_dir, new_boom_tile, syn_result,
                              area, syn_elapsed)

        # IPC + correctness. None when verilator was skipped (--skip-verilator),
        # in which case there is no speed score and no gate to evaluate.
        mean_ipc = None
        metrics = {}
        child_isa: dict[str, dict] = {}
        perf_rows: list[dict] = []
        measure_error = None
        if verilator_outcome is not None:
            metrics, child_isa, perf_rows, measure_error = _measure(
                out_dir, build_config, verilator_outcome, embench_tests,
            )
            db.save_perf_results(out_branch, perf_rows)
            _register_measurements(db, out_branch, out_dir)
            mean_ipc = metrics.get("mean_ipc")
            ver_passed = len(verilator_outcome.results) - len(verilator_outcome.failed)
            ver_failed = len(verilator_outcome.failed)
            ver_summary = (
                f"embench: {metrics['embench_tests']}/{metrics['embench_expected']} "
                f"with IPC, mean IPC {mean_ipc}; "
                f"riscv-tests: {metrics['riscv_tests_passed']}/"
                f"{metrics['riscv_tests_total']} passed")
            print(f"  {ver_summary}")
        else:
            ver_passed = ver_failed = None
            ver_summary = "Verilator: skipped (--skip-verilator) — no IPC measured"

        # embench_speed_score_area_eff is the objective and the gate; the IPC figure rides
        # along because it separates the per-cycle half of a change from the
        # frequency half, which the objective alone cannot show.
        embench_speed_score_per_mhz = metrics.get("embench_speed_score_per_mhz")
        eff_ipc = ipc_area_eff(mean_ipc, area)
        eff = embench_speed_score_area_eff(embench_speed_score_per_mhz, area, fmax_mhz)
        print(f"  efficiency: {format_both_eff(mean_ipc, area, embench_speed_score_per_mhz, fmax_mhz)}")

        # Store both reports so the child can serve as the next iteration's
        # parent: the STA transcript sets the queryable worst-slack columns, and
        # the Yosys stat is what the next agent reads to find the area.
        new_rpt_text = resolve_report(syn_result.reports, STA_REPORT_SUFFIXES)
        db.save_timing_report(out_branch, new_rpt_text)
        db.save_area_report(out_branch, resolve_report(syn_result.reports,
                                                       AREA_REPORT_SUFFIXES))

        # ---- The gates ----
        if measure_error is not None:
            gates_passed, gate_reasons = False, [f"FAIL measurement: {measure_error}"]
        elif verilator_outcome is None:
            gates_passed, gate_reasons = False, [
                "SKIP gates: verilator was skipped, so neither IPC nor the "
                "riscv-test gate could be evaluated (area-only probe)"]
        else:
            seed_row = db.get_seed_branch()
            # Read before this child's own status is written, so it can never
            # be its own bar.
            gates_passed, gate_reasons = evaluate_gates(
                parent_row, fmax_mhz, child_isa, parent_isa or None,
                seed_isa=(db.load_isa_per_test(seed_row["name"])
                          if seed_row else None) or None,
                child_eff=eff,
                best=db.best_eff_branch(),
            )
        for r in gate_reasons:
            print(f"  {r}")

        parent_eff = parent_row.get("embench_speed_score_area_eff")
        improved = (eff is not None and parent_eff is not None and eff > parent_eff)
        if eff is not None and parent_eff:
            delta_pct = (eff / parent_eff - 1.0) * 100.0
            verdict = (f"{'IMPROVED' if improved else 'REGRESSED'} "
                       f"{delta_pct:+.3f}% vs parent")
        else:
            delta_pct = None
            verdict = "no comparison available"
        # The edit was written against the parent; the gate is against the best.
        best_row = db.best_eff_branch()
        best_eff = (best_row or {}).get("embench_speed_score_area_eff")
        if eff is not None and best_eff and best_row["name"] != parent_row["name"]:
            print(f"  vs best so far ({_short_branch(best_row['name'])}) "
                  f"{format_eff(best_eff)}: {(eff / best_eff - 1.0) * 100.0:+.3f}%")
        # Gates are recorded, not enforced by discarding: a child that loses
        # efficiency or trips a gate is still a measurement worth keeping, and
        # the next iteration picks its parent by querying these columns.
        status = "ok" if gates_passed else "gates_failed"
        print(f"  perf_area_eff: {format_eff(eff)} vs parent "
              f"{format_eff(parent_eff)} — {verdict}; gates "
              f"{'PASSED' if gates_passed else 'FAILED'}")

        def _row(label, parent_v, child_v, fmt=lambda v: f"{v}"):
            p = "n/a" if parent_v is None else fmt(parent_v)
            c = "n/a" if child_v is None else fmt(child_v)
            if parent_v and child_v:
                d = f"{(child_v / parent_v - 1.0) * 100.0:+.3f}%"
            else:
                d = "n/a"
            return f"| {label} | {p} | {c} | {d} |"

        summary = [
            f"# improve_perf_area: {out_branch}",
            f"Parent branch: {branch_name}",
            f"Build config: {build_config}",
            f"BoomTile (parent): {inputs['boom_tile']}",
            f"BoomTile (child):  {new_boom_tile}",
            f"Synthesis success: {syn_result.success}; STA success: "
            f"{None if timing_result is None else timing_result.success}",
            ver_summary,
            "",
            "## Objective",
            "",
            "| metric | parent | child | delta |",
            "|---|---|---|---|",
            _row("mean embench IPC", parent_row.get("mean_ipc"), mean_ipc,
                 lambda v: f"{v:.6f}"),
            _row("total cell area (um2)", parent_row.get("area"), area,
                 lambda v: f"{v:,.0f}"),
            _row("SRAM macro area (um2)", parent_row.get("sram_macro_area"),
                 sram_area, lambda v: f"{v:,.0f}"),
            _row("fmax (MHz)", parent_row.get("fmax_mhz"), fmax_mhz,
                 lambda v: f"{v}"),
            _row("embench speed/MHz", parent_row.get("embench_speed_score_per_mhz"),
                 embench_speed_score_per_mhz, lambda v: f"{v:.6f}"),
            _row("embench speed score", parent_row.get("embench_speed_score"),
                 embench_speed_score(embench_speed_score_per_mhz, fmax_mhz), lambda v: f"{v:.3f}"),
            _row("embench_speed_score_area_eff (speed/mm2) -- gates",
                 parent_eff, eff, lambda v: f"{v * 1e6:.6f}"),
            _row("ipc_area_eff (IPC/mm2) -- recorded",
                 ipc_area_eff(parent_row.get("mean_ipc"), parent_row.get("area")),
                 eff_ipc, lambda v: f"{v * 1e6:.6f}"),
            "",
            f"Verdict: **{verdict}**",
            "",
            "## Hard gates",
            "",
            *[f"- {r}" for r in gate_reasons],
            "",
            f"Gates: **{'PASSED' if gates_passed else 'FAILED'}** "
            f"(recorded as status={status})",
        ]
        _write_log("\n".join(summary) + "\n")

        db.set_metrics(
            out_branch,
            status=status,
            area=area,
            sram_macro_area=sram_area,
            std_cell_area=(None if area is None or sram_area is None
                           else area - sram_area),
            fmax_mhz=fmax_mhz,
            mean_ipc=mean_ipc,
            embench_speed_score_per_mhz=embench_speed_score_per_mhz,
            embench_speed_score=embench_speed_score(embench_speed_score_per_mhz, fmax_mhz),
            embench_speed_score_area_eff=eff,
            # Recorded alongside, not optimized: it separates a change's
            # per-cycle half from its frequency half, which the objective on
            # its own cannot show.
            ipc_area_eff=eff_ipc,
            embench_tests=metrics.get("embench_tests"),
            riscv_tests_passed=metrics.get("riscv_tests_passed"),
            riscv_tests_total=metrics.get("riscv_tests_total"),
            gates_passed=int(bool(gates_passed)),
            synthesis_success=int(bool(syn_result.success)),
            verilator_passed=ver_passed,
            verilator_failed=ver_failed,
            boom_tile_module=new_boom_tile,
        )

        print(f"\n{'='*60}\nDone: {out_branch}\n{'='*60}")
        return (final_result := {
            "status": status,
            "out_branch": out_branch,
            "area": area,
            "sram_macro_area": sram_area,
            "fmax_mhz": fmax_mhz,
            "mean_ipc": mean_ipc,
            "embench_speed_score_per_mhz": embench_speed_score_per_mhz,
            "embench_speed_score": embench_speed_score(embench_speed_score_per_mhz, fmax_mhz),
            "ipc_area_eff": eff_ipc,
            "gating_eff": eff,
            "parent_gating_eff": parent_eff,
            "delta_pct": delta_pct,
            "improved": improved,
            "gates_passed": gates_passed,
            "gate_reasons": gate_reasons,
            "synthesis_success": syn_result.success,
            "riscv_tests_passed": metrics.get("riscv_tests_passed"),
            "riscv_tests_total": metrics.get("riscv_tests_total"),
            "verilator_passed": ver_passed,
            "verilator_failed": ver_failed,
        })
    finally:
        # On failure (or unhandled exception), revert chipyard to the parent
        # branch's diff so the tree is left in a clean, reproducible state.
        # A completed run leaves the LLM/debugger edits in place — they're
        # already persisted to the DB. "gates_failed" counts as completed: the
        # measurement finished and was recorded, the child just isn't a winner.
        on_failure = (final_result is None
                      or final_result.get("status") not in ("ok", "gates_failed"))
        if diff_applied and on_failure and pg_opts is not None and inputs is not None:
            try:
                print(f"  cleanup: reverting diff to parent branch state")
                get(reset_and_apply_diff.options(**pg_opts).chia_remote(inputs["diff_dict"]))
            except Exception as e:
                print(f"  cleanup: revert diff failed: {e}")
        # Register the per-run log directory and record the final status.
        try:
            db.register_dir(out_branch, "log", instance_log_dir)
            if final_result is not None:
                db.set_metrics(out_branch, status=final_result.get("status"))
            elif on_failure:
                db.set_metrics(out_branch, status="error")
        except Exception as e:
            print(f"  cleanup: db status/log update failed: {e}")
        if experiment_tool is not None:
            try:
                experiment_tool.stop()
            except Exception as e:
                print(f"  cleanup: experiment_tool.stop() failed: {e}")
        if experiment_logger is not None:
            try:
                ray.kill(experiment_logger)
            except Exception as e:
                print(f"  cleanup: experiment_logger kill failed: {e}")
        if chipyard_bash is not None:
            try:
                chipyard_bash.stop()
            except Exception as e:
                print(f"  cleanup: chipyard_bash.stop() failed: {e}")
        if pg is not None:
            try:
                remove_placement_group(pg)
            except Exception as e:
                print(f"  cleanup: remove_placement_group failed: {e}")


def seed_flow(
    db: PerfAreaEffDB,
    build_config: str = BUILD_CONFIG,
    max_debug_retries: int = 3,
    iteration: int = 0,
    known_failures: set[str] | None = None,
    llm: LLMSpec = LLMSpec(),
    synth_flatten: bool = False,
) -> str | None:
    """Bootstrap the DB: measure the *unmodified* base RTL as the seed.

    Runs when there is no parent to optimize. Resets chipyard to a clean tree
    (empty diff), builds the design, runs CACTI + MacroCompiler, synthesizes and
    times BoomTile (so the seed carries the area and STA reports the optimizer
    reads), runs embench + riscv-tests for the baseline IPC, and stores
    everything as the ``baseline`` branch (the first DB entry). Returns the seed
    branch name, or None on failure.

    No LLM editing step; a clean baseline is expected to build and pass (build
    errors still go through build_all_thread_variants' debug retry).
    """
    out_branch = SEED_BRANCH_NAME
    db.create_branch(out_branch, parent=None, is_seed=True, iteration=iteration,
                     build_config=build_config)
    out_dir = db.branch_files_dir(out_branch)
    instance_log_dir = os.path.join(str(out_dir), "logs")
    os.makedirs(instance_log_dir, exist_ok=True)
    timing_path = os.path.join(instance_log_dir, "timing.csv")
    if not os.path.isfile(timing_path):
        with open(timing_path, "w") as f:
            f.write("iteration,step,duration_s\n")

    debug_prompt_text, debug_aux_files = _load_debug_prompt()

    pg = None
    pg_opts: dict | None = None
    chipyard_bash = None
    status = "seed_failed"
    try:
        # ---- acquire chipyard placement group + bash tool ----
        print(f"\n{'='*60}\nSeed: acquire chipyard placement group + bash tool\n{'='*60}")
        pg = placement_group([{"CPU": 1, "chipyard": 1}], strategy="STRICT_PACK")
        ray.get(pg.ready())
        pg_opts = {
            "scheduling_strategy": PlacementGroupSchedulingStrategy(
                placement_group=pg, placement_group_bundle_index=0,
            )
        }
        bash_name = f"chipyard_bash_seed_{uuid4().hex[:8]}"
        chipyard_bash = ChipyardBashTool(
            name=bash_name, work_dir=CHIPYARD_PATH, task_options=pg_opts,
            timeout_seconds=600,
        )

        # ---- reset chipyard to clean, unmodified RTL (empty diff) ----
        print(f"\n{'='*60}\nSeed: reset chipyard to unmodified base RTL\n{'='*60}")
        err, msg = get(reset_and_apply_diff.options(**pg_opts).chia_remote({}))
        print(f"  reset_and_apply_diff: {msg}")

        # ---- build all thread variants ----
        print(f"\n{'='*60}\nSeed: build {build_config} (all thread variants)\n{'='*60}")
        embench_tests, isa_tests = load_and_configure_test_binaries()
        test_binaries = list(embench_tests) + list(isa_tests)
        print(f"  Loaded {len(embench_tests)} embench + {len(isa_tests)} "
              f"riscv-tests = {len(test_binaries)} binaries")
        artifacts_by_threads = build_all_thread_variants(
            test_binaries=test_binaries,
            chipyard_bash=chipyard_bash,
            iteration=iteration,
            log_dir=instance_log_dir,
            timing_path=timing_path,
            max_debug_retries=max_debug_retries,
            label="seed_baseline",
            chipyard_task_options=pg_opts,
            collect_generated_src_for_first=True,
            debug_log_base_dir=instance_log_dir,
            branch_name=out_branch,
            debug_prompt_text=debug_prompt_text,
            debug_aux_files=debug_aux_files,
            # `config` is not optional here: build.py defaults it to the timing
            # flow's MegaBoomChiaBigCacheConfig, so leaving it off seeds the tree
            # with a baseline measured on the wrong core. ENABLE_YOSYS_FLOW=1 is
            # required for firtool to emit Verilog that Yosys' front end can
            # read; see the note in run_perf_area_loop.
            config=build_config,
            config_package=BUILD_CONFIG_PACKAGE,
            make_jobs=MAKE_JOBS,
            extra_make_args={"ENABLE_YOSYS_FLOW": "1"},
            debug_fn=LLMDebugger(llm),
        )
        if artifacts_by_threads is None:
            print(f"  Seed build failed after {max_debug_retries} retries")
            status = "build_failed"
            return None
        first_artifact = next(iter(artifacts_by_threads.values()))

        # ---- persist clean diff + generated_src ----
        _err, seed_diff = get(collect_diff.options(**pg_opts).chia_remote())
        db.save_diff(out_branch, seed_diff if not _err else {})
        db.save_generated_src(out_branch, first_artifact.generated_src_files)

        # ---- CACTI + MacroCompiler remap → resolve BoomTile ----
        print(f"\n{'='*60}\nSeed: CACTI + MacroCompiler remap\n{'='*60}")
        gen_src, cacti_libs, new_boom_tile = run_cacti_macrocompiler_prep(
            first_artifact.generated_src_files, pg_opts, CACTI_PATH,
        )
        if new_boom_tile is None:
            print(f"  Seed: could not resolve BoomTile in generated_src")
            status = "boom_tile_resolve_failed"
            return None
        _save_cacti_libs(db, out_branch, out_dir, cacti_libs)

        # ---- synthesize + time BoomTile (async), run verilator in parallel ----
        # obj_dir is a path on the synth worker's local /scratch (the cluster has
        # no shared filesystem). The head node never reads it: the reports come
        # back in memory.
        obj_dir = os.path.join(SYN_OBJ_SCRATCH_DIR, out_branch, "syn_obj")
        print(f"\n{'='*60}\nSeed: Yosys synthesis + OpenSTA (vlsi_top={new_boom_tile})\n{'='*60}")
        t_syn = time.time()
        syn_ref = synthesize_and_time.chia_remote(
            _drop_behavioral_sources(gen_src), new_boom_tile,
            obj_dir=obj_dir,
            cacti_sram_libs=cacti_libs,
            clock_period_ns=CLOCK_PERIOD_NS,
            timeout_seconds=SYNTHESIS_TIMEOUT_SECONDS,
            flatten=synth_flatten,
        )

        print(f"\n{'='*60}\nSeed: dispatch embench + riscv-tests\n{'='*60}")
        verilator_outcome = dispatch_verilator_tests(
            artifacts_by_threads=_artifact_refs(artifacts_by_threads),
            test_binaries=test_binaries,
            **_DISPATCH_LIMITS,
        )
        print(f"  Verilator: {len(verilator_outcome.results)} total, "
              f"{len(verilator_outcome.failed)} failed")
        # The seed does NOT abort on test failures: unmodified RTL already fails
        # rv64ui-{p,v}-ma_data (BOOM has no misaligned-data support), so aborting
        # would make it impossible to seed at all. Failures are recorded per test
        # and become the known-failure set every child is gated against.
        if known_failures and verilator_outcome.failed:
            unexpected = sorted(
                r.test_binary_name for r in verilator_outcome.failed
                if r.test_binary_name not in known_failures)
            if unexpected:
                print(f"  Seed: WARNING unexpected failures on clean baseline "
                      f"(not in the known-failure set): {', '.join(unexpected)}")

        # ---- collect synthesis + timing result ----
        try:
            syn_result, timing_result = get(syn_ref)
        except Exception as e:
            print(f"  Seed synthesis task raised: {e}")
            status = "synthesis_failed"
            return None
        syn_elapsed = time.time() - t_syn
        area = parse_area_from_reports(syn_result.reports)
        sram_area = _sram_macro_area(syn_result.reports, cacti_sram_libs=cacti_libs)
        fmax_mhz = timing_result.fmax_mhz if timing_result is not None else None
        print(f"  Seed synthesis+STA done in {syn_elapsed:.1f}s: "
              f"syn_success={syn_result.success}, area={area}, "
              f"sram={sram_area}, fmax={fmax_mhz} MHz")

        # ---- persist results ----
        _save_synthesis_to_db(db, out_branch, out_dir, new_boom_tile, syn_result,
                              area, syn_elapsed)
        metrics, child_isa, perf_rows, measure_error = _measure(
            out_dir, build_config, verilator_outcome, embench_tests,
        )
        db.save_perf_results(out_branch, perf_rows)
        _register_measurements(db, out_branch, out_dir)
        mean_ipc = metrics.get("mean_ipc")
        embench_speed_score_per_mhz = metrics.get("embench_speed_score_per_mhz")
        eff = embench_speed_score_area_eff(embench_speed_score_per_mhz, area, fmax_mhz)
        print(f"  efficiency: {format_both_eff(mean_ipc, area, embench_speed_score_per_mhz, fmax_mhz)}")
        if measure_error is not None:
            # A seed with an incomplete IPC set would silently become the
            # reference every later iteration is measured against.
            print(f"  Seed: {measure_error}")
            status = "seed_measurement_incomplete"
            return None

        db.save_timing_report(
            out_branch, resolve_report(syn_result.reports, STA_REPORT_SUFFIXES))
        db.save_area_report(
            out_branch, resolve_report(syn_result.reports, AREA_REPORT_SUFFIXES))
        log_path = out_dir / "improve_perf_area_log.md"
        log_path.write_text(
            f"# seed baseline: {out_branch}\n"
            f"Build config: {build_config}\n"
            f"BoomTile: {new_boom_tile}\n"
            f"Synthesis success: {syn_result.success}\n\n"
            f"## Measured baseline\n\n"
            f"- total cell area : {area:,.0f} um2\n"
            f"- SRAM macro area : "
            f"{'n/a' if sram_area is None else f'{sram_area:,.0f} um2'}\n"
            f"- fmax            : {fmax_mhz} MHz ({STA_CORNER})\n"
            f"- mean embench IPC: {mean_ipc}\n"
            f"- embench speed   : {embench_speed_score(embench_speed_score_per_mhz, fmax_mhz)} "
            f"({embench_speed_score_per_mhz} per MHz)\n"
            f"- embench with IPC: {metrics['embench_tests']}/"
            f"{metrics['embench_expected']}\n"
            f"- riscv-tests     : {metrics['riscv_tests_passed']}/"
            f"{metrics['riscv_tests_total']} passed\n"
            f"- embench_speed_score_area_eff  : {format_eff(eff)}\n"
        )
        db.register_file(out_branch, "improve_perf_area_log", log_path)
        db.set_metrics(
            out_branch,
            status="ok",
            area=area,
            sram_macro_area=sram_area,
            std_cell_area=(None if area is None or sram_area is None
                           else area - sram_area),
            fmax_mhz=fmax_mhz,
            mean_ipc=mean_ipc,
            embench_speed_score_per_mhz=embench_speed_score_per_mhz,
            embench_speed_score=embench_speed_score(embench_speed_score_per_mhz, fmax_mhz),
            embench_speed_score_area_eff=eff,
            ipc_area_eff=ipc_area_eff(mean_ipc, area),
            embench_tests=metrics.get("embench_tests"),
            riscv_tests_passed=metrics.get("riscv_tests_passed"),
            riscv_tests_total=metrics.get("riscv_tests_total"),
            gates_passed=1,
            synthesis_success=int(bool(syn_result.success)),
            verilator_passed=len(verilator_outcome.results) - len(verilator_outcome.failed),
            verilator_failed=len(verilator_outcome.failed),
            boom_tile_module=new_boom_tile,
        )
        status = "ok"
        print(f"\n{'='*60}\nSeed done: {out_branch}\n"
              f"  area={area:,.0f} um2  mean_ipc={mean_ipc}  fmax={fmax_mhz} MHz\n"
              f"  riscv-tests={metrics['riscv_tests_passed']}/{metrics['riscv_tests_total']}\n"
              f"  perf_area_eff={format_eff(eff)}\n{'='*60}")
        return out_branch
    finally:
        try:
            db.register_dir(out_branch, "log", instance_log_dir)
            if status != "ok":
                db.set_metrics(out_branch, status=status)
        except Exception as e:
            print(f"  cleanup: db status/log update failed: {e}")
        if chipyard_bash is not None:
            try:
                chipyard_bash.stop()
            except Exception as e:
                print(f"  cleanup: chipyard_bash.stop() failed: {e}")
        if pg is not None:
            try:
                remove_placement_group(pg)
            except Exception as e:
                print(f"  cleanup: remove_placement_group failed: {e}")


def _worst_slack_line(report_text: str) -> str:
    """Return the worst-slack line (MET or VIOLATED), or a placeholder."""
    _, _, line = parse_worst_slack(report_text)
    return line if line else "(no slack line found)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _dry_run(db: PerfAreaEffDB, branch_name: str) -> int:
    inputs = db.load_inputs(branch_name)
    print(f"branch={branch_name}")
    print(f"  BoomTile: {inputs['boom_tile']}")
    print(f"  generated_src files: {len(inputs['generated_src'])}")
    print(f"  timing report path: {inputs['timing_report_path']}")
    print(f"  timing report head:")
    for line in inputs["timing_report"].splitlines()[:20]:
        print(f"    {line}")
    return 0


def synth_only_flow(
    db: PerfAreaEffDB,
    branch_name: str,
    output_branch: str | None = None,
    build_config: str = BUILD_CONFIG,
    iteration: int = 1,
    synth_flatten: bool = False,
) -> dict:
    """Re-synthesize an existing branch's stored generated_src — CACTI + Yosys +
    OpenSTA only. No rebuild, no Verilator, no LLM.

    The branch's generated_src already contains the .top.mems.conf and is
    already MacroCompiler-remapped (cacti_* stubs present), so we only re-run
    CACTI characterization (dispatched from the driver, so it is head-owned and
    tunnel-safe) to regenerate the SRAM Liberty/LEF, then synthesize BoomTile
    on the stored RTL with 1 VLSI.

    Records area and fmax but NOT IPC, so perf_area_eff is left null: this is an
    area/timing re-measurement, not a comparable efficiency result.

    Result is written to a NEW branch (default ``<branch>_synth_only``) so the
    original results are preserved for comparison.
    """
    out_branch = output_branch or f"{branch_name}_synth_only"
    if db.branch_exists(out_branch):
        print(f"ERROR: output branch '{out_branch}' already exists — pass "
              f"--output-branch or remove it first")
        return {"status": "exists", "out_branch": out_branch}

    print(f"\n{'='*60}\nSynth-only resynth: {branch_name} -> {out_branch}\n{'='*60}")
    inputs = db.load_inputs(branch_name)
    generated_src = inputs["generated_src"]
    boom_tile = inputs.get("boom_tile")
    if not boom_tile:
        mods = _parse_verilog_modules(generated_src)
        boom_tile = _resolve_boom_tile_module(mods, set(mods))
    if boom_tile is None:
        print("ERROR: could not resolve BoomTile module")
        return {"status": "no_boom_tile"}
    print(f"  generated_src files: {len(generated_src)}; BoomTile: {boom_tile}")

    db.create_branch(out_branch, parent=branch_name, iteration=iteration,
                     build_config=build_config)
    out_dir = db.branch_files_dir(out_branch)

    final_result: dict | None = None
    try:
        print("  CACTI + MacroCompiler remap ...")
        gen_src, cacti_libs, new_boom_tile = run_cacti_macrocompiler_prep(
            generated_src, {}, CACTI_PATH)
        if new_boom_tile is None:
            print("  ERROR: could not resolve BoomTile in remapped generated_src")
            return {"status": "boom_tile_resolve_failed", "out_branch": out_branch}
        print(f"  CACTI libs: {len(cacti_libs) if cacti_libs else 0}; "
              f"remapped BoomTile: {new_boom_tile}")

        # Save the post-MacroCompiler LEF/Liberty (what Yosys and OpenSTA
        # consume) to the head before synthesis runs.
        _save_cacti_libs(db, out_branch, out_dir, cacti_libs)

        # BoomTile synthesis — 1 VLSI, no Verilator, no nested resource calls.
        # Synthesize the REMAPPED source with the remapped BoomTile top.
        obj_dir = os.path.join(SYN_OBJ_SCRATCH_DIR, out_branch, "syn_obj")
        print(f"  dispatching synthesis + STA (vlsi_top={new_boom_tile}) ...")
        t0 = time.time()
        syn_result, timing_result = get(synthesize_and_time.chia_remote(
            _drop_behavioral_sources(gen_src), new_boom_tile,
            obj_dir=obj_dir,
            cacti_sram_libs=cacti_libs,
            clock_period_ns=CLOCK_PERIOD_NS,
            timeout_seconds=SYNTHESIS_TIMEOUT_SECONDS,
            flatten=synth_flatten,
        ))
        elapsed = time.time() - t0
        area = parse_area_from_reports(syn_result.reports)
        sram_area = _sram_macro_area(syn_result.reports, cacti_sram_libs=cacti_libs)
        fmax_mhz = timing_result.fmax_mhz if timing_result is not None else None
        print(f"  synthesis {'OK' if syn_result.success else 'FAILED'}: "
              f"area={area}, sram={sram_area}, fmax={fmax_mhz} MHz, "
              f"elapsed={elapsed:.0f}s")

        # Persist — same DB calls as the main loop's Step 8, minus Verilator.
        _save_synthesis_to_db(db, out_branch, out_dir, new_boom_tile,
                              syn_result, area, elapsed)
        new_rpt_text = resolve_report(syn_result.reports, STA_REPORT_SUFFIXES)
        db.save_timing_report(out_branch, new_rpt_text)
        db.save_area_report(
            out_branch, resolve_report(syn_result.reports, AREA_REPORT_SUFFIXES))
        old_worst = _worst_slack_line(inputs["timing_report"])
        new_worst = _worst_slack_line(new_rpt_text) if new_rpt_text else "(no report)"
        (out_dir / "improve_perf_area_log.md").write_text(
            f"# resynth (synth-only): {out_branch}\n"
            f"Parent: {branch_name}\nBoomTile: {new_boom_tile}\n"
            f"Synthesis success: {syn_result.success}\n\n"
            f"- total cell area : {area:,.0f} um2\n"
            f"- SRAM macro area : "
            f"{'n/a' if sram_area is None else f'{sram_area:,.0f} um2'}\n"
            f"- fmax            : {fmax_mhz} MHz ({STA_CORNER})\n"
            f"- IPC             : not measured (synth-only)\n\n"
            f"## Worst-slack\nParent: {old_worst}\nChild:  {new_worst}\n")
        db.set_metrics(out_branch, status="ok", area=area,
                       sram_macro_area=sram_area,
                       std_cell_area=(None if area is None or sram_area is None
                                      else area - sram_area),
                       fmax_mhz=fmax_mhz,
                       synthesis_success=int(bool(syn_result.success)),
                       boom_tile_module=new_boom_tile)
        final_result = {
            "status": "ok" if syn_result.success else "synth_failed",
            "out_branch": out_branch, "area": area,
            "sram_macro_area": sram_area, "fmax_mhz": fmax_mhz,
            "worst_slack_parent": old_worst, "worst_slack_child": new_worst,
            "elapsed": elapsed,
        }
        print(f"\nDone: {out_branch} (area={area}, fmax={fmax_mhz} MHz, "
              f"child {new_worst})")
        return final_result
    finally:
        if final_result is None:
            try:
                db.set_metrics(out_branch, status="error")
            except Exception as e:
                print(f"  cleanup: db status update failed: {e}")


def _raise_keyboard_interrupt(signum, _frame):
    raise KeyboardInterrupt(f"received {signal.Signals(signum).name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default=None,
                    help="DB branch (parent) to optimize. If omitted and the DB "
                         "is empty, the baseline is seeded first.")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--max-debug-retries", type=int, default=3)
    ap.add_argument("--build-config", default=BUILD_CONFIG)
    ap.add_argument("--output-suffix", default="_area",
                    help="Suffix base. Output branch is "
                         "<parent><suffix>_v<N>, where N auto-increments if "
                         "<parent> already matches that pattern.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Load inputs from the DB, print timing-report head, exit")
    ap.add_argument("--skip-llm", action="store_true",
                    help="Skip the LLM edit step. Apply the parent diff "
                         "and run build+verilator+synth on it unchanged. Used for "
                         "ablation re-measurement.")
    ap.add_argument("--skip-verilator", action="store_true",
                    help="Skip verilator entirely: build once (just to "
                         "elaborate the RTL + collect Verilog), then CACTI + synth. "
                         "Yields area and fmax but NO IPC, so perf_area_eff is left "
                         "null and the gates cannot be evaluated. Pair with "
                         "--skip-llm + --diff-file to measure a diff's area alone.")
    ap.add_argument("--output-branch", default=None,
                    help="Override the auto-computed output branch name. "
                         "Useful for ablation runs that don't follow the _v<N> "
                         "auto-increment scheme.")
    ap.add_argument("--seed-only", action="store_true",
                    help="Measure the unmodified baseline into the DB, "
                         "then exit without running an optimization.")
    ap.add_argument("--prompt-file", default=IMPROVE_PERF_AREA_PROMPT_PATH,
                    help="Path to the optimization prompt markdown.")
    ap.add_argument("--no-experiment-tool", action="store_true",
                    help="Do NOT give the LLM the perf_area_experiment (sub-block "
                         "A/B synthesis) MCP tool; it gets only chipyard_bash.")
    ap.add_argument("--llm", choices=list(LLM_DEFAULT_MODELS), default=LLM_BACKEND,
                    help=f"Agent CLI for the optimization step and the "
                         f"build/test debugger (default {LLM_BACKEND}).")
    ap.add_argument("--model", default=None,
                    help="Model id for --llm (default: " + ", ".join(
                        f"{b} {m}" for b, m in LLM_DEFAULT_MODELS.items()) + ").")
    ap.add_argument("--effort", default=LLM_EFFORT,
                    help=f"Thinking level for --llm (default {LLM_EFFORT}; " + "; ".join(
                        f"{b}: {', '.join(levels)}"
                        for b, levels in LLM_EFFORT_LEVELS.items()) + ").")
    ap.add_argument("--synth-only", action="store_true",
                    help="Re-synthesize an existing --branch's stored "
                         "generated_src (CACTI + Yosys + OpenSTA — no rebuild, no "
                         "Verilator, no LLM). Records area and fmax but not IPC. "
                         "Writes a new branch <branch>_synth_only (override "
                         "with --output-branch). Requires --branch.")
    ap.add_argument("--synth-flatten", action="store_true",
                    help="Insert a Yosys `flatten` before abc. Without it abc "
                         "runs once per module (298 on a BoomTile) against a "
                         "-constr file that carries no clock, so no step ever "
                         "optimizes the tile's real cross-hierarchy worst path "
                         "and fmax moves with edits that did not touch it. "
                         "Costs: abc may not fit 1.2M cells in time or memory, "
                         "and sram_macro_area falls back to the CACTI Liberty. "
                         "Measure both before turning it on for a whole run.")
    ap.add_argument("--diff-file", default=None,
                    help="Path to a diff.json (the {'' : root, 'generators/boom': "
                         "..., ...} format collect_diff emits) to apply INSTEAD of "
                         "the parent --branch's diff. The parent only supplies the "
                         "baseline generated_src/timing_report. Pair with "
                         "--skip-llm to synthesize an external diff with no LLM "
                         "(e.g. an angela perf-feature diff).")
    ap.add_argument("--ray-address", default="auto",
                    help="Ray cluster address to connect to (default: auto).")
    args = ap.parse_args()
    try:
        llm = LLMSpec(args.llm, args.model, args.effort)
    except ValueError as e:
        ap.error(str(e))

    # Load the test suite before anything else: a run that cannot measure IPC
    # should stop here, not after an LLM edit and a build.
    embench_tests = isa_tests = None
    if not (args.dry_run or args.synth_only or args.skip_verilator):
        try:
            embench_tests, isa_tests = load_and_configure_test_binaries()
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            return 1

    # Under the job manager stdout is a file, which Python block-buffers; line
    # buffering makes `chia job logs -f` show progress as it is printed.
    sys.stdout.reconfigure(line_buffering=True)

    # Submitted with `chia job submit --working-dir .`, the job already has a
    # working_dir (the uploaded repo root), and ray.init refuses to merge
    # RUNTIME_ENV's own. Let the driver's win: workers then get the checkout and
    # the py_modules exactly as when the driver runs directly. The job's env_vars
    # (from --runtime-env-json) are kept. No effect outside a job.
    os.environ.setdefault("RAY_OVERRIDE_JOB_RUNTIME_ENV", "1")

    # PerfAreaEffDB is a chia SQLiteNode pinned to the current node, so it needs an
    # initialized Ray context — init Ray before constructing it (and before the
    # --dry-run path, which reads the DB).
    ray.init(address=args.ray_address, runtime_env=RUNTIME_ENV,
             ignore_reinit_error=True)

    # `chia job stop` stops the driver with SIGTERM, then SIGKILL once
    # RAY_JOB_STOP_WAIT_TIME_S has passed (the cluster YAML raises it for this).
    # Python's default SIGTERM action exits without running `finally`, which would
    # skip run_perf_area_loop's cleanup -- reverting the chipyard diff, stopping
    # the tool servers, releasing the placement group. Raise KeyboardInterrupt
    # instead, so a stopped job cleans up exactly as Ctrl-C does. Installed after
    # ray.init, which replaces any SIGTERM handler with its own.
    signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)

    db = PerfAreaEffDB(DB_DIR)

    if args.dry_run:
        return _dry_run(db, args.branch)

    # Synth-only resynthesis: no LLM, no build, no Verilator — just re-run
    # CACTI + Yosys + OpenSTA on the branch's stored generated_src.
    if args.synth_only:
        if not args.branch or not db.branch_exists(args.branch):
            print(f"ERROR: --synth-only requires an existing --branch "
                  f"(got '{args.branch}')")
            return 1
        result = synth_only_flow(
            db, args.branch, output_branch=args.output_branch,
            build_config=args.build_config, iteration=args.iteration,
            synth_flatten=args.synth_flatten)
        print(f"\nresult: {json.dumps(result, indent=2, default=str)}")
        return 0 if result.get("status") == "ok" else 1

    # Bootstrap: with no entries in the DB there is no parent — seed the baseline
    # from the unmodified RTL first, then optimize from it.
    parent = args.branch
    if not db.has_any_branch():
        print("DB is empty — seeding baseline from unmodified RTL via seed_flow()")
        if args.branch is not None:
            print(f"  (ignoring --branch '{args.branch}'; DB has no entries to use as parent)")
        seed = seed_flow(db, build_config=args.build_config,
                         max_debug_retries=args.max_debug_retries,
                         known_failures=BASELINE_KNOWN_FAILURES, llm=llm,
                         synth_flatten=args.synth_flatten)
        if seed is None:
            print("seed_flow failed — see DB status and logs")
            return 1
        parent = seed
    elif parent is None:
        print("ERROR: DB already seeded; pass --branch <parent> to choose what to optimize")
        return 1
    elif not db.branch_exists(parent):
        print(f"ERROR: --branch '{parent}' not found in DB")
        return 1

    if args.seed_only:
        print(f"--seed-only: baseline ready ({parent}); exiting without optimization")
        return 0

    diff_override = None
    if args.diff_file:
        with open(args.diff_file) as f:
            diff_override = json.load(f)
        print(f"Loaded diff override from {args.diff_file} "
              f"({len(diff_override)} repo parts)")

    result = run_perf_area_loop(
        db=db,
        branch_name=parent,
        skip_llm=args.skip_llm,
        skip_verilator=args.skip_verilator,
        output_branch=args.output_branch,
        iteration=args.iteration,
        max_debug_retries=args.max_debug_retries,
        build_config=args.build_config,
        output_suffix=args.output_suffix,
        prompt_path=args.prompt_file,
        enable_experiment_tool=not args.no_experiment_tool,
        llm=llm,
        embench_tests=embench_tests,
        isa_tests=isa_tests,
        diff_override=diff_override,
        synth_flatten=args.synth_flatten,
    )
    print(f"\nresult: {json.dumps(result, indent=2, default=str)}")
    # "gates_failed" means the loop closed and recorded a comparable measurement
    # that simply is not an improvement; that is a successful run of the flow.
    return 0 if result.get("status") in ("ok", "gates_failed") else 1


if __name__ == "__main__":
    sys.exit(main())
