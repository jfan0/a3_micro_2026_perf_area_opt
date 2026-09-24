"""Custom Hammer CLI driver used by Chia's open-source synthesis node.

Subclasses ``hammer.vlsi.CLIDriver`` to repair the Yosys ``syn_generic``
synthesis step, which maps flip-flops with ``dfflibmap -map-only``. The
``-map-only`` flag skips the ``-prepare`` pass that rewrites Yosys's internal
FF cells into the flavours the target library actually provides. Because
``sky130_fd_sc_hd`` has no synchronous-reset flop, every ``$_SDFFE_*`` survives
unmapped, which both breaks downstream STA (the netlist still contains Yosys
internal cells) and silently drops all sequential area from ``stat`` -- an
8-bit counter reports 92.59um2 unmapped versus 289.03um2 mapped.

Invoked as a script with the same CLI as ``hammer-vlsi``.
"""
import os
import re

from hammer.vlsi import CLIDriver, HammerTool
from hammer.vlsi.hooks import HammerToolHookAction

# Liberty groups that make a library a useful dfflibmap target. CACTI SRAM
# libraries land in the same typical corner as the standard cells and so are
# picked up by the same filter, but they define no sequential cells; handing one
# to dfflibmap is at best a no-op and at worst an error.
_SEQUENTIAL_GROUP_RE = re.compile(r"^\s*(ff|latch)\s*\(", re.MULTILINE)


def _has_sequential_cells(liberty_path: str) -> bool:
    try:
        with open(liberty_path, "r", errors="replace") as f:
            return _SEQUENTIAL_GROUP_RE.search(f.read()) is not None
    except OSError:
        return False


def _flatten_step() -> str:
    """``flatten``, or a comment explaining its absence.

    Off by default. Set ``CHIA_YOSYS_FLATTEN=1`` on the synthesis worker to
    enable it -- via the job's runtime_env env_vars, since this driver runs as
    a subprocess of the Ray worker and inherits its environment.

    Why it matters: without it the design stays hierarchical and the `abc` below
    runs once per module (298 times on a BoomTile), each against `-D` alone --
    the -constr file carries only set_driving_cell and set_load, no clock. Every
    module therefore assumes it owns the whole period, while the tile's worst
    path crosses module boundaries and nobody optimizes it. Measured: the design
    has never met its 20 ns target, and an edit anywhere reshuffles every
    module's local optimum, moving fmax by up to 20% for reasons unrelated to
    the edit.

    Why it is off by default: flattening 1.2M cells into one AIG may exceed
    ABC's time or memory here, and it removes the SRAM wrapper modules that
    boom_tile_syn_open._sram_macro_area identifies macros by -- that figure goes
    null rather than wrong when this is on. Measure both before switching.
    """
    if os.environ.get("CHIA_YOSYS_FLATTEN", "").strip() not in ("", "0", "false"):
        return "flatten"
    return "# flatten: off (set CHIA_YOSYS_FLATTEN=1 to enable)"


def _syn_generic_mapped_flops(ht: HammerTool) -> bool:
    """``syn_generic`` with a dfflibmap that actually maps the flip-flops."""
    if ht._database.has_setting("synthesis.yosys.latch_map_file"):
        latch_map = f"techmap -map {ht.get_setting('synthesis.yosys.latch_map_file')}"
    else:
        latch_map = ""

    flatten = _flatten_step()
    ht.logger.info(f"yosys flatten: {'ON' if flatten == 'flatten' else 'off'}")

    ht.block_append(f"""
    yosys proc
    hierarchy -check -top {ht.top_module}

    synth -top {ht.top_module}

    # Flatten before abc so it sees the cross-hierarchy paths (see _flatten_step)
    {flatten}

    # Optimize the design
    opt -purge

    # Technology mapping of latches
    {latch_map}

    # Technology mapping of flip-flops
    """)
    for liberty_file in ht.liberty_files_tt.split():
        if not _has_sequential_cells(liberty_file):
            ht.logger.info(
                f"Skipping dfflibmap for {liberty_file}: no sequential cells"
            )
            continue
        ht.verbose_append(f"dfflibmap -liberty {liberty_file}")
    ht.verbose_append("opt")

    ht.write_sdc_file()
    return True


def _generate_reports_all_liberties(ht: HammerTool) -> bool:
    """``generate_reports`` with every typical-corner Liberty given to ``stat``.

    Hammer passes only the first, so a macro defined in any other library -- the
    CACTI SRAMs, in this flow -- has no known area and is dropped from the total
    with only a warning, which is how a BOOM tile's caches would silently
    vanish from its area. ``stat`` accumulates cell areas over repeated
    ``-liberty`` options.
    """
    liberty_args = " ".join(f"-liberty {lib}" for lib in ht.liberty_files_tt.split())
    ht.block_append(f"""
    tee -o {ht.run_dir}/{ht.top_module}.synth_check.rpt check

    tee -o {ht.run_dir}/{ht.top_module}.synth_stat.txt stat -top {ht.top_module} {liberty_args}
    """)
    return True


class ChiaOpenCLIDriver(CLIDriver):
    def get_extra_synthesis_hooks(self) -> list[HammerToolHookAction]:
        return [
            HammerTool.make_replacement_hook(
                "syn_generic", _syn_generic_mapped_flops
            ),
            HammerTool.make_replacement_hook(
                "generate_reports", _generate_reports_all_liberties
            ),
        ]


def main() -> None:
    ChiaOpenCLIDriver().main()


if __name__ == "__main__":
    main()
