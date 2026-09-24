"""Ray runtime-env config for running the perf-area-efficiency example as a
standalone script.
"""

from pathlib import Path

# Repo checkout root, resolved relative to this file
# (examples/perf_area_eff_opt/common_constants.py → parents[2]) so nothing is
# hardcoded to one clone location.
_REPO_ROOT = Path(__file__).resolve().parents[2]

RUNTIME_ENV = {
    # Ship the checkout as the job's working_dir, and the packages the
    # pipeline's ChiaFunctions are pickled against (chia.*, common.*,
    # sky130_vlsi.*, perf_area_eff_opt.*) as py_modules so they are top-level
    # importable on every worker — the repo-root working_dir alone does not
    # put examples/ on the workers' sys.path.
    #
    # This must name THIS package: py_modules is what the workers import from,
    # so shipping a sibling example would silently run them against its
    # constants (its DB_DIR, its BUILD_CONFIG, its CACTI path) no matter what
    # the driver read on the head.
    "working_dir": str(_REPO_ROOT),
    "py_modules": [
        str(_REPO_ROOT / "chia"),
        str(_REPO_ROOT / "examples" / "common"),
        str(_REPO_ROOT / "examples" / "sky130_vlsi"),
        str(_REPO_ROOT / "examples" / "perf_area_eff_opt"),
    ],
    # gitignore-style patterns, applied to working_dir and py_modules uploads
    # alike. DB/ (the head-only SQLite store + files tree), fpga_builds/, out/,
    # sibling examples' verilatorbins/ and the caches dominate the upload size.
    # benchmarks/ is excluded too: its binaries reach the workers as
    # TestBinary.content instead (see embench_isa_tests.py).
    "excludes": [
        "/DB/",
        "/fpga_builds/",
        "verilatorbins/ubench/",
        "__pycache__",
        ".mypy_cache",
        "benchmarks/",
        "out/",
    ],
}
