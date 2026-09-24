# perf_area_eff_opt

LLM-in-the-loop (Claude or Codex) **performance-area efficiency** improvement for
the BOOM core: read a Yosys area report, an OpenSTA timing report and a
per-benchmark IPC table, edit Chisel to raise
`embench_speed_score / total_cell_area`, rebuild, re-synthesize, re-benchmark,
and record the result as a new branch in a tree of design variants.

Frequency needs no gate of its own: the Embench speed score is
`fmax x geomean(reference_cycles / our_cycles)`, so fmax is already a factor of
the objective.

Self-contained: depends only on the installed `chia` package and the sibling
`common/` and `sky130_vlsi/` helpers.

## The perf-area loop

The optimizer maintains a **multi-branch tree** of design variants in a
SQLite-backed store (`db.py`). Each branch records a diff against the base
RTL, the generated Verilog, the Yosys area report, the OpenSTA timing report,
the per-benchmark ROI counters, the riscv-test results, and logs. User picks a
**parent** branch to optimize each turn; the flow produces one **child** branch
per invocation.

`run_perf_area_loop()` runs this 8-step pipeline (`improve_perf_area.py`):

1. **Load inputs** — pull the parent branch's BoomTile module name, generated
   Verilog, area report, timing report and per-test results from the DB.
2. **Acquire a chipyard placement group** + a `chipyard_bash` tool the LLM
   drives. Also spawn the head-pinned `ExperimentLogger` actor and the LLM's
   `perf_area_experiment` MCP tool (see below).
3. **Reset + stage** — reset chipyard + submodules to their recorded commits,
   re-apply the parent's diff so the tree reproduces the parent exactly, then
   write the parent's generated Verilog to the chipyard node.
4. **LLM `improve_perf_area`** — stage the parent's area report, timing report
   and IPC table on the chipyard node (they are too large to inline in the
   prompt), build the prompt (`prompts/improve_perf_area.md`), and call the LLM
   selected with `--llm` (Claude or Codex). The LLM greps the reports with
   `chipyard_bash`, edits Chisel, and validates candidate edits with fast
   sub-block syntheses via the `perf_area_experiment` tool. `--skip-llm` skips this step (ablation re-measurement on the parent
   diff unchanged).
5. **Build all thread variants** with an LLM build-debug retry loop
   (`common.build.build_all_thread_variants` → `build_with_debug_retry` →
   `llm_backend.LLMDebugger`), with `ENABLE_YOSYS_FLOW=1` so Yosys can
   read the generated Verilog. Every benchmark runs 1-threaded, so this is a
   single `MediumBoomV3Config` build.
6. **Synthesis + verilator, in parallel, with recovery** — per attempt:
   - **prep**: CACTI SRAM characterization + MacroCompiler remap, then resolve
     the BoomTile module name (`common.common_nodes.run_cacti_macrocompiler_prep`),
     redone each attempt because debugger edits can change the Verilog.
   - **dispatch BoomTile synthesis + STA** (async, Yosys then OpenSTA on a VLSI
     worker) and **run the verilator suite** (19 embench + 239 riscv-tests,
     `common.verilator.dispatch_verilator_tests`) at the same time. The embench
     runs give the per-benchmark ROI cycle counts the speed score is built
     from; the riscv-tests are a **correctness gate**.
   - if a test fails that the parent passed: cancel the in-flight synth, run
     the LLM debugger (shared session across retries), rebuild, and loop
     (up to `--max-debug-retries`).
7. **Collect synthesis result** once verilator is clean.
8. **Persist** the child branch: synthesis reports, area, fmax, the embench
   speed score, `embench_speed_score_area_eff`, mean IPC, per-test results, the
   produced area and timing reports, and a summary with parent-vs-child
   efficiency and both gates (the objective not below the **parent's**, no new
   riscv-test failures against the **seed**).

On any failure the `finally` block reverts chipyard to the parent diff and
records the final status; success leaves the edits in place (already persisted).

### Seed flow

When the DB is empty there is no parent to optimize, so `main()` first runs
`seed_flow()`: reset to the **unmodified** base RTL (empty diff), build,
CACTI/MacroCompiler prep, synthesize + time BoomTile, run verilator for the
baseline cycle counts, and store it as the `baseline` branch — the first DB
entry, the root of the tree, and the reference the riscv-test gate measures
against. No LLM editing step.

## The `perf_area_experiment` tool

`PerfAreaExperimentTool` (`perf_area_experiment_tool.py`) is an MCP tool the LLM
calls during step 4 to A/B-test edits without paying for a full BoomTile
synthesis. A sub-block synthesis can take longer than an MCP HTTP round-trip —
so it uses a **start / poll** split:

- `rebuild_verilog()` — re-elaborate Chisel to Verilog (`make verilog`, no C++
  build) and cache the result.
- `list_modules()` / `list_modules_parent()` — list child / parent Verilog
  module names so the LLM knows the valid `vlsi_top` values.
- `start_synth_child(vlsi_top, …)` / `start_synth_parent(vlsi_top, …)` —
  dispatch a sub-block synth on the edited vs. unmodified RTL; return a handle
  in sub-seconds. Issue both for a parallel A/B comparison.
- `synth_status(handle, max_wait_seconds)` — poll an in-flight synth; returns
  `running` or the full area + fmax summary on completion.

Results are recorded in the `llm_experiments` table via the head-pinned
`ExperimentLogger` actor (the tool's worker can't see the head's DB).

## Running

`improve_perf_area.py` is the entry point. With an empty DB it seeds the
baseline, then optimizes from it:

    python examples/perf_area_eff_opt/improve_perf_area.py \
        --branch baseline \
        [--iteration 1] \
        [--max-debug-retries 3] \
        [--build-config MediumBoomV3Config] \
        [--output-suffix _area] \           # child = <parent><suffix>_v<N> (auto-increment)
        [--output-branch NAME] \            # override the computed child name
        [--prompt-file prompts/improve_perf_area.md] \
        [--llm claude] \                    # agent CLI: claude or codex (edit step + debugger)
        [--model MODEL] \                   # default claude-opus-5 (claude), gpt-6-astra (codex)
        [--effort xhigh] \                  # thinking level: claude low..max, codex minimal..xhigh
        [--skip-llm] \                      # ablation: apply parent diff, no LLM edit
        [--skip-verilator] \                # single build, no sim; frees the build node during synth
        [--no-experiment-tool] \            # LLM gets only chipyard_bash (no A/B sub-block synth)
        [--diff-file path/to/diff.json] \   # measure an external diff instead of the parent's
        [--synth-only] \                    # re-synth a branch's stored RTL → <branch>_synth_only
        [--seed-only] \                     # build + measure the baseline, then exit
        [--dry-run] \                       # print the parent's timing-report head, exit
        [--ray-address auto]

The optimization prompt is `prompts/improve_perf_area.md`.

### Modes

Besides the full LLM loop, `improve_perf_area.py` exposes a few non-LLM modes
used to run experiments and ablations:

- **`--skip-llm`** — apply the parent's diff (or `--diff-file`'s) unchanged and
  run build → verilator → synth. No optimizer LLM.
- **`--skip-verilator`** — build once (just to elaborate the RTL + collect
  Verilog), skip the verilator suite, and release the chipyard placement group
  right after dispatching synthesis, so the build node is free during
  synthesis. No cycle counts are recorded, so no
  `embench_speed_score_area_eff` either.
- **`--diff-file FILE`** — apply an external `diff.json` (the
  `{"": root, "generators/boom": …}` format `collect_diff` emits) instead of
  the parent's. The parent only supplies the staging generated_src and reports.
  Combine with `--skip-llm --skip-verilator` to synthesize a given diff as-is
  with no LLM and no sim.
- **`--no-experiment-tool`** — don't give the LLM the `perf_area_experiment` MCP
  tool; it gets only `chipyard_bash`.
- **`--synth-only --branch B`** — re-run CACTI + Yosys + OpenSTA on branch `B`'s
  stored generated_src (no rebuild, verilator, or LLM), writing `B_synth_only`.
  For re-measuring an existing branch when the area model changes.

Because Ray runs the driver from the head, the DB lives at an absolute head
path (`constants.DB_DIR`, override with the `PERF_AREA_EFF_DB_DIR` env var),
never a `Path(__file__)`-relative path (which would resolve into Ray's upload
dir and make the seed-detection lie).

### Run layout

The SQLite DB and its file tree live under `DB_DIR`:

    {DB_DIR}/
    ├── perf_area_eff.db              # branches / files / perf_results / llm_experiments
    └── files/<branch>/
        ├── logs/                     # timing.csv, improve_perf_area_prompt.md,
        │                             # improve_perf_area_llm.md, error_context_*.txt,
        │                             # debug_failure_*.md
        ├── improve_perf_area_log.md  # parent-vs-child metrics and gate results
        ├── diff.json                 # branch diff vs base RTL (root + per-submodule)
        ├── generated_src/            # generated Verilog
        ├── cacti_libs/               # CACTI SRAM Liberty files
        ├── area_report.txt           # produced Yosys area report
        ├── timing_report.rpt         # produced OpenSTA report
        ├── ipc_report.md             # parent's per-benchmark IPC table given to the LLM
        ├── synthesis_reports/        # per-run Yosys + OpenSTA reports
        ├── area_estimates.json, synthesis_log.md
        ├── perf.json, perf_results.md       # per-benchmark ROI counters
        ├── riscv_tests.json, riscv_tests_failures/
        └── experiments/<id>/         # sub-block synths run by the LLM

### Reporting

`scripts/perf_table.py` reads the DB and prints a per-branch table of area,
fmax, mean IPC, the embench speed score and `embench_speed_score_area_eff`, with
the efficiency change vs each branch's parent and vs the baseline:

    python examples/perf_area_eff_opt/scripts/perf_table.py \
        [--db {DB_DIR}/perf_area_eff.db] [--baseline baseline] [--all]

## DB schema (`db.py`)

| table | purpose |
|-------|---------|
| `branches` | the variant tree: `name`, `parent_id`, `is_seed`, `iteration`, `status`, `boom_tile_module`, `area`, `sram_macro_area`, `std_cell_area`, `fmax_mhz`, `worst_slack_ns/_met/_line`, `mean_ipc`, `embench_speed_score`, `embench_speed_score_per_mhz`, `embench_speed_score_area_eff`, `ipc_area_eff`, `embench_tests`, `riscv_tests_passed/_total`, `gates_passed`, `synthesis_success`, `verilator_passed/_failed`, `files_dir` |
| `files` | registered on-disk artifacts per branch, keyed by `role` (`diff`, `generated_src`, `area_report`, `timing_report`, `synthesis_reports`, `log`, …) and `kind` (`file`/`dir`) |
| `perf_results` | per-test `passed` + `counters_json` (ROI counters) |
| `llm_experiments` | sub-block synths the LLM ran via `perf_area_experiment`: `vlsi_top`, `status`, `area`, `sram_macro_area`, `fmax_mhz`, `worst_slack_*`, `elapsed_seconds`, `files_dir` |

## Prerequisites

> **Before running, fill in every operator-specific value** the example ships
> with — the Tailscale auth key, the GCP project and SSH key, and the editable
> `chia` checkout. See [Paths to fill in](#paths-to-fill-in) for the complete
> checklist.

- **Ray cluster** with `chipyard`, `verilator_run`, `VLSI`/`Syn`/`cacti`, and
  `llm`/`codex_creds`/`claude_creds` resources. `perf_area_eff_cluster.yaml` is
  a reference topology (GCP workers joined over Tailscale, with the head and the
  LLM worker on the local machine); `env.yml` is the conda env.
- **Synthesis collateral** on the VLSI worker: CACTI (`constants.CACTI_PATH`)
  and OpenSTA ship in the `chia-cacti` image; Yosys and the open sky130 PDK are
  installed by the cluster YAML's `worker_setup_commands`.
- **Test binaries** under the `examples/benchmarks` submodule
  (`embench/build/`, `riscv-tests/isa/build/`), built on the head.
  `dramsim_ini/` ships alongside for the verilator runs.
- **`LLM_ENV`** (`constants.LLM_ENV`) is just the working directory the LLM
  CLI runs in; the cluster setup creates it empty. **Nothing needs to live
  there** — all prompts are sent inline: the `improve_perf_area` prompt is read
  from `prompts/improve_perf_area.md` and pre-expanded on the head node, and the
  build/verilator debugger prompt is read from `prompts/debugging.md` and passed
  inline to `llm_backend.LLMDebugger` (its required-reading references,
  `common_debugging.md` + `chisel_debugging.md`, ride along as `aux_files`, get
  written to a per-call `{AUX_DIR}` temp dir on the LLM machine, and are deleted
  after the call).

## Setup: environment-specific config

Machine-/site-specific values are read from environment variables (with
reference-cluster defaults) so the example is reusable without editing code.

### Paths to fill in

| File | Stub | Replace with |
|------|------|--------------|
| `auth/tailscale_key` | empty | a reusable, pre-authorized Tailscale auth key (`tskey-auth-…`). Do not commit the filled file. |
| `env.sh` (repo root) | `GCP_PROJECT=gcp_project_name`, `GCP_SSH_KEY=/path/to/ssh_key` | your GCP project, and the SSH private key whose `.pub` is injected into the VMs. `HEAD_IP` (this machine's first address) and `TS_AUTHKEY` (read from `auth/tailscale_key`) need no edit. |
| `examples/perf_area_eff_opt/env.yml` | `- -e /path/to/chia` | path to your editable `chia` checkout (pip `-e` install in the conda env) |

For the tailscale auth key at auth/tailscale_key, they can be generated at
https://console.tailscale.com/admin/settings/keys. Also, you can reference examples/tailscale
to know more about how to run a CHIA cluster whose machines can only reach each other through
a [tailscale](https://tailscale.com) network.

**`constants.py` env vars** (pass via `chia job submit --runtime-env-json`, as in
[Launching runs end-to-end](#launching-runs-end-to-end) — not a shell `export`):

| Env var | Default | What it is |
|---------|---------|------------|
| `PERF_AREA_EFF_DB_DIR` | `~/perf_area_eff_DB` | SQLite store + file tree. **Must** be a stable absolute head path (never under Ray's working-dir upload). |
| `PERF_AREA_EFF_CHIPYARD_PATH` | `/home/ray/chipyard/` | chipyard checkout inside the chisel-build image |
| `PERF_AREA_EFF_LLM_ENV` | `/home/ray/llm_env` | LLM working dir (created empty by the cluster setup) inside the LLM image |
| `PERF_AREA_EFF_SYN_OBJ_SCRATCH_DIR` | `/scratch/perf_area_eff` | worker-local scratch for the synthesis obj_dir |
| `PERF_AREA_EFF_CACTI_PATH` | `/scratch/cacti/cacti` | CACTI binary on the synth worker |

**`perf_area_eff_cluster.yaml`** carries operator-specific values to set before
`chia up`:

- `${HEAD_IP}`, `${TS_AUTHKEY}`, `${GCP_PROJECT}`, `${GCP_SSH_KEY}` — expanded
  from `env.sh`.
- GCP API access uses Application Default Credentials on the local machine:
  `gcloud auth application-default login` and
  `gcloud auth application-default set-quota-project $GCP_PROJECT`.
- The LLM worker mounts `~/chia_codex_home` as its `~/.codex` and
  `~/chia_claude_home` as its `~/.claude`: copy `auth.json`, `config.toml` and
  `installation_id` from `~/.codex` into the first and
  `~/.claude/.credentials.json` into the second. Only the backend you run with
  needs credentials.
```bash
mkdir -p ~/chia_codex_home && cp ~/.codex/auth.json \
    ~/.codex/config.toml ~/.codex/installation_id ~/chia_codex_home/

mkdir -p ~/chia_claude_home && cp ~/.claude/.credentials.json ~/chia_claude_home/
```

## Launching runs end-to-end

Once every value from [Paths to fill in](#paths-to-fill-in) is set, bring the
flow up with the steps below, driven through the **`chia` CLI** (`chia up` /
`chia job submit` / `chia down`). Commands run from the repo root.

**1. Fetch and build the embench and riscv-tests.** The suite reads `embench/build/` and
`riscv-tests/isa/build/` under `examples/benchmarks/` (a git submodule — see
[Prerequisites](#prerequisites)); `--remote` checks out the latest commit of the
benchmarks repo, then build them as following descriptions:
```bash
# checkout benchmarks at f45a126
git submodule update --init --recursive --remote examples/benchmarks

cd examples/benchmarks/
conda env create -f env.yml && conda activate benchmarks-build

# checkout riscv-tests at 0494f95, so riscv-tests/benchmarks/common/crt.S defines tohost and fromhost,
# in the latest commit (2ebecad), tohost/fomhost definitions are removed.
git submodule update --init --recursive

# fix main() not declared first at baremetal_init.c to prevent gcc error
git apply ../perf_area_eff_opt/embench_fix/embench_fix.patch

# build embench to embench/build/<name>.riscv
cd embench
make

# build rv64gc riscv-tests to isa/build/<name>.riscv
cd ../riscv-tests
mkdir -p isa/build
make -C isa/build -f $PWD/isa/Makefile src_dir=$PWD/isa -j8 \
    rv64ui rv64uc rv64um rv64ua rv64uf rv64ud rv64si rv64mi

# The riscv-tests Makefile hardcodes the unsuffixed names; to give the binaries a .riscv suffix, rename after building:
for f in isa/build/rv64*; do
    case "$f" in *.dump|*.riscv) ;; *) mv "$f" "$f.riscv" ;; esac
done

# return to perf_are_eff_loop env and repo root
conda deactivate
cd ../../../
```
**2. Create + activate the head conda env.** Only the head needs it — workers get
`chia` via Ray `py_modules` and the cluster images. The env is named
`perf_area_eff_loop` (in `env.yml`):
```bash
conda env create -f examples/perf_area_eff_opt/env.yml
conda activate perf_area_eff_loop
```

**3. Bring up the cluster.**
`chia up` expands `${HEAD_IP}`, `${TS_AUTHKEY}`, `${GCP_PROJECT}` and `${GCP_SSH_KEY}` from `env.sh`:
```bash
source env.sh
chia up examples/perf_area_eff_opt/perf_area_eff_cluster.yaml
```
The first bring-up is slow — it pulls the large chipyard/verilator images.
Confirm all four workers (1 `verilator_run` + 1 `chisel_build` + 1 `llm` +
1 `vlsi`) are up in the dashboard before submitting.

**4. Seed the baseline.** With an empty DB the flow builds, synthesizes and
benchmarks the **unmodified** RTL and stores it as the `baseline` branch (the
tree root). Pass any non-default `PERF_AREA_EFF_*` values via
`--runtime-env-json`, **not** a shell `export`: the `chia job submit` entrypoint
runs under Ray's job manager and does *not* inherit your shell's env. Run from
the repo root so `--working-dir .` uploads the checkout (from the example dir
the upload collides with the package's own `py_modules` entry, and workers
cannot import it):
```bash
chia job submit --working-dir . \
  --runtime-env-json '{"env_vars": {"PERF_AREA_EFF_DB_DIR": "/abs/path/on/head/perf_area_eff_DB"}}' \
  -- python examples/perf_area_eff_opt/improve_perf_area.py --seed-only
```
Include only the vars you're overriding.

**5. Run a perf-area optimization iteration.** Once the baseline exists, choose a
parent branch to optimize; each invocation produces one child branch named
`<parent>_area_v<N>` (auto-incremented). Reuse the **same** `--runtime-env-json`
block on every submit so the DB path stays consistent:
```bash
chia job submit --working-dir . \
  --runtime-env-json '{"env_vars": {"PERF_AREA_EFF_DB_DIR": "/abs/path/on/head/perf_area_eff_DB"}}' \
  -- python examples/perf_area_eff_opt/improve_perf_area.py --branch baseline
```
Optimize a child instead by passing its name (e.g. `--branch baseline_area_v1`).
Re-running the same `--branch` reuses the same child name, so pass
`--output-branch NAME` to grow the tree wider with another sibling. The
[Running](#running) section lists the full flag set (`--skip-llm`,
`--skip-verilator`, `--diff-file`, `--no-experiment-tool`, `--llm`, `--model`, `--effort`,
`--prompt-file`, …) — the same flags apply here.

> You can skip step 4 and run step 5 directly: with an empty DB the loop
> auto-seeds the baseline first, then optimizes it in the same job. Submitting via
> `chia job submit` makes the driver logs show up in the dashboard at
> `http://127.0.0.1:8265` on the head.

**6. Inspect results** with the reporting script (reads the head-local DB):
```bash
python examples/perf_area_eff_opt/scripts/perf_table.py \
  --db /abs/path/on/head/perf_area_eff_DB/perf_area_eff.db
```

**7. Tear down** when finished. Use `--no-scoped`:
```bash
chia down --no-scoped examples/perf_area_eff_opt/perf_area_eff_cluster.yaml
```
The GCP workers go with their VMs either way, but `llm_1` runs here and the
default scoped teardown often leaves its container behind. The next `chia up`
reuses it with stale credential mounts, and Step 4 fails with `llm_failed`
(`Not logged in`) after the build is already done. To recover from that:
`docker rm -f chia-llm-$USER-0`, then `chia up`.
