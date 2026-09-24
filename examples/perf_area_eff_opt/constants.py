"""Configuration for the BoomTile performance-area-efficiency loop.

Only the knobs this flow actually reads live here; the shared
build/verilator/synthesis helpers it calls (in ``common``) take their own
defaults as keyword arguments.
"""

import os
from pathlib import Path


# Path to the chipyard checkout INSIDE the chisel-build / LLM docker images.
CHIPYARD_PATH = os.environ.get("PERF_AREA_EFF_CHIPYARD_PATH", "/home/ray/chipyard/")
BOOM_REPO_PATH = str(Path(CHIPYARD_PATH) / "generators/boom/src/main/scala/v3/")

# Which BOOM config this loop optimizes. The seed run measures it from
# unmodified RTL, and every later iteration is compared against that seed.
BUILD_CONFIG = "MediumBoomV3Config"
BUILD_CONFIG_PACKAGE = "chipyard"

# LLM working directory inside the Docker container (not the host) -- the CWD
# the agent CLI runs in. Created empty by the cluster setup's
# `mkdir -p /home/ray/llm_env`; this flow ships all prompts in this package
# under prompts/ and sends them inline, so nothing needs to live in this dir.
LLM_ENV = os.environ.get("PERF_AREA_EFF_LLM_ENV", "/home/ray/llm_env")

# --- Objective -------------------------------------------------------------

# --- LLM -------------------------------------------------------------------

# The agent CLI, chosen per run with --llm. Both ship in the llm_1 container,
# each against its own staged credentials (see perf_area_eff_cluster.yaml).
LLM_BACKEND = "claude"

# --model's default per backend.
LLM_DEFAULT_MODELS = {
    "codex": "gpt-6-astra",
    "claude": "claude-opus-5",
}

# --effort, the thinking level. Codex takes it as model_reasoning_effort and
# Claude as --effort, and the two CLIs accept different sets of levels.
LLM_EFFORT_LEVELS = {
    "codex": ("minimal", "low", "medium", "high", "xhigh"),
    "claude": ("low", "medium", "high", "xhigh", "max"),
}
LLM_EFFORT = "xhigh"

# Pre-expanded on the head node before being sent inline, so $ARGUMENTS / $1 and
# the report-path placeholders are substituted driver-side. Resolved relative to
# this package so the example stays self-contained wherever the repo is checked
# out.
IMPROVE_PERF_AREA_PROMPT_PATH = str(
    Path(__file__).resolve().parent / "prompts" / "improve_perf_area.md"
)

# --- Workload thread / timeout maps (verilator) ----------------------------

# Threads per benchmark. Verilator fixes its thread count at compile time, so
# each distinct value here costs one more build (~380 s) in
# build_all_thread_variants -- which is why only the long tail is listed.
#
# A round's simulation ends when its slowest benchmark does, and with 32 slots
# for 19 benchmarks the rest of the pool sits idle waiting. Measured on v9:
# synthesis + STA finished in 963 s while the last benchmark ran on past an
# hour. The eight below are every benchmark over 2.3 M ROI cycles; the
# remaining eleven are 1.9 M and under and finish well inside the tail, so
# threading them would buy nothing and only widen the wakeup overhead.
#
# 4, not more: verilator's threads synchronise every cycle, so the speedup is
# sub-linear (~2-2.5x at 4) and 8 would cost more in slots than it returns.
EMBENCH_WORKLOADS_THREAD_MAP = {
    # > 2.3 M ROI cycles -- the tail that sets simulation wall time.
    "nsichneu":       4,   # 3.42 M
    "ud":             4,   # 2.79 M
    "qrduino":        4,   # 2.69 M
    "crc32":          4,   # 2.47 M
    "nettle-aes":     4,   # 2.40 M
    "sglib-combined": 4,   # 2.39 M
    "nettle-sha256":  4,   # 2.38 M
    "xgboost":        4,   # 2.32 M
    # The rest run 1-threaded.
    "huffbench":      1,   # 1.94 M
    "depthconv":      1,   # 1.81 M
    "slre":           1,   # 1.73 M
    "edn":            1,   # 1.72 M
    "statemate":      1,   # 1.68 M
    "picojpeg":       1,   # 1.66 M
    "md5sum":         1,   # 1.41 M
    "matmult-int":    1,   # 1.38 M
    "aha-mont64":     1,   # 1.36 M
    "wikisort":       1,   # 0.95 M
    "tarfind":        1,   # 0.75 M
}

# Per-benchmark cycle budgets, read by embench_isa_tests.py's load_embench and
# scaled there by EMBENCH_TIMEOUT_SCALE.
EMBENCH_TIMEOUT_CYCLES = {
    "default":         20_000_000,
    "edn":           2*1_822_000,
    "slre":          2*1_831_000,
    "statemate":     2*2_402_000,
    "matmult-int":   2*1_524_000,
    "md5sum":        2*1_788_000,
    "sglib-combined":2*4_187_000,
    "aha-mont64":    2*1_928_000,
    "tarfind":       2*1_481_000,
    "depthconv":     2*2_245_000,
    "ud":            2*4_700_000,
    "nettle-sha256": 2*2_568_000,
    "qrduino":       2*5_114_000,
    "picojpeg":      2*2_615_000,
    "nsichneu":      2*4_312_000,
    "nettle-aes":    2*2_585_000,
    "wikisort":      2*1_913_000,
    "huffbench":     2*3_416_000,
    "crc32":         2*4_905_000,
    "xgboost":       2*7_089_000,
}

# --- Reports ---------------------------------------------------------------

# Report keys inside a SynthesisResult.reports dict, as SUFFIXES rather than
# exact paths. hammer_syn_node._collect_reports keys Yosys' output as the
# "syn-rundir/<top>.synth_stat.txt" and boom_tile_syn_open.py re-keys
# OpenSTA's as "sta/<top>.sta.rpt", and <top> is the remapped BoomTile name,
# which is resolved at runtime rather than known here. Match on the tail and use
# resolve_report() below.
AREA_REPORT_SUFFIXES = (".synth_stat.txt",)
STA_REPORT_SUFFIXES = (".sta.rpt",)


def resolve_report(reports: dict[str, str], suffixes=AREA_REPORT_SUFFIXES) -> str:
    """First report whose key ends with one of *suffixes*, or "".

    Suffix matching rather than a dict lookup because the key embeds the
    synthesized top module's name.
    """
    for suffix in suffixes:
        for name, body in (reports or {}).items():
            if name.endswith(suffix) and body:
                return body
    return ""


# Where the parent branch's reports are staged for the LLM on the chipyard
# worker -- chipyard_bash reads/greps these through the BashTool. The timing
# flow staged one report; this one stages three, because the objective is a
# ratio under a constraint and the agent needs all three terms:
#   area  -- Yosys' per-module "Chip area for module" roll-up, the thing to
#            shrink and the only report that says WHERE the area is
#   sta   -- OpenSTA's setup paths, so fmax (a hard gate) is not traded away
#   ipc   -- per-benchmark IPC, so the agent can tell which structures the
#            sensitive benchmarks actually exercise
_LLM_REPORT_DIR = "/tmp/improve_perf_area"
AREA_REPORT_LLM_PATH = f"{_LLM_REPORT_DIR}/area_report.txt"
STA_REPORT_LLM_PATH = f"{_LLM_REPORT_DIR}/sta_report.rpt"
IPC_REPORT_LLM_PATH = f"{_LLM_REPORT_DIR}/ipc_report.md"

# Where the last few branches' OWN reports are staged, one directory per branch
# holding the same three files the parent gets. A hunk and a three-factor delta
# cannot say which paths a rejected edit actually broke; its STA report can.
HISTORY_REPORTS_LLM_DIR = f"{_LLM_REPORT_DIR}/history"

# How many branches back to stage. Each costs ~0.9 MB on the chipyard node.
HISTORY_REPORT_BRANCHES = 5

# Where PerfAreaExperimentTool stages per-experiment reports for the LLM. Lives
# on the same chipyard worker as chipyard_bash (same PG bundle), so the agent can
# grep <EXPERIMENT_REPORTS_LLM_DIR>/<exp_id>/... without crossing nodes.
EXPERIMENT_REPORTS_LLM_DIR = f"{_LLM_REPORT_DIR}/experiments"

# --- Storage ---------------------------------------------------------------

# SQLite-backed store for this flow. The DB is only touched on the head node, so
# an absolute head path is used everywhere it is read -- NOT Path(__file__),
# which under a ray working_dir upload resolves to /tmp/ray/.../_ray_pkg_*/ (the
# uploaded, empty copy), making has_any_branch() lie and re-fire seed_flow. Its
# its own directory, so no other flow's lineage ever shares this tree.
DB_DIR = os.environ.get(
    "PERF_AREA_EFF_DB_DIR",
    os.path.expanduser("~/perf_area_eff_DB"),
)

# Worker-local scratch directory where the remote synthesis task writes its
# Hammer/Yosys obj_dir. /scratch is local to each machine (not shared across the
# cluster). The Genus path tarred this up and returned the bytes; the open path
# returns its reports in memory instead, so this tree stays on the worker.
SYN_OBJ_SCRATCH_DIR = os.environ.get(
    "PERF_AREA_EFF_SYN_OBJ_SCRATCH_DIR", "/scratch/perf_area_eff")

# --- Synthesis collateral --------------------------------------------------

# CACTI, on the synthesis workers. Ships in the chia-cacti image this cluster's
# vlsi node runs, which is why it is under /scratch and not a conda prefix.
# run_cacti_macrocompiler_prep's own default is a redaction placeholder
# ("/path/to/cacti/cacti"), so this must be passed explicitly at every call
# site -- improve_perf_area.py's three run_cacti_macrocompiler_prep calls and
# perf_area_experiment_tool.py's cacti dispatch.
CACTI_PATH = os.environ.get("PERF_AREA_EFF_CACTI_PATH", "/scratch/cacti/cacti")

