"""The agent LLM -- Claude or Codex -- for the edit step and the debugger.

``--llm`` picks the CLI (``claude`` or ``codex``), ``--model`` the model and
``--effort`` the thinking level. Both CLIs live in the ``llm_1`` container, each
against its own staged credentials, and each backend's calls request its own
resource (``codex_creds`` / ``claude_creds``), so a run only needs the node to
declare the one it selects.

  ``LLMSpec``          -- backend + model + effort; builds the LLM on the worker
  ``_llm_prompt_task`` -- runs one prompt in-process on the LLM worker
  ``prompt_llm``       -- the edit step's entry point
  ``LLMDebugger``      -- a ``debug_failure``-compatible handle, passed to
                          ``common.build``'s ``debug_fn`` hook and called
                          directly for verilator failures

``common.common_nodes.debug_failure`` is not used: it is hardcoded to Claude on
the ``llm`` resource, and its session threading needs the caller to carry the
transcript bytes, which ``common.build`` does not.
"""

import os
import shutil
from dataclasses import dataclass
from uuid import uuid4

from chia.base.ChiaFunction import ChiaFunction, get
from chia.base.llm_call import QueryResult
from chia.base.tools.BashTool import BashTool
from chia.models.claude import ClaudeCodeLLM
from chia.models.codex import CodexLLM

from perf_area_eff_opt.constants import (
    LLM_BACKEND,
    LLM_DEFAULT_MODELS,
    LLM_EFFORT,
    LLM_EFFORT_LEVELS,
    LLM_ENV,
)

# Container-local map from a caller's session key to the CLI session it started.
# The debugger's retries share a key (a uuid4 from common.build or the verilator
# loop), and every call lands on the same llm_1 container, so the CLI's own
# session files are already on disk there -- what a fresh LLM object lacks is
# which session to resume.
_SESSION_DIR = "/tmp/llm_sessions"


@dataclass(frozen=True)
class LLMSpec:
    """Which agent CLI runs, on which model, at which thinking level."""

    backend: str = LLM_BACKEND
    model: str | None = None  # None -> LLM_DEFAULT_MODELS[backend]
    effort: str = LLM_EFFORT

    def __post_init__(self):
        if self.backend not in LLM_DEFAULT_MODELS:
            raise ValueError(f"unknown LLM backend {self.backend!r}; expected one "
                             f"of {', '.join(LLM_DEFAULT_MODELS)}")
        levels = LLM_EFFORT_LEVELS[self.backend]
        if self.effort not in levels:
            raise ValueError(f"{self.backend} has no effort {self.effort!r}; "
                             f"expected one of {', '.join(levels)}")
        if self.model is None:
            object.__setattr__(self, "model", LLM_DEFAULT_MODELS[self.backend])

    @property
    def creds_resource(self) -> str:
        return f"{self.backend}_creds"

    def __str__(self) -> str:
        return f"{self.backend} {self.model} (effort={self.effort})"

    def build(self, work_dir: str, **config) -> CodexLLM | ClaudeCodeLLM:
        if self.backend == "codex":
            return CodexLLM(model=self.model, reasoning_effort=self.effort,
                            work_dir=work_dir, **config)
        # The claude CLI has no working-dir flag: it runs in the process CWD,
        # which _llm_prompt_task sets, and keys its session files on it.
        # projects_cwd=None derives the transcript dir from that same CWD.
        return ClaudeCodeLLM(model=self.model,
                             extra_cli_args=["--effort", self.effort],
                             projects_cwd=None, **config)


def _resume(llm, backend: str, session_key: str) -> None:
    """Point *llm* at the session *session_key* already started, if any."""
    if backend == "claude":
        # Claude takes a caller-chosen id: --session-id the first time, then
        # --resume once its transcript exists (a second --session-id is refused).
        llm._session_id = session_key
        if os.path.exists(llm._transcript_path()):
            llm._call_counter = 1
        return
    # Codex assigns its own id, read back off the first run's output.
    path = os.path.join(_SESSION_DIR, session_key)
    if os.path.exists(path):
        with open(path) as f:
            llm._session_id = f.read().strip() or None


@ChiaFunction()
def _llm_prompt_task(
    spec: LLMSpec, config: dict, user_message: str, tools,
    work_dir: str = LLM_ENV,
    aux_dir: str | None = None,
    aux_files: dict[str, str] | None = None,
    session_key: str | None = None,
) -> QueryResult:
    """Run one prompt on the LLM worker this task was scheduled on.

    Builds the LLM here and calls ``prompt`` in process -- a local call does NOT
    re-dispatch, so the CLI runs on this worker, next to the ``aux_files``
    written for it. Resources come from the caller's ``.options``.
    """
    os.chdir(work_dir)
    os.makedirs("/tmp/ray/llm_logs", exist_ok=True)
    if spec.backend == "claude":
        # Each session starts from the prompt and the DB alone. Claude Code's
        # auto-memory otherwise keeps notes in this container's ~/.claude and
        # reads them into every later session -- across iterations and parent
        # branches alike, so one run's "already taken" steers the next.
        os.environ["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    if aux_files:
        os.makedirs(aux_dir, exist_ok=True)
        for name, content in aux_files.items():
            with open(os.path.join(aux_dir, name), "w") as f:
                f.write(content)

    llm = spec.build(work_dir, resume_session=session_key is not None, **config)
    if session_key is not None:
        _resume(llm, spec.backend, session_key)
    try:
        cli = llm.prompt(user_message, tools)
    finally:
        if aux_files:
            shutil.rmtree(aux_dir, ignore_errors=True)

    codex_session = getattr(cli, "session_id", None)
    if session_key is not None and spec.backend == "codex" and codex_session:
        os.makedirs(_SESSION_DIR, exist_ok=True)
        with open(os.path.join(_SESSION_DIR, session_key), "w") as f:
            f.write(codex_session)
    return cli


def prompt_llm(spec: LLMSpec, user_message: str, tools, *,
               logging_name: str, timeout_seconds: int) -> QueryResult:
    """Run the edit step's prompt on a worker holding *spec*'s credentials."""
    return get(
        _llm_prompt_task.options(resources={spec.creds_resource: 0.01}).chia_remote(
            spec,
            # retries=1: a retry is not a resume. It re-sends the whole prompt
            # to a fresh session on a chipyard tree that already carries the
            # failed attempt's edits, and a timeout would stack to retries x
            # timeout_seconds.
            dict(timeout_seconds=timeout_seconds, retries=1,
                 log_dir="/tmp/ray/llm_logs", logging_name=logging_name),
            user_message, tools,
        ))


class LLMDebugger:
    """Build/test debugger bound to one :class:`LLMSpec`.

    ``common.build`` calls ``debug_fn.chia_remote(...)`` with
    ``common.common_nodes.debug_failure``'s arguments and ``get``s the result.
    A module-level ChiaFunction could not carry the run's ``--llm``/``--model``/
    ``--effort`` through that fixed call, so this object binds them and
    ``chia_remote`` dispatches the prompt task itself.
    """

    def __init__(self, spec: LLMSpec):
        self.spec = spec

    def chia_remote(
        self,
        error_context: str,
        chipyard_bash: BashTool,
        attempt: int = 1,
        session_id: str | None = None,
        llm_env: str = LLM_ENV,
        prompt_text: str = "",
        aux_files: dict[str, str] | None = None,
    ):
        """Dispatch one debugging call; ``get`` the ref for its QueryResult.

        ``prompt_text`` is the debugger prompt markdown, sent inline (this
        package installs no slash commands in ``llm_env``). Any ``{AUX_DIR}``
        placeholder in it is replaced with a per-call temp dir on the LLM
        machine into which ``aux_files`` are written, then deleted after the
        call. Calls sharing a ``session_id`` continue one CLI session, so the
        debugger remembers the fixes it already tried.
        """
        aux_dir = f"/tmp/llm_aux/{uuid4().hex[:8]}"
        if prompt_text:
            prompt = (f"{prompt_text.replace('{AUX_DIR}', aux_dir)}\n\n"
                      f"{error_context}")
        else:
            # No slash commands are installed in llm_env, so an empty
            # prompt_text would send a bare "/debugging ..." string neither CLI
            # can expand. Say so rather than letting the model improvise
            # against a literal.
            prompt = (f"You are debugging a build or test failure. Diagnose it "
                      f"and fix the source using the chipyard_bash tool.\n\n"
                      f"{error_context}")

        # A whole `llm` unit on top of the credentials: the node declares 4, so
        # at most four debuggers share one CLI install.
        return _llm_prompt_task.options(
            resources={"llm": 1.0, self.spec.creds_resource: 0.01},
        ).chia_remote(
            self.spec,
            # retries=1 for the same reason as the edit step; the outer
            # max_debug_retries loop is the retry budget.
            dict(timeout_seconds=1800, retries=1, log_dir="/tmp/ray/llm_logs",
                 logging_name=f"debugger_attempt{attempt}"),
            prompt, [chipyard_bash],
            work_dir=llm_env, aux_dir=aux_dir, aux_files=aux_files,
            session_key=session_id,
        )
