"""LLM-invokable synthesis-experiment tool for the perf-area efficiency flow.

A result reports **area and fmax per side**: a sub-block A/B is only actionable
if it says what the edit did to both terms the objective prices.

Exposes six MCP methods the agent can call during the optimization step:

  - ``rebuild_verilog()``                      — re-elaborate Chisel into Verilog
    via Chipyard's ``make verilog`` (no Verilator C++ compile).
  - ``list_modules()``                         — list the *child* Verilog module
    names so the LLM knows what ``vlsi_top`` values are available.
  - ``list_modules_parent()``                  — list the *parent* branch's
    module names, available without ``rebuild_verilog()``. Useful in Phase 1
    to ground the mental model and to detect structural drift between parent
    and child (renames, splits, new modules).
  - ``start_synth_child(vlsi_top, ...)``       — dispatch a sub-block synthesis
    + STA on the LLM-edited (child) RTL. **Async**: returns a short handle
    string immediately; the heavy run happens in a background Ray task.
  - ``start_synth_parent(vlsi_top, ...)``      — same, but on the parent
    branch's *unmodified* RTL. Issue together with ``start_synth_child`` as
    parallel MCP tool calls for the A/B comparison; both runs proceed
    concurrently on the VLSI worker (capacity permitting).
  - ``synth_status(handle, max_wait_seconds)`` — check on an in-flight run.
    Returns ``status: running`` (with elapsed_seconds) or the full summary
    on completion, including area, sram_macro_area and fmax_mhz.
    ``max_wait_seconds`` lets the agent block opportunistically; keep it under
    ~200 so the MCP HTTP round-trip stays inside the session timeout.

This start / poll split is deliberate: a run can outlast the MCP HTTP timeout.
By returning a handle in sub-seconds and letting the agent poll, we get
arbitrary synth durations without disconnects.

The tool actor lives on the **head node** (pinned via
``NodeAffinitySchedulingStrategy``), and so does the ``_experiment_orchestrator``
task, so that child tasks are head-submitted -- this avoids the cross-worker
lease storm hit when the orchestrator ran without affinity.

**Bulk data never goes through the head**, though. On this cluster the head is
the operator's machine, reaching the GCP workers over a slow, high-latency
tailnet link, while worker-to-worker traffic goes directly between the VMs.
See "Sub-block A/B data path" below for how each side's RTL, the CACTI
Liberty files and the reports move. Results are recorded in the SQLite DB via
the head-node ``ExperimentLogger`` actor (passed in by name).
"""

from __future__ import annotations

import hashlib
import os
import pickle
import shutil
import subprocess
import time
import uuid
import zlib
from pathlib import Path
from typing import Optional

import ray
from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

from chia.base.ChiaFunction import ChiaFunction, get
from chia.base.tools.BashTool import BashTool
from chia.base.tools.ChiaTool import ChiaTool

from common.common_nodes import (
    _build_children_map,
    _get_all_descendants,
    _parse_verilog_modules,
    parse_area_from_reports,
    run_macrocompiler_remap,
)
from perf_area_eff_opt.boom_tile_syn_open import (
    CLOCK_PERIOD_NS,
    STA_CORNER,
    _drop_behavioral_sources,
    _sram_macro_area,
    synthesize_and_time,
)
from perf_area_eff_opt.constants import (
    AREA_REPORT_SUFFIXES,
    CACTI_PATH,
    EXPERIMENT_REPORTS_LLM_DIR,
    STA_REPORT_SUFFIXES,
    SYN_OBJ_SCRATCH_DIR,
)


# ---------------------------------------------------------------------------
# Sub-block A/B data path
#
# The head reaches the GCP workers over a ~1.3 MB/s, ~300 ms RTT tailnet link,
# and Ray's object manager copes badly with it: it pushes several 5 MB chunks
# in parallel, they time out and are re-pushed. The first version of this tool
# routed everything through the head -- the whole ~29 MB RTL to CACTI and back,
# the Liberty files back and out again, the child RTL from chipyard -- about
# 70 MB per side, and in the trial iteration each synthesis task waited 17-37
# min for its arguments to arrive against 30-100 s of Yosys.
#
# Worker-to-worker traffic goes directly between the VMs, so bulk data now
# never touches the head:
#
#   chipyard  _ab_read_mems_conf   RTL stays on disk: the child is snapshotted by
#                                  rebuild_verilog, the parent is Step 3's
#                                  staging. Only the .top.mems.conf (KB) moves.
#   vlsi      _ab_cacti_cached     CACTI on that conf; Liberty cached on the VLSI
#                                  node's disk, keyed by the conf's content, so
#                                  repeat calls skip CACTI. Returns macro names.
#   chipyard  _ab_bundle           MacroCompiler remap + vlsi_top closure filter,
#                                  compressed. The head only holds the ref.
#   vlsi      _ab_synth            pulls the bundle from chipyard, loads the
#                                  cached Liberty, runs Yosys + OpenSTA locally.
#
# Only metrics and compressed reports come back to the head.
# ---------------------------------------------------------------------------

_AB_CHILD_SRC_DIR = os.path.join(
    os.path.dirname(EXPERIMENT_REPORTS_LLM_DIR), "ab_src", "child")
_CACTI_CACHE_DIR = os.path.join(SYN_OBJ_SCRATCH_DIR, "cacti_cache")


def _pack(obj) -> bytes:
    return zlib.compress(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL), 6)


def _unpack(blob: bytes):
    return pickle.loads(zlib.decompress(blob))


def _read_src_dir(src_dir: str) -> list[tuple[str, str]]:
    """``(relative_path, contents)`` for every file under *src_dir*."""
    root = Path(src_dir)
    return [(p.relative_to(root).as_posix(), p.read_text(errors="replace"))
            for p in sorted(root.rglob("*")) if p.is_file()]


def _require_src_dir(src_dir: str, side: str) -> None:
    if not os.path.isdir(src_dir) or not any(Path(src_dir).iterdir()):
        what = ("call rebuild_verilog() first" if side == "child" else
                "the loop stages it in Step 3; it may have been removed since")
        raise FileNotFoundError(f"{side} RTL not found at {src_dir} ({what})")


@ChiaFunction(resources={"chipyard": 1.0})
def _ab_read_mems_conf(src_dir: str, side: str) -> tuple[str | None, str | None]:
    """``(name, contents)`` of the side's ``.top.mems.conf``, or ``(None, None)``."""
    _require_src_dir(src_dir, side)
    for p in sorted(Path(src_dir).glob("*.top.mems.conf")):
        return p.name, p.read_text()
    return None, None


@ChiaFunction(resources={"cacti": 1})
def _ab_cacti_cached(mems_conf_name: str, mems_conf: str, cacti_path: str) -> dict:
    """CACTI-characterize one ``.top.mems.conf``, caching the Liberty on this node.

    CACTI reads nothing but the conf (its generated-source argument is passed
    through untouched), so that is all it is sent. The Liberty files stay here,
    in ``_CACTI_CACHE_DIR/<key>``, for ``_ab_synth`` -- which the orchestrator pins
    to the node id returned here. An edit that leaves the SRAMs alone has the same
    conf, so after the first call per side this is a cache hit.
    """
    from chia.vlsi.sram_cacti.sram_characterize import (
        characterize_top_mems_conf_with_cacti,
    )
    key = hashlib.sha256(f"{cacti_path}\0{mems_conf}".encode()).hexdigest()[:16]
    blob = Path(_CACTI_CACHE_DIR) / key / "cacti.pkl.z"
    node_id = ray.get_runtime_context().get_node_id()
    if blob.is_file():
        names = _unpack(blob.read_bytes())["names"]
        return {"key": key, "names": names, "node_id": node_id, "cached": True}
    # A direct call runs in this process: no second task, no transfer.
    char = characterize_top_mems_conf_with_cacti([(mems_conf_name, mems_conf)], cacti_path)
    blob.parent.mkdir(parents=True, exist_ok=True)
    tmp = blob.with_name(f"{blob.name}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_bytes(_pack({"libs": char.sram_libs, "names": list(char.sram_names)}))
    os.replace(tmp, blob)  # atomic: two sides racing on one conf both land a whole file
    return {"key": key, "names": list(char.sram_names), "node_id": node_id, "cached": False}


@ChiaFunction(resources={"chipyard": 1.0})
def _ab_bundle(
    src_dir: str, side: str, vlsi_top: str, cacti_names: list[str], chipyard_path: str,
) -> bytes:
    """Build the ``_pack``-ed synthesis input for *vlsi_top* from the side's RTL.

    Mirrors ``common_nodes.run_cacti_macrocompiler_prep`` plus the closure filter
    the orchestrator used to apply, but next to the RTL: MacroCompiler remaps the
    CACTI-characterized SRAMs, and only files touching *vlsi_top*'s module closure
    are kept. Returns ``{"status": "ok", "files", ...}`` or
    ``{"status": "vlsi_top_not_found", "close"}``.
    """
    from chia.chipyard.macrocompiler import generate_macro_stubs
    from chia.vlsi.sram_cacti.cacti_runner import parse_mems_conf
    from chia.vlsi.sram_cacti.sram_characterize import (
        assemble_generated_src_with_cacti,
        generate_cacti_macrocompiler_lib,
    )
    _require_src_dir(src_dir, side)
    gen_src = _read_src_dir(src_dir)
    mems_conf = next((c for n, c in gen_src if n.endswith(".top.mems.conf")), None)
    if mems_conf and cacti_names:
        # Only CACTI-characterized SRAMs become cacti_ macros; the rest are forced
        # to flop arrays (see run_cacti_macrocompiler_prep for why).
        characterized = set(cacti_names)
        all_specs = parse_mems_conf(mems_conf)
        specs = [s for s in all_specs if s.name in characterized]
        synflops = [s.name for s in all_specs if s.name not in characterized]
        remapped_v = run_macrocompiler_remap(
            mems_conf, generate_cacti_macrocompiler_lib(specs), chipyard_path, synflops,
        )
        if remapped_v:
            gen_src = assemble_generated_src_with_cacti(
                gen_src, remapped_v, generate_macro_stubs(specs, "cacti_"),
            )
        else:
            print(f"  [experiment:{side}] MacroCompiler remap returned None -- synflops")

    modules = _parse_verilog_modules(gen_src)
    if vlsi_top not in modules:
        close = sorted(n for n in modules if vlsi_top.lower() in n.lower())[:8]
        return _pack({"status": "vlsi_top_not_found", "close": close})
    keep = {vlsi_top} | _get_all_descendants(
        vlsi_top, _build_children_map(modules, set(modules)))
    filtered = [
        (fname, content) for fname, content in gen_src
        if any(m in content for m in keep) or fname.endswith(".top.mems.conf")
    ]
    print(f"  [experiment:{side}] vlsi_top={vlsi_top}: {len(keep)} modules in "
          f"closure, {len(filtered)}/{len(gen_src)} files to synth")
    return _pack({"status": "ok", "files": _drop_behavioral_sources(filtered),
                  "modules_in_closure": len(keep)})


@ChiaFunction(resources={"VLSI": 1, "Syn": 0})
def _ab_synth(
    bundle: bytes, vlsi_top: str, cacti_key: str | None, obj_dir: str,
    clock_period_ns: float, timeout_seconds: int,
) -> bytes:
    """Run Yosys + OpenSTA on a ``_ab_bundle`` with the node-local CACTI Liberty.

    *bundle* is passed as an ObjectRef, so Ray resolves it here by pulling it
    from the chipyard node. Calls ``synthesize_and_time`` directly (in this
    process, under the same ``VLSI`` resource it declares) and returns the
    ``_pack``-ed result, reports included.
    """
    b = _unpack(bundle)
    if b["status"] != "ok":
        return _pack(b)
    libs = None
    if cacti_key:
        libs = _unpack((Path(_CACTI_CACHE_DIR) / cacti_key / "cacti.pkl.z")
                       .read_bytes())["libs"]
    t0 = time.time()
    syn, timing = synthesize_and_time(
        b["files"], vlsi_top, obj_dir=obj_dir, cacti_sram_libs=libs,
        clock_period_ns=clock_period_ns, timeout_seconds=timeout_seconds,
    )
    return _pack({"status": "ran", "syn": syn, "timing": timing,
                  "synth_seconds": time.time() - t0,
                  "modules_in_closure": b["modules_in_closure"]})


@ChiaFunction(resources={"chipyard": 1.0})
def _rebuild_verilog_remote(
    chipyard_path: str,
    build_config: str,
    make_timeout: int,
) -> tuple[str, list[str] | None]:
    """Run Chipyard's ``make verilog`` on the chipyard worker.

    Pinned to the chipyard PG via the ``chipyard`` resource so it lands
    on the worker that has the chipyard tree (and shares /tmp with
    ``chipyard_bash``). On success, snapshots gen-collateral/ +
    ``.top.mems.conf`` into ``_AB_CHILD_SRC_DIR`` -- so a later edit or ``make``
    does not change what ``start_synth_child`` measures until the next rebuild --
    and returns ``(summary_string, module_names)``. The RTL itself stays on this
    node. On failure returns ``(error_string, None)`` so the actor's
    ``rebuild_verilog`` method can update its cached state only when the result
    is good.
    """
    t0 = time.time()
    verilator_dir = os.path.join(chipyard_path, "sims/verilator")
    # ENABLE_YOSYS_FLOW=1 so the child is lowered exactly like the parent the A/B
    # compares it against (the loop's build passes it too); without it firtool
    # emits packed arrays Yosys cannot read. The flag only reaches firtool through
    # .mfc_lowering_options, whose make rule has no prerequisites: once an
    # unflagged make has written it, the flag is silently ignored until the file
    # goes. So drop any copy that lacks the Yosys option.
    cmd = ["make", "verilog", f"CONFIG={build_config}", "ENABLE_YOSYS_FLOW=1"]
    gen_src_dir = Path(verilator_dir) / "generated-src"
    for opts in gen_src_dir.glob(f"*.{build_config}/.mfc_lowering_options"):
        if "disallowPackedArrays" not in opts.read_text():
            opts.unlink()
    try:
        result = subprocess.run(
            cmd, cwd=verilator_dir, capture_output=True, text=True,
            timeout=make_timeout,
        )
    except subprocess.TimeoutExpired:
        return (
            f"make verilog TIMED OUT after {make_timeout}s. "
            f"Inspect with chipyard_bash in {verilator_dir}.",
            None,
        )
    elapsed = time.time() - t0
    if result.returncode != 0:
        return (
            f"make verilog FAILED (rc={result.returncode}, {elapsed:.1f}s)\n"
            f"command: {' '.join(cmd)}\n"
            f"cwd: {verilator_dir}\n"
            f"stderr (last 4000 chars):\n{result.stderr[-4000:]}",
            None,
        )
    # Collect generated_src files
    gen_src_root = Path(chipyard_path) / "sims/verilator/generated-src"
    candidates = [
        p for p in gen_src_root.glob(f"*{build_config}*")
        if (p / "gen-collateral").is_dir()
    ]
    if not candidates:
        return (
            f"make verilog OK ({elapsed:.1f}s) but no gen-collateral/ dir "
            f"under {gen_src_root} matched '*{build_config}*'",
            None,
        )
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    cfg_dir = candidates[0]
    # Same layout as the parent's staged generated_src: gen-collateral paths
    # relative to that directory, with the .top.mems.conf at the top level.
    tmp_dir = f"{_AB_CHILD_SRC_DIR}.{uuid.uuid4().hex[:8]}.tmp"
    shutil.copytree(cfg_dir / "gen-collateral", tmp_dir)
    for mc in cfg_dir.glob("*.top.mems.conf"):
        shutil.copy2(mc, os.path.join(tmp_dir, mc.name))
    shutil.rmtree(_AB_CHILD_SRC_DIR, ignore_errors=True)
    os.rename(tmp_dir, _AB_CHILD_SRC_DIR)
    files = _read_src_dir(_AB_CHILD_SRC_DIR)
    summary = (
        f"make verilog OK in {elapsed:.1f}s: collected {len(files)} files. "
        f"Call list_modules() for available vlsi_top names, then "
        f"start_synth_child(vlsi_top=..., timeout_seconds=...) to test a sub-block."
    )
    return summary, sorted(_parse_verilog_modules(files))


@ChiaFunction(resources={"chipyard": 1.0})
def _stage_experiment_reports_remote(
    exp_id: Optional[int],
    reports_packed: bytes,
) -> str:
    """Pinned to the chipyard PG so the files land where ``chipyard_bash``
    will read them. The actor (head-pinned) calls this each time a synth
    completes, via ``_stage_experiment_reports_remote.options(**pg_opts).chia_remote(...)``.
    The reports arrive ``_pack``-ed: text compresses ~10x, and this is one of the
    few payloads that still has to cross the head's link.
    """
    exp_tag = str(exp_id) if exp_id is not None else f"unknown_{uuid.uuid4().hex[:8]}"
    local_dir = os.path.join(EXPERIMENT_REPORTS_LLM_DIR, exp_tag)
    try:
        os.makedirs(local_dir, exist_ok=True)
        for relpath, text in (_unpack(reports_packed) or {}).items():
            if not text:
                continue
            basename = relpath.rsplit("/", 1)[-1]
            with open(os.path.join(local_dir, basename), "w") as f:
                f.write(text)
    except Exception as e:
        print(f"  [experiment] stage to {local_dir} failed: {e}")
    return local_dir


@ChiaFunction(num_cpus=0)
def _experiment_orchestrator(
    side: str,
    src_dir: str,
    vlsi_top: str,
    timeout_seconds: int,
    pg_opts: dict,
    logger_actor_name: str,
    chipyard_path: str,
) -> dict:
    """Background Ray task that runs a single sub-block synth experiment end-to-end.

    Chains the four tasks described under "Sub-block A/B data path", records the
    outcome to the head-side ``ExperimentLogger`` actor, and returns a dict with
    every field ``PerfAreaExperimentTool.synth_status`` needs -- including the
    raw ``reports`` dict, which the actor stages to /tmp on the chipyard worker
    for ``chipyard_bash`` to grep.

    It only ever handles small values: the ``.top.mems.conf``, macro names, and
    the finished result. The bundle goes from ``_ab_bundle`` to ``_ab_synth`` as
    an ObjectRef this task never fetches.

    Runs as a regular Ray task (not from inside an actor), which sidesteps a
    placement-group / runtime-env interaction we hit when CACTI was
    dispatched directly from the experiment-tool actor — those dispatches
    stayed PENDING_NODE_ASSIGNMENT forever. Submitting CACTI from inside
    this task (a free-scheduled Ray task) places normally.

    ``num_cpus=0`` because this is a thin orchestrator that mostly waits on
    other Ray tasks.
    """
    t_start = time.time()
    obj_dir = os.path.join(
        SYN_OBJ_SCRATCH_DIR, f"experiment_{uuid.uuid4().hex[:8]}", "syn_obj",
    )
    cacti = {"key": None, "names": [], "node_id": None, "cached": None}
    try:
        mems_name, mems_conf = get(
            _ab_read_mems_conf.options(**pg_opts).chia_remote(src_dir, side))
        if mems_conf:
            # DEFAULT so this escapes any enclosing placement group (see
            # run_cacti_macrocompiler_prep). CACTI_PATH explicitly: the
            # characterizer has no usable default.
            cacti = get(_ab_cacti_cached.options(scheduling_strategy="DEFAULT")
                        .chia_remote(mems_name, mems_conf, CACTI_PATH))
        print(f"  [experiment:{side}] CACTI: {len(cacti['names'])} macros "
              f"({'cached' if cacti['cached'] else 'characterized'}) "
              f"[{time.time() - t_start:.1f}s]")
        bundle_ref = _ab_bundle.options(**pg_opts).chia_remote(
            src_dir, side, vlsi_top, cacti["names"], chipyard_path)
        # The Liberty is on the node that characterized it.
        synth_strategy = (
            NodeAffinitySchedulingStrategy(node_id=cacti["node_id"], soft=False)
            if cacti["node_id"] else "DEFAULT")
        out = _unpack(get(_ab_synth.options(scheduling_strategy=synth_strategy)
                          .chia_remote(bundle_ref, vlsi_top, cacti["key"], obj_dir,
                                       CLOCK_PERIOD_NS, timeout_seconds)))
    except Exception as e:
        elapsed = time.time() - t_start
        logger = ray.get_actor(logger_actor_name)
        ray.get(logger.record.remote(
            vlsi_top=vlsi_top, status="synthesis_failed",
            syn_result=None, timing_result=None, elapsed_seconds=elapsed,
        ))
        return {
            "status": "synthesis_failed",
            "side": side,
            "vlsi_top": vlsi_top,
            "elapsed_seconds": elapsed,
            "error": str(e),
        }
    elapsed = time.time() - t_start

    if out["status"] == "vlsi_top_not_found":
        return {
            "status": "vlsi_top_not_found",
            "side": side,
            "vlsi_top": vlsi_top,
            "close": out["close"],
            "elapsed_seconds": elapsed,
        }
    syn_result, timing_result = out["syn"], out["timing"]

    area = parse_area_from_reports(syn_result.reports)
    sram_area = _sram_macro_area(syn_result.reports)
    status_str = "ok" if syn_result.success else "synthesis_failed"
    logger = ray.get_actor(logger_actor_name)
    record = ray.get(logger.record.remote(
        vlsi_top=vlsi_top, status=status_str,
        syn_result=syn_result, timing_result=timing_result,
        elapsed_seconds=elapsed,
    ))

    return {
        "status": status_str,
        "side": side,
        "vlsi_top": vlsi_top,
        "modules_in_closure": out["modules_in_closure"],
        # Both terms of the objective's constraint pair. area is what the edit
        # was probably trying to shrink; fmax is the gate it must not trip.
        "area": area,
        "sram_macro_area": sram_area,
        "std_cell_area": (None if area is None or sram_area is None
                          else area - sram_area),
        "fmax_mhz": None if timing_result is None else timing_result.fmax_mhz,
        "sta_success": None if timing_result is None else timing_result.success,
        "elapsed_seconds": elapsed,
        # Where the wall time went, so a slow A/B says whether it was the tools.
        "synth_seconds": out["synth_seconds"],
        "cacti_cached": cacti["cached"],
        "worst_slack_line": (record or {}).get("worst_slack_line"),
        "files_dir": (record or {}).get("files_dir"),
        "exp_id": (record or {}).get("exp_id"),
        # Raw reports — passed through Ray object store to the actor, which
        # writes them to /tmp on the chipyard worker for chipyard_bash to grep.
        "reports": syn_result.reports,
    }


# Unset in every agent command. On a worker these are what route Ray's gRPC
# through the tailnet relay (chia/cluster/node_setup.py _grpc_proxy_exports);
# without them the head's GCS is unreachable, so `ray.init(address="auto")` from
# the agent's shell fails instead of handing it every node in the cluster,
# including the operator's machine. RAY_ADDRESS is pinned to a dead local port
# so a bare ray.init() does not fall back to /tmp/ray/ray_current_cluster
# either. The last two make that attempt fail in seconds with ConnectionError:
# by default ray.init retries the GCS 20 times with a 30 s connect timeout and
# looks hung, which just invites the agent to work around it.
_AGENT_SHELL_FENCE = (
    "unset RAY_grpc_enable_http_proxy grpc_proxy GRPC_PROXY no_grpc_proxy; "
    "export RAY_ADDRESS=127.0.0.1:1 RAY_NUM_REDIS_GET_RETRIES=1 "
    "RAY_py_gcs_connect_timeout_s=2; "
)


class ChipyardBashTool(BashTool):
    """``BashTool`` for agents: each command runs with Ray's cluster wiring removed.

    The trial iteration's agent used ``chipyard_bash`` to ``ray.init`` from the
    build node, then read logs and tool source on the head, launched its own
    Yosys runs on the VLSI node and inspected the pipeline's actors. On this
    cluster the head is the operator's machine, so that is arbitrary code
    execution there.

    This is a fence, not a sandbox: a determined agent can rebuild the proxy
    settings (they are in other processes' environments on the same node).
    Real isolation needs the agent's shell outside the Ray network. The prompts
    carry the matching rule.
    """

    def run_command(self, command: str) -> str:
        """Run a bash command on the chipyard build node and return combined stdout/stderr."""
        return super().run_command(_AGENT_SHELL_FENCE + command)


class PerfAreaExperimentTool(ChiaTool):
    """LLM-callable rebuild + sub-block-synth tool, reporting area and fmax.

    Stateful across method calls within an LLM session:

    - ``rebuild_verilog()`` snapshots the child RTL on the chipyard node and
      caches its module names on the actor.
    - CACTI Liberty is cached on the VLSI node per distinct ``.top.mems.conf``,
      so only the first synth of each side pays for characterization. SRAM macros
      don't vary per ``vlsi_top``, so this is safe.
    - In-flight synths are tracked in a per-handle dict; ``synth_status`` polls
      the corresponding Ray task and returns either "running" or the full
      structured summary.
    """

    def __init__(
        self,
        name: str,
        chipyard_path: str,
        build_config: str,
        parent_branch: str,
        logger_actor_name: str,
        pg_opts: dict,
        head_node_id: str,
        default_timeout: int = 5400,  # 1.5 hours
        make_timeout: int = 7200,
        task_options: Optional[dict] = None,
        parent_generated_src: Optional[list[tuple[str, str]]] = None,
        parent_src_dir: Optional[str] = None,
    ):
        super().__init__(name, task_options=task_options)
        # All instance attributes must be set BEFORE super().__post_init__()
        # because __post_init__ materializes the Ray actor — anything assigned
        # after that point only lives on the client-side proxy, not the remote
        # actor process that handles MCP method calls. (BashTool does the same
        # thing with self.work_dir / self.timeout_seconds.)
        self._chipyard_path = chipyard_path
        self._build_config = build_config
        self._parent_branch = parent_branch
        self._logger_actor_name = logger_actor_name
        # pg_opts: scheduling options for the chipyard placement group bundle.
        # Used to dispatch chipyard-bound work (make verilog, report staging)
        # while the actor itself lives on the head node.
        self._pg_opts = pg_opts
        # head_node_id: where to pin _experiment_orchestrator. The orchestrator
        # must run on the head so its inner cacti/synthesis child tasks are
        # head-submitted (avoids the cross-AWS-worker lease storm).
        self._head_node_id = head_node_id
        self._default_timeout = default_timeout
        self._make_timeout = make_timeout
        # The RTL itself stays on the chipyard node: the child snapshot in
        # _AB_CHILD_SRC_DIR (written by rebuild_verilog), the parent in
        # parent_src_dir (the loop's Step 3 staging of the same source). The
        # actor only keeps what list_modules* needs: child names from the last
        # rebuild, and the parent's source, already local from the DB.
        # Nothing CACTI-related is dispatched from the actor -- that deadlocked
        # in PENDING_NODE_ASSIGNMENT (see _start_synth docstring) -- it all runs
        # in the background orchestrator.
        self._child_modules: list[str] | None = None
        self._parent_generated_src: list[tuple[str, str]] | None = parent_generated_src
        self._parent_src_dir = parent_src_dir
        # In-flight synth tasks. Keyed by short handle string returned to the
        # LLM; value is {ref, side, vlsi_top, started}. Drained when
        # synth_status fetches the result successfully (or errors).
        self._inflight: dict[str, dict] = {}
        self.mcp.add_tool(self.rebuild_verilog,      name=f"{name}_rebuild_verilog")
        self.mcp.add_tool(self.list_modules,         name=f"{name}_list_modules")
        self.mcp.add_tool(self.list_modules_parent,  name=f"{name}_list_modules_parent")
        self.mcp.add_tool(self.start_synth_child,    name=f"{name}_start_synth_child")
        self.mcp.add_tool(self.start_synth_parent,   name=f"{name}_start_synth_parent")
        self.mcp.add_tool(self.synth_status,         name=f"{name}_synth_status")
        super().__post_init__()

    # ------------------------------------------------------------------ #
    # rebuild_verilog: dispatch `make verilog` to the chipyard worker
    # ------------------------------------------------------------------ #
    def rebuild_verilog(self) -> str:
        """Re-elaborate Chisel into Verilog using Chipyard's ``make verilog`` target.

        Dispatches ``make verilog CONFIG=<BUILD_CONFIG>`` to a chipyard-PG-pinned
        Ray task (``_rebuild_verilog_remote``) that runs on the chipyard worker
        where the chipyard tree lives. This skips the Verilator C++ simulator
        build, so it's much faster than the full build the surrounding pipeline
        does. After it succeeds, the generated Verilog (and the
        ``.top.mems.conf``) is snapshotted for ``start_synth_child()``, and its
        module names are available to ``list_modules()``.

        Returns a one-line summary on success, or a stderr tail on failure.
        """
        summary, names = get(
            _rebuild_verilog_remote.options(**self._pg_opts).chia_remote(
                self._chipyard_path, self._build_config, self._make_timeout,
            )
        )
        if names is not None:
            self._child_modules = names
        return summary

    # ------------------------------------------------------------------ #
    # list_modules / list_modules_parent
    # ------------------------------------------------------------------ #
    def list_modules(self) -> str:
        """List the Verilog module names from the cached *child* generated source.

        Call ``rebuild_verilog()`` first. One name per line; you can pass any
        of these as ``vlsi_top`` to ``start_synth_child``. Output is truncated past
        500 modules (use chipyard_bash to grep gen-collateral directly).
        """
        if not self._child_modules:
            return "ERROR: no Verilog cached. Call rebuild_verilog() first."
        return self._format_module_list(self._child_modules, side="child")

    def list_modules_parent(self) -> str:
        """List the Verilog module names from the *parent* branch's RTL.

        Available immediately — no ``rebuild_verilog()`` required. Use this in
        Phase 1 to ground your mental model of what modules exist, and to
        diff against ``list_modules()`` after editing to spot structural
        drift (renames, splits, new modules). Pass any returned name as
        ``vlsi_top`` to ``start_synth_parent``.
        """
        if not self._parent_generated_src:
            return (
                "ERROR: parent generated_src was not provided when the tool "
                "was constructed. Re-launch the flow with a populated DB."
            )
        return self._format_module_list(
            sorted(_parse_verilog_modules(self._parent_generated_src)), side="parent")

    def _format_module_list(self, names: list[str], side: str) -> str:
        """Return the sorted module *names* one per line, truncated past 500."""
        if len(names) > 500:
            shown = "\n".join(names[:500])
            return (
                shown
                + f"\n... ({len(names) - 500} more {side} modules truncated; "
                f"grep gen-collateral/ via chipyard_bash to see all)\n"
            )
        return "\n".join(names) + "\n"

    # ------------------------------------------------------------------ #
    # start_synth_child / start_synth_parent — dispatch sub-block synths
    # ------------------------------------------------------------------ #
    def start_synth_child(self, vlsi_top: str, timeout_seconds: int = 0) -> str:
        """Start a sub-block synth on the LLM-edited (child) RTL.

        Async: returns a short handle string in sub-seconds; CACTI (cached per
        SRAM set), MacroCompiler remap, and the actual Yosys + OpenSTA run all
        happen in the background. Call ``synth_status(handle=...)`` to check
        progress and retrieve results when done.

        Background runtime is the synthesis itself plus a small fixed prep: the
        first call per side also characterizes its SRAMs with CACTI, and later
        calls reuse that. A register-file-sized block takes ~1-2 min of Yosys.

        Issue this in parallel with ``start_synth_parent(vlsi_top=...)`` for
        an A/B comparison: both runs proceed concurrently on the VLSI
        worker (capacity permitting). Then poll the two handles via
        ``synth_status``.

        Args:
            vlsi_top: A Verilog module name from the child RTL. Use
                ``list_modules()`` to see valid options. Pick the *smallest*
                module that contains the bottleneck cluster you targeted in
                Phase 1 — smaller = faster synthesis runtime per experiment.
            timeout_seconds: Per-synthesis cap. 0 → use the tool's default
                (5400s = 1.5 hours). Tighten with ``timeout_seconds`` for
                small blocks to fail-fast.

        Returns:
            A multi-line string of the form::

                started: handle=abc12345, side=child, vlsi_top=IssueUnitCollapsing, timeout_seconds=5400
                poll with synth_status(handle="abc12345", max_wait_seconds=180)

            Keep the handle and poll via ``synth_status``. The actor will not
            print further progress; ``synth_status`` is your visibility.
        """
        if not self._child_modules:
            return "ERROR: no Verilog cached. Call rebuild_verilog() first."
        return self._start_synth(
            src_dir=_AB_CHILD_SRC_DIR,
            vlsi_top=vlsi_top,
            timeout_seconds=timeout_seconds or self._default_timeout,
            side="child",
        )

    def start_synth_parent(self, vlsi_top: str, timeout_seconds: int = 0) -> str:
        """Start a sub-block synth on the parent branch's *unmodified* RTL.

        Analog of ``start_synth_child`` for the pre-edit baseline. The parent
        RTL is fixed for the session (staged by the loop before your session
        started), so no ``rebuild_verilog`` precondition.

        Same async semantics as ``start_synth_child``: returns a handle in
        sub-seconds, and prep + synthesis + STA run in the background.

        Issue in parallel with ``start_synth_child(vlsi_top=...)`` for the
        A/B comparison; both runs proceed concurrently on the VLSI
        worker.

        Args / returns: same shape as ``start_synth_child``.
        """
        if not self._parent_src_dir:
            return (
                "ERROR: no parent RTL directory was provided when the tool "
                "was constructed. Re-launch the flow."
            )
        return self._start_synth(
            src_dir=self._parent_src_dir,
            vlsi_top=vlsi_top,
            timeout_seconds=timeout_seconds or self._default_timeout,
            side="parent",
        )

    def _start_synth(
        self,
        src_dir: str,
        vlsi_top: str,
        timeout_seconds: int,
        side: str,
    ) -> str:
        """Shared start path: submit the orchestrator Ray task and stash its handle.

        The orchestrator runs the full pipeline (CACTI → MacroCompiler remap +
        closure filter → synthesis + STA → log → return) as a background task. We
        explicitly use scheduling_strategy="DEFAULT" so the orchestrator
        runs free of this actor's chipyard placement group — earlier we
        observed actor-dispatched CACTI tasks sitting in
        PENDING_NODE_ASSIGNMENT forever, presumably due to a PG-inheritance
        / runtime-env interaction. Running the whole pipeline as a Ray task
        avoids that path.

        Sub-second return; the actual work happens in the background and is
        polled via ``synth_status(handle, max_wait_seconds=...)``.
        """
        if side not in ("child", "parent"):
            return f"ERROR: invalid side {side!r}; expected 'child' or 'parent'."

        # NodeAffinity to head_node_id (soft=False) — the orchestrator MUST
        # run on the head so its inner cacti / synthesis dispatches are
        # head-submitted. We hit a cross-worker lease storm when the
        # orchestrator landed on a non-head node and tried to dispatch a
        # VLSI=1 child task.
        ref = _experiment_orchestrator.options(
            scheduling_strategy=NodeAffinitySchedulingStrategy(
                node_id=self._head_node_id, soft=False,
            )
        ).chia_remote(
            side, src_dir, vlsi_top, timeout_seconds,
            self._pg_opts, self._logger_actor_name, self._chipyard_path,
        )
        handle = uuid.uuid4().hex[:8]
        self._inflight[handle] = {
            "ref": ref,
            "side": side,
            "vlsi_top": vlsi_top,
            "started": time.time(),
        }
        print(
            f"  [experiment:{side}] start_synth dispatched: handle={handle}, "
            f"vlsi_top={vlsi_top}, timeout_seconds={timeout_seconds}"
        )
        return (
            f"started: handle={handle}, side={side}, vlsi_top={vlsi_top}, "
            f"timeout_seconds={timeout_seconds}\n"
            f"Prep + Yosys synth + OpenSTA run in the background.\n"
            f"poll with synth_status(handle=\"{handle}\", max_wait_seconds=180)"
        )

    # ------------------------------------------------------------------ #
    # synth_status — poll an in-flight synth
    # ------------------------------------------------------------------ #
    def synth_status(self, handle: str, max_wait_seconds: int = 0) -> str:
        """Check on an in-flight synth dispatched by ``start_synth_child`` /
        ``start_synth_parent``.

        Args:
            handle: The handle returned by a previous ``start_synth_*`` call.
            max_wait_seconds: 0 → return current state immediately. >0 →
                block up to that many seconds for the synth to finish before
                responding. Cap is 240; keep it under ~200 so the MCP HTTP
                round-trip stays inside the agent's session timeout. Recommended
                value: 180 (3 minutes).

        Returns:
            While running, a multi-line string of the form::

                status: running
                handle: abc12345
                side: child
                vlsi_top: IssueUnitCollapsing
                elapsed_seconds: 423.1
                retry: synth_status(handle="abc12345", max_wait_seconds=180)

            On completion (ok or synthesis_failed)::

                status: ok
                handle: abc12345
                side: child
                exp_id: 7
                vlsi_top: IssueUnitCollapsing
                modules_in_closure: 23
                area: 412,855.4 um2   <- total cell area, SRAM macros included
                sram_macro_area: 0.0 um2
                std_cell_area: 412,855.4 um2
                fmax_mhz: 24.7   <- tt_025C_1v80; judge both sides against the tile's fmax
                sta_success: True
                worst_slack: ... slack (VIOLATED) -30.1 ...
                elapsed_seconds: 212.3
                synth_seconds: 96.4 (CACTI cached: True)
                area_report: /tmp/improve_perf_area/experiments/7/IssueUnitCollapsing.synth_stat.txt
                timing_report: /tmp/improve_perf_area/experiments/7/IssueUnitCollapsing.sta.rpt
                reports_dir: /tmp/improve_perf_area/experiments/7
                db_files_dir: <DB_DIR>/files/<branch>/experiments/7
                hint: run the SAME vlsi_top on the other side and compare BOTH...

            Compare the two sides on **both** numbers: ``area`` is what the edit
            was probably meant to shrink, and ``fmax_mhz`` is the hard gate it
            must not trip. The gate is about the tile: if both sides' sub-block
            fmax is above the full-tile parent fmax, it passes whatever the
            child-vs-parent delta is.

            Once a result has been fetched successfully, the handle is dropped
            from the actor's in-flight set — calling ``synth_status`` again
            with the same handle will error.
        """
        inflight = self._inflight.get(handle)
        if not inflight:
            return (
                f"ERROR: no such handle '{handle}'. Either the handle was "
                f"already polled to completion (results are one-shot), it "
                f"was never returned by start_synth_*, or the actor "
                f"restarted."
            )
        ref = inflight["ref"]
        timeout = max(0, min(int(max_wait_seconds), 240))
        ready, _ = ray.wait([ref], timeout=timeout)
        if not ready:
            elapsed = time.time() - inflight["started"]
            return (
                f"status: running\n"
                f"handle: {handle}\n"
                f"side: {inflight['side']}\n"
                f"vlsi_top: {inflight['vlsi_top']}\n"
                f"elapsed_seconds: {elapsed:.1f}\n"
                f"retry: synth_status(handle=\"{handle}\", max_wait_seconds=180)"
            )
        try:
            result = ray.get(ref)
        except Exception as e:
            del self._inflight[handle]
            return (
                f"synth FAILED (handle={handle}, side={inflight['side']}, "
                f"vlsi_top={inflight['vlsi_top']}): {e}"
            )
        del self._inflight[handle]
        return self._format_result(handle, result)

    def _format_result(self, handle: str, result: dict) -> str:
        """Stage reports to /tmp on the chipyard worker and produce the
        user-facing summary string for a completed (or failed) experiment.

        Stage runs as a chipyard-pinned Ray remote
        (``_stage_experiment_reports_remote``) because the actor lives on
        the head — the reports need to land on the chipyard worker's /tmp
        for ``chipyard_bash`` to grep them. The head-side ``files_dir``
        from the DB lives under constants.DB_DIR and is invisible from the
        chipyard container, so /tmp is the LLM's actual reading path.
        """
        status = result.get("status", "?")
        side = result.get("side", "?")
        vlsi_top = result.get("vlsi_top", "?")
        elapsed = result.get("elapsed_seconds", 0.0)

        if status == "vlsi_top_not_found":
            close = result.get("close") or []
            list_call = "list_modules" if side == "child" else "list_modules_parent"
            hint = (
                f"\nSimilarly-named modules in {side} RTL: {close}" if close
                else f"\n(no similar names in {side} RTL; call {list_call}() to see valid names)"
            )
            return f"ERROR: '{vlsi_top}' is not a Verilog module name.{hint}"

        if status == "synthesis_failed" and "error" in result:
            return (
                f"synth FAILED (handle={handle}, side={side}, vlsi_top={vlsi_top}, "
                f"{elapsed:.1f}s): {result['error']}"
            )

        exp_id = result.get("exp_id")
        reports = result.get("reports") or {}
        local_dir = get(
            _stage_experiment_reports_remote.options(**self._pg_opts).chia_remote(
                exp_id, _pack(reports),
            )
        )

        def _local(suffixes):
            """Staged path of the first report matching one of *suffixes*."""
            for suffix in suffixes:
                for name, body in reports.items():
                    if name.endswith(suffix) and body:
                        return os.path.join(local_dir, name.rsplit("/", 1)[-1])
            return None

        area_local = _local(AREA_REPORT_SUFFIXES)
        timing_local = _local(STA_REPORT_SUFFIXES)

        def _num(key, unit=""):
            v = result.get(key)
            if v is None:
                return "(not reported)"
            return f"{v:,.1f}{unit}" if isinstance(v, float) else f"{v}{unit}"

        return (
            f"status: {status}\n"
            f"handle: {handle}\n"
            f"side: {side}\n"
            f"exp_id: {exp_id}\n"
            f"vlsi_top: {vlsi_top}\n"
            f"modules_in_closure: {result.get('modules_in_closure', '?')}\n"
            f"area: {_num('area', ' um2')}   <- total cell area, SRAM macros included\n"
            f"sram_macro_area: {_num('sram_macro_area', ' um2')}\n"
            f"std_cell_area: {_num('std_cell_area', ' um2')}\n"
            f"fmax_mhz: {_num('fmax_mhz')}   <- {STA_CORNER}; costs the tile no "
            f"frequency while both sides stay above the full-tile parent fmax\n"
            f"sta_success: {result.get('sta_success')}\n"
            f"worst_slack: {result.get('worst_slack_line') or '(no slack line)'}\n"
            f"elapsed_seconds: {elapsed:.1f}\n"
            f"synth_seconds: {_num('synth_seconds')} "
            f"(CACTI cached: {result.get('cacti_cached')})\n"
            f"area_report: {area_local or '(none emitted)'}\n"
            f"timing_report: {timing_local or '(none emitted)'}\n"
            f"reports_dir: {local_dir}\n"
            f"db_files_dir: {result.get('files_dir', '(?)')}\n"
            f"hint: run the SAME vlsi_top on the other side and compare BOTH "
            f"area (lower is better) and fmax_mhz (frequency is a factor of the "
            f"objective, so price any drop below the full-tile parent fmax "
            f"against the area saving). Grep the "
            f"reports via chipyard_bash on this node, e.g. "
            f"`grep 'Chip area for module' {area_local or local_dir + '/<top>.synth_stat.txt'} "
            f"| sort -t: -k2 -g -r | head -20`."
        )

