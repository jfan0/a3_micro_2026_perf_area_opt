"""Performance-area efficiency example: multi-branch BoomTile optimization.

An LLM-in-the-loop flow that reads a design's area, timing and IPC reports, edits
Chisel to improve ``embench_speed_score / total_cell_area``, rebuilds,
re-measures, and records each child branch in a SQLite-backed tree (see
``db.py``). A ratio objective under two hard gates: it must not regress on the
parent, and no riscv-test that passes on the seed may start failing. Toolchain is
all open source. Self-contained: depends only on the installed ``chia`` package
and the sibling ``common`` helpers.

  * ``constants``        — constants.py: paths, build config, the LLM model,
                           report suffixes/staging paths, DB + scratch dirs.
  * ``common_constants`` — Ray runtime-env for standalone-script ``ray.init``.
  * ``improve_perf_area``— improve_perf_area.py: the per-branch loop
                           (load → diff → LLM edit → build → CACTI/MC prep →
                           parallel synth+STA and simulation → debug retry →
                           gate → persist) plus ``seed_flow``, the objective
                           (``embench_speed_score_area_eff``), the gate check
                           (``evaluate_gates``) and the ``ExperimentLogger``
                           actor.
  * ``perf_area_experiment_tool`` — the MCP tool that lets the agent start/poll
                           fast sub-block Yosys+OpenSTA runs to A/B test an edit,
                           reporting area *and* fmax per side.
  * ``boom_tile_syn_open`` — boom_tile_syn_open.py: ``synthesize_and_time``
                           (Yosys area + OpenSTA fmax in one dispatch), the
                           sky130/CACTI collateral paths, and
                           ``_save_variant_results``, which writes a run's
                           reports into a branch's files dir.
  * ``embench_isa_tests`` — embench_isa_tests.py: embench/riscv-tests loaders,
                           ROI counter parsing (``parse_roi``) and the result
                           writers, so every branch's files dir comes out in
                           the same shape and two branches are diffable.
  * ``llm_backend``      — the agent LLM (Claude or Codex, picked with ``--llm``)
                           for the edit step, and the build/simulation debugger
                           standing in for ``common.common_nodes.debug_failure``
                           (which is hardcoded to Claude).
  * ``db``               — db.py: SQLite ``PerfAreaEffDB`` (branch tree, files,
                           perf_results, llm_experiments) + ``parse_worst_slack``.

The shared infrastructure this package reuses from ``common``:
  * ``common.common_nodes``   — collect_diff, reset_and_apply_diff, the
                             generated-Verilog parsing / hierarchy helpers,
                             CACTI / MacroCompiler task nodes +
                             ``run_cacti_macrocompiler_prep``, area parsing.
  * ``common.build``       — build_with_debug_retry / build_all_thread_variants.
  * ``common.verilator``   — run_verilator_test / dispatch_verilator_tests.
  * ``common.common_helpers`` — format_test_error, load_test_binaries.
"""
