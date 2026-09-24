"""The verilator suites: embench cycle counts and riscv-tests pass/fail.

The performance half of the objective, the counterpart to
boom_tile_syn_open.py's area and timing. Every embench benchmark and every rv64gc
ISA test runs on the verilator workers; embench yields per-benchmark ROI cycle
counts and the ISA tests yield a compliance verdict. Scoring those cycle counts
against Embench's reference platform gives ``embench_speed_score_per_mhz``, which
times fmax and over the cell area is the figure this flow optimizes. Mean IPC is
reported alongside, but is not what the gates use.

The cycle counts come from the benchmarks' own ROI counters, not from the TMA
hardware, because those counters come from the `WithBoomTMACounters` config
mixin, which only MegaBoomChiaBigCacheConfig applies -- see improve_perf_area.py
for the full reasoning.

The loaders (``load_embench`` / ``load_isa``), the outcome classifier and the
result writers are consumed by improve_perf_area.py, which dispatches the suites
itself.
"""

import json
import math
import re
from pathlib import Path

from chia.chipyard.state_def import RunResult
from common.common_helpers import load_test_binaries
from perf_area_eff_opt.constants import (
    EMBENCH_TIMEOUT_CYCLES,
    EMBENCH_WORKLOADS_THREAD_MAP,
)

# Built on the head from the benchmarks submodule (see its README), not taken
# from the chipyard image: the image's prebuilt embench set has no
# ROI instrumentation. RUNTIME_ENV excludes benchmarks/ from the job upload, so
# these travel to the workers as TestBinary.content instead.
_BENCH_ROOT = Path(__file__).resolve().parents[1] / "benchmarks"
EMBENCH_DIR = _BENCH_ROOT / "embench" / "build"
ISA_DIR = _BENCH_ROOT / "riscv-tests" / "isa" / "build"

# A cycle budget only bounds a benchmark that hangs: a healthy one exits at its
# natural cycle count however large the budget is. So this scale is nearly free
# insurance, and worth having because EMBENCH_TIMEOUT_CYCLES was measured
# against the image's prebuilt ELFs while ours were compiled by a different
# GCC. Raise it if a benchmark reports outcome=timeout.
EMBENCH_TIMEOUT_SCALE = 2.0

# Embench's reference times in milliseconds, verbatim from upstream
# baseline-data/speed.json. The reference platform is an STM32F4 Discovery
# (Cortex-M4, no FPU) at 16MHz, built with GLOBAL_SCALE_FACTOR=16, so each entry
# covers 16 units of work; see embench_speed_score_per_mhz for how that cancels.
EMBENCH_SPEED_BASELINE_MS = {
    "aha-mont64": 4002, "crc32": 4006, "depthconv": 3842, "edn": 4006,
    "huffbench": 3993, "matmult-int": 4010, "md5sum": 3931, "nettle-aes": 3956,
    "nettle-sha256": 3998, "nsichneu": 4303, "picojpeg": 3915, "qrduino": 3927,
    "sglib-combined": 4131, "slre": 3995, "statemate": 6421, "tarfind": 4005,
    "ud": 3934, "wikisort": 3622, "xgboost": 3528,
}

# The GLOBAL_SCALE_FACTOR *our* binaries are built with -- see the benchmarks
# submodule's Makefile. Embench's score formula multiplies by it, which is what
# makes a run at a different scale factor comparable with the reference.
EMBENCH_GSF = 1
# The -v (virtual memory) ISA tests build page tables before reaching the test
# body, so they need far more headroom than the -p assembly tests.
ISA_TIMEOUT_CYCLES = 2_000_000

# Default threads, used by every ISA test and by any benchmark missing from
# EMBENCH_WORKLOADS_THREAD_MAP. The 239 ISA tests are short and there are many
# of them, so throughput (one slot each) beats latency for those; the benchmark
# tail is the opposite case and is threaded by that map instead.
VERILATOR_THREADS = 1

# roi.h prints both readings from one printf inside stop_trigger(), on stdout
# over HTIF -- so RunResult.log, not RunResult.out (which is stderr through
# spike-dasm). Both lines appear together or not at all: roi_before() only
# latches the counters, so a benchmark killed mid-kernel prints neither.
_ROI_RE = re.compile(r"ROI_(BEFORE|AFTER):\s*cycles=(\d+)\s+instret=(\d+)")

# The simulator's verdicts. Chipyard's Verilator harness is TestDriver.v plus
# testchipip's SimTSI -- not rocket-chip's emulator.cc, whose `*** FAILED ***
# via dtm/jtag/trace_count` wording is in the same tree but never reached from
# this flow. Taken from the harness and confirmed against real runs:
#   TestDriver.v:166  $fdisplay(stderr, "*** FAILED ***%s after %d simulation cycles")
#   TestDriver.v:174  $fdisplay(stderr, "*** PASSED *** Completed after %d simulation cycles")
# with %s = " (timeout)" when +max-cycles was exceeded. Verilog's %d is space
# padded, hence \s+ before each count.
# The gap before `(timeout)` is wide and variable: `reason` is a fixed-width
# Verilog string reg, so %s pads it out to the full register width. `Completed`
# on the pass line is a literal and needs no such allowance.
_PASSED_RE = re.compile(
    r"\*\*\* PASSED \*\*\* Completed after\s+(\d+) simulation cycles")
_TIMEOUT_RE = re.compile(
    r"\*\*\* FAILED \*\*\*\s*\(timeout\) after\s+(\d+) simulation cycles")
# A nonzero write to tohost trips SimTSI.scala:21's Chisel assert, which $stops
# the run before TestDriver.v can print a cycle count -- so those two are not
# alternatives to these. The code arrives twice over: from fesvr's
# syscall.cc:217 on stderr, and from the assert itself on stdout. It is the HTIF
# exit code, which for riscv-tests is the number of the assertion that failed
# and for embench is 1337, baremetal_init.c's handle_trap catch-all.
_TOHOST_RE = re.compile(r"\*\*\* FAILED \*\*\* \(tohost = (\d+)\)")
_EXIT_CODE_RE = re.compile(r"\*\*\* FAILED \*\*\* \(exit code =\s+(\d+)\)")

_EMBENCH_TRAP_CODE = "1337"


def parse_roi(result: RunResult) -> dict | None:
    """Return the ROI cycle/instret deltas and IPC, or None if not measured."""
    readings = {kind: (int(cycles), int(instret))
                for kind, cycles, instret in _ROI_RE.findall(result.log)}
    if "BEFORE" not in readings or "AFTER" not in readings:
        return None
    cycles = readings["AFTER"][0] - readings["BEFORE"][0]
    instret = readings["AFTER"][1] - readings["BEFORE"][1]
    if cycles <= 0:
        return None
    return {
        "roi_cycles": cycles,
        "roi_instret": instret,
        "ipc": round(instret / cycles, 6),
    }


def total_cycles(result: RunResult) -> int | None:
    """Whole-run cycle count the simulator reports as it exits."""
    m = _PASSED_RE.search(result.out) or _TIMEOUT_RE.search(result.out)
    return int(m.group(1)) if m else None


def classify_outcome(result: RunResult) -> tuple[str, str]:
    """Return ``(outcome, detail)`` for one run.

    ``outcome`` is one of ``pass``, ``timeout``, ``trap``, ``assert_failed``,
    ``killed`` or ``unknown``, so failures can be grouped without re-reading
    logs.
    """
    if result.success:
        return "pass", ""
    m = _TIMEOUT_RE.search(result.out)
    if m:
        return "timeout", f"reached the cycle budget after {m.group(1)} cycles"
    m = _TOHOST_RE.search(result.out) or _EXIT_CODE_RE.search(result.log)
    if m:
        if m.group(1) == _EMBENCH_TRAP_CODE:
            return "trap", ("took an unhandled trap; handle_trap in "
                            "baremetal_init.c exits with 1337")
        return "assert_failed", (
            f"wrote {m.group(1)} to tohost; for riscv-tests that is the "
            f"number of the failing assertion, findable in the test's .S source")
    if result.returncode < 0:
        return "killed", (f"simulator killed by signal {-result.returncode}, "
                          f"which is how the wall-clock timeout presents")
    return "unknown", f"simulator exited {result.returncode} with no verdict line"


def isa_suite(name: str) -> str:
    """``rv64ui-p-add`` -> ``rv64ui``, the suite riscv-tests built it under."""
    return name.split("-", 1)[0]


def load_embench(only: list[str] | None, timeout_scale: float):
    tests = load_test_binaries(EMBENCH_DIR, only)
    for tb in tests:
        budget = EMBENCH_TIMEOUT_CYCLES.get(
            tb.name, EMBENCH_TIMEOUT_CYCLES["default"])
        tb.timeout_cycles = int(budget * timeout_scale)
        tb.verilator_threads = EMBENCH_WORKLOADS_THREAD_MAP.get(
            tb.name, VERILATOR_THREADS)
    return tests


def load_isa(suites: list[str] | None, timeout_cycles: int):
    tests = load_test_binaries(ISA_DIR)
    if suites:
        tests = [tb for tb in tests if isa_suite(tb.name) in suites]
    for tb in tests:
        # ISA tests are compliance evidence, not data for the DB the timing
        # loop trains on, and there are an order of magnitude more of them
        # than there are benchmarks.
        tb.log_to_db = False
        tb.timeout_cycles = timeout_cycles
        tb.verilator_threads = VERILATOR_THREADS
    return tests


def embench_speed_score_per_mhz(per_test: dict[str, dict]) -> float | None:
    """Embench's speed score divided by the clock rate, from ROI cycle counts.

    Embench scores a benchmark as ``baseline_ms / measured_ms * gsf`` and then
    divides by the clock rate (benchmark_speed.py's compute_rel and its
    per-MHz output). With ``measured_ms = cycles / mhz / 1000`` -- the
    conversion its own target modules use -- the clock rate cancels, leaving
    ``baseline_ms * 1000 * gsf / cycles``. So this figure is fixed by the RTL
    alone and can be computed here, before synthesis has reported an fmax;
    multiplying it by that fmax later gives the score itself.

    Returns the geometric mean over every benchmark that produced ROI cycles, or
    None if none did. Benchmarks with no reference time are skipped rather than
    scored against a guess.
    """
    rel = [EMBENCH_SPEED_BASELINE_MS[name] * 1000.0 * EMBENCH_GSF / e["roi_cycles"]
           for name, e in per_test.items()
           if name in EMBENCH_SPEED_BASELINE_MS and e.get("roi_cycles")]
    if not rel:
        return None
    return round(math.exp(sum(math.log(r) for r in rel) / len(rel)), 6)


def write_embench_results(out_dir: Path, config: str, results: list[RunResult],
                          expected: list[str]) -> dict:
    """Write perf.json and return its summary section."""
    per_test: dict[str, dict] = {}
    missing: list[str] = []
    for r in results:
        outcome, detail = classify_outcome(r)
        entry = {"outcome": outcome, "returncode": r.returncode,
                 "total_cycles": total_cycles(r)}
        if detail:
            entry["detail"] = detail
        roi = parse_roi(r)
        if roi:
            entry.update(roi)
        else:
            # An unmeasured benchmark is reported, never averaged away: a mean
            # over a silently smaller set would look like a faster core.
            missing.append(r.test_binary_name)
        per_test[r.test_binary_name] = entry

    missing += [n for n in expected if n not in per_test]
    ipcs = [e["ipc"] for e in per_test.values() if "ipc" in e]
    mean_ipc = round(sum(ipcs) / len(ipcs), 6) if ipcs else None

    summary = {
        "embench_mean_ipc": mean_ipc,
        "embench_speed_score_per_mhz": embench_speed_score_per_mhz(per_test),
        "embench_tests": len(ipcs),
        "embench_expected": len(expected),
        "embench_missing_ipc": sorted(set(missing)),
    }
    (out_dir / "perf.json").write_text(json.dumps(
        {"config": config, **summary, "per_test": per_test}, indent=2) + "\n")
    return summary


def write_isa_results(out_dir: Path, config: str,
                      results: list[RunResult]) -> dict:
    """Write riscv_tests.json plus a log per failure; return the summary."""
    per_test: dict[str, dict] = {}
    by_suite: dict[str, dict[str, int]] = {}
    log_dir = out_dir / "riscv_tests_failures"

    for r in results:
        outcome, detail = classify_outcome(r)
        name = r.test_binary_name
        per_test[name] = {"outcome": outcome, "returncode": r.returncode}
        if detail:
            per_test[name]["detail"] = detail
        counts = by_suite.setdefault(isa_suite(name), {"passed": 0, "total": 0})
        counts["total"] += 1
        counts["passed"] += int(outcome == "pass")
        if outcome != "pass":
            # Keep the evidence for failure analysis, but
            # only for failures: 239 passing transcripts are just noise.
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / f"{name}.log").write_text(
                f"=== outcome: {outcome} ({detail}) ===\n"
                f"=== returncode: {r.returncode} ===\n"
                f"=== stdout (.log) ===\n{r.log}\n"
                f"=== stderr (.out, tail) ===\n{r.out[-100_000:]}\n")

    passed = sum(1 for e in per_test.values() if e["outcome"] == "pass")
    summary = {
        "riscv_tests_passed": passed,
        "riscv_tests_total": len(per_test),
    }
    (out_dir / "riscv_tests.json").write_text(json.dumps({
        "config": config, **summary,
        "by_suite": dict(sorted(by_suite.items())),
        "failures": {n: e for n, e in sorted(per_test.items())
                     if e["outcome"] != "pass"},
        "per_test": dict(sorted(per_test.items())),
    }, indent=2) + "\n")
    return summary
