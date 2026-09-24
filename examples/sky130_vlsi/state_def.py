from dataclasses import dataclass, field


@dataclass
class SynthesisResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    reports: dict[str, str] = field(default_factory=dict)  # filename -> contents


@dataclass
class TimingResult:
    """Post-synthesis static timing, for flows whose synthesis tool reports none.

    Slacks are in nanoseconds and are positive when the constraint is met.
    ``min_period_ns``/``fmax_mhz`` come from OpenSTA's ``report_clock_min_period``
    and describe the speed the netlist actually achieves, independent of the
    clock period it was constrained with.
    """
    success: bool
    stdout: str
    stderr: str
    returncode: int
    setup_slack_ns: float | None = None
    hold_slack_ns: float | None = None
    min_period_ns: float | None = None
    fmax_mhz: float | None = None
    reports: dict[str, str] = field(default_factory=dict)  # filename -> contents
