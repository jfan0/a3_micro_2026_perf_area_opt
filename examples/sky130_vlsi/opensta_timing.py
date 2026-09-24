"""OpenSTA timing for the open-source Sky130 synthesis flow.

Hammer's Yosys plugin reports area but not timing: its ``generate_reports`` step
writes only ``<top>.synth_check.rpt`` and ``<top>.synth_stat.txt``. Hammer also
ships no open-source timing plugin, since ``hammer/timing`` holds only Tempus.
Timing for this flow therefore comes from driving OpenSTA over the mapped
netlist directly. OpenSTA is bundled with OpenROAD, already in the Chia CACTI
image as ``sta``.

The constraints have to be written here too: the SDC Yosys emits carries only
``set_driving_cell`` and ``set_load``, with no ``create_clock``.
"""

import logging
import os
import re
import shutil
import subprocess
import tempfile

from chia.base.ChiaFunction import ChiaFunction
from sky130_vlsi.state_def import TimingResult

logger = logging.getLogger(__name__)

# Marker printed before each report so the metrics can be told apart: setup and
# hold slack both print an otherwise identical "worst slack <n>" line.
_MARK = "CHIA_METRIC"

_WORST_SLACK_RE = re.compile(r"worst slack\s+(-?[\d.]+)")
_MIN_PERIOD_RE = re.compile(r"period_min\s*=\s*([\d.]+)\s+fmax\s*=\s*([\d.]+)")


def _build_sta_script(
    netlist_path: str,
    top_module: str,
    liberty_files: list[str],
    clock_port: str,
    clock_period_ns: float,
    max_paths: int,
    extra_sdc: str | None,
) -> str:
    lines = [f"read_liberty {lib}" for lib in liberty_files]
    lines += [
        f"read_verilog {netlist_path}",
        f"link_design {top_module}",
        f"create_clock -name {clock_port} -period {clock_period_ns} "
        f"[get_ports {clock_port}]",
    ]
    if extra_sdc:
        lines.append(extra_sdc)
    lines += [
        f'puts "{_MARK} setup_slack"',
        "report_worst_slack -max -digits 4",
        f'puts "{_MARK} hold_slack"',
        "report_worst_slack -min -digits 4",
        f'puts "{_MARK} min_period"',
        "report_clock_min_period",
        f'puts "{_MARK} critical_paths"',
        f"report_checks -path_delay max -digits 4 -group_count {max_paths}",
    ]
    return "\n".join(lines) + "\n"


def _parse_metrics(stdout: str) -> dict[str, float]:
    """Pull the marked metrics out of an OpenSTA transcript.

    Each metric's value is on a line after its ``CHIA_METRIC <name>`` marker, so
    walk the transcript and attribute values to whichever marker is in scope.
    """
    metrics: dict[str, float] = {}
    current: str | None = None
    for line in stdout.splitlines():
        if line.startswith(_MARK):
            parts = line.split()
            current = parts[1] if len(parts) > 1 else None
            continue
        if current in ("setup_slack", "hold_slack"):
            m = _WORST_SLACK_RE.search(line)
            if m:
                metrics[current] = float(m.group(1))
                current = None
        elif current == "min_period":
            m = _MIN_PERIOD_RE.search(line)
            if m:
                metrics["min_period"] = float(m.group(1))
                metrics["fmax"] = float(m.group(2))
                current = None
    return metrics


def run_opensta(
    netlist_path: str,
    top_module: str,
    liberty_files: list[str],
    clock_port: str = "clock",
    clock_period_ns: float = 10.0,
    sta_bin: str = "sta",
    work_dir: str | None = None,
    extra_sdc: str | None = None,
    max_paths: int = 100,
    timeout_seconds: int = 21600,
) -> TimingResult:
    """Run OpenSTA over a mapped netlist and return its timing metrics.

    Args:
        netlist_path: Mapped gate-level Verilog, e.g. ``<top>.mapped.v``.
        top_module: Design to ``link_design``.
        liberty_files: Liberty files for one corner, standard cells first.
            Every cell in the netlist must be covered, macros included.
        clock_port: Top-level clock port to constrain.
        clock_period_ns: Period for ``create_clock``. Slack is relative to this;
            ``min_period_ns``/``fmax_mhz`` are not.
        sta_bin: OpenSTA executable.
        work_dir: Where to write the script and report. A temp dir if omitted.
        extra_sdc: Additional constraints, inserted after ``create_clock``.
        max_paths: Path groups for the critical-path report.
        timeout_seconds: Subprocess timeout.
    """
    if not os.path.isfile(netlist_path):
        return TimingResult(
            success=False, stdout="", stderr=f"Netlist not found: {netlist_path}",
            returncode=-1,
        )
    missing = [lib for lib in liberty_files if not os.path.isfile(lib)]
    if not liberty_files or missing:
        return TimingResult(
            success=False, stdout="",
            stderr=f"Liberty files missing or empty: {missing or liberty_files}",
            returncode=-1,
        )

    owns_work_dir = work_dir is None
    work_dir = work_dir or tempfile.mkdtemp(prefix="opensta_")
    try:
        return _run_opensta_in(
            work_dir, netlist_path, top_module, liberty_files, clock_port,
            clock_period_ns, sta_bin, extra_sdc, max_paths, timeout_seconds,
        )
    finally:
        if owns_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)


def _run_opensta_in(
    work_dir: str,
    netlist_path: str,
    top_module: str,
    liberty_files: list[str],
    clock_port: str,
    clock_period_ns: float,
    sta_bin: str,
    extra_sdc: str | None,
    max_paths: int,
    timeout_seconds: int,
) -> TimingResult:
    os.makedirs(work_dir, exist_ok=True)
    script_path = os.path.join(work_dir, f"{top_module}.sta.tcl")
    with open(script_path, "w") as f:
        f.write(_build_sta_script(
            netlist_path, top_module, liberty_files, clock_port,
            clock_period_ns, max_paths, extra_sdc,
        ))

    try:
        # -no_splash keeps the banner out of the transcript; -exit quits when the
        # script ends instead of dropping into the interactive shell.
        proc = subprocess.run(
            [sta_bin, "-no_splash", "-exit", script_path],
            cwd=work_dir, capture_output=True, text=True,
            timeout=timeout_seconds,
        )
        stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"OpenSTA timed out after {timeout_seconds}s")
        return TimingResult(
            success=False, stdout="", stderr=f"OpenSTA timeout ({timeout_seconds}s)",
            returncode=-1,
        )
    except OSError as e:
        logger.error(f"Could not run {sta_bin}: {e}")
        return TimingResult(success=False, stdout="", stderr=str(e), returncode=-1)

    metrics = _parse_metrics(stdout)
    if returncode != 0:
        logger.error(f"OpenSTA failed (rc={returncode}); stderr tail: {stderr[-500:]}")
    elif "setup_slack" not in metrics:
        logger.warning("OpenSTA produced no setup slack; check the transcript")

    # Written where hammer_syn._collect_reports already looks, so the transcript
    # travels back with the synthesis reports.
    report_name = f"{top_module}.sta.rpt"
    report_path = os.path.join(work_dir, report_name)
    with open(report_path, "w") as f:
        f.write(stdout)

    result = TimingResult(
        success=(returncode == 0 and "setup_slack" in metrics),
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        setup_slack_ns=metrics.get("setup_slack"),
        hold_slack_ns=metrics.get("hold_slack"),
        min_period_ns=metrics.get("min_period"),
        fmax_mhz=metrics.get("fmax"),
        reports={report_name: stdout},
    )
    if result.success:
        logger.info(
            f"OpenSTA {top_module}: setup slack {result.setup_slack_ns} ns, "
            f"hold slack {result.hold_slack_ns} ns, fmax {result.fmax_mhz} MHz"
        )
    return result


class OpenStaTimingNode:
    """Time a mapped netlist on a VLSI worker.

    Takes the netlist as contents rather than a path so the call does not have
    to land on the same worker that ran synthesis. The Liberty files stay paths,
    since the PDK is installed on the worker.
    """

    def __init__(
        self,
        netlist: str,
        top_module: str,
        liberty_files: list[str],
        clock_port: str = "clock",
        clock_period_ns: float = 10.0,
        sta_bin: str = "sta",
        extra_sdc: str | None = None,
        max_paths: int = 100,
        timeout_seconds: int = 21600,
    ):
        self.netlist = netlist
        self.top_module = top_module
        self.liberty_files = liberty_files
        self.clock_port = clock_port
        self.clock_period_ns = clock_period_ns
        self.sta_bin = sta_bin
        self.extra_sdc = extra_sdc
        self.max_paths = max_paths
        self.timeout_seconds = timeout_seconds

    @ChiaFunction(resources={"VLSI": 1})
    def timing(self) -> TimingResult:
        work_dir = tempfile.mkdtemp(prefix="opensta_")
        try:
            netlist_path = os.path.join(work_dir, f"{self.top_module}.mapped.v")
            with open(netlist_path, "w") as f:
                f.write(self.netlist)
            return run_opensta(
                netlist_path=netlist_path,
                top_module=self.top_module,
                liberty_files=self.liberty_files,
                clock_port=self.clock_port,
                clock_period_ns=self.clock_period_ns,
                sta_bin=self.sta_bin,
                work_dir=work_dir,
                extra_sdc=self.extra_sdc,
                max_paths=self.max_paths,
                timeout_seconds=self.timeout_seconds,
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
