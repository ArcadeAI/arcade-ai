"""
Arcade TDK Runtime Context Wrapper

Exposes namespaced runtime capabilities (`log`, `resources`, `prompts`, etc.)
for tools without changing function signatures by subclassing ToolContext and
delegating to the current ModelContext provided by the runtime (e.g., MCP).

Tools can annotate their parameter as either `ToolContext` or `Context`.
At runtime, engines should set the current model context using the MCP layer.

Note: This shim may be removed in arcade-tdk 3.0.0. Prefer annotating with
`arcade_tdk.Context` today; a future migration path to a direct runtime context
will be provided before removal.
"""

from __future__ import annotations

from arcade_core.context import (
    LogsContext,
    ModelContext,
    NotificationsContext,
    ProgressContext,
    PromptsContext,
    ResourcesContext,
    SamplingContext,
    ToolsContext,
    UIContext,
)
from arcade_core.schema import ToolContext

# Optional runtime provider import (guarded to avoid hard dependency at import time)
try:
    from arcade_mcp.context import (
        get_current_model_context as _tdk_get_current_model_context,
    )
except Exception:  # pragma: no cover - optional dependency
    _tdk_get_current_model_context = None


def _get_model_context() -> ModelContext:
    """Retrieve the current ModelContext from the runtime layer.

    Engines embedding Arcade must set a current model context during tool execution.
    """
    if _tdk_get_current_model_context is None:
        raise RuntimeError(
            "Model context runtime provider not available. Did you include arcade-mcp and set the current context?"
        )
    ctx: Context | None = _tdk_get_current_model_context()
    if ctx:
        return ctx
    raise RuntimeError(
        "No current model context is set. This should be set by the engine during tool execution."
    )


class Context(ToolContext):
    """Runtime tool context for tools.

    Subclasses the transport-agnostic ToolContext and exposes namespaced runtime
    capabilities by delegating to the active ModelContext. Tools can annotate
    their context parameter as either ToolContext or Context.
    """

    # Namespaced runtime properties
    @property
    def log(self) -> LogsContext:
        return _get_model_context().log

    @property
    def progress(self) -> ProgressContext:
        return _get_model_context().progress

    @property
    def resources(self) -> ResourcesContext:
        return _get_model_context().resources

    @property
    def tools(self) -> ToolsContext:
        return _get_model_context().tools

    @property
    def prompts(self) -> PromptsContext:
        return _get_model_context().prompts

    @property
    def sampling(self) -> SamplingContext:
        return _get_model_context().sampling

    @property
    def ui(self) -> UIContext:
        return _get_model_context().ui

    @property
    def notifications(self) -> NotificationsContext:
        return _get_model_context().notifications

    # Identity passthrough via model context
    @property
    def request_id(self) -> str | None:
        return _get_model_context().request_id

    @property
    def session_id(self) -> str | None:
        return _get_model_context().session_id

    # Access to underlying tool context (self)
    @property
    def tool_context(self) -> ToolContext:  # for parity with ModelContext
        return self
