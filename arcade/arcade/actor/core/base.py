import time
from datetime import datetime
from typing import Any, Callable, ClassVar

from arcade.actor.core import Actor, Router
from arcade.actor.core.components import (
    ActorComponent,
    CatalogComponent,
    HealthCheckComponent,
    InvokeToolComponent,
)
from arcade.core.catalog import ToolCatalog, Toolkit
from arcade.core.executor import ToolExecutor
from arcade.core.schema import (
    InvokeToolRequest,
    InvokeToolResponse,
    ToolCallError,
    ToolCallOutput,
    ToolContext,
    ToolDefinition,
)


class BaseActor(Actor):
    """
    A base actor class that provides a default implementation for registering tools and invoking them.
    Actor implementations for specific web frameworks will inherit from this class.
    """

    base_path = "/actor"  # By default, prefix all our routes with /actor

    default_components: ClassVar[tuple[type[ActorComponent], ...]] = (
        CatalogComponent,
        InvokeToolComponent,
        HealthCheckComponent,
    )

    def __init__(self) -> None:
        """
        Initialize the BaseActor with an empty ToolCatalog.
        """
        self.catalog = ToolCatalog()

    def get_catalog(self) -> list[ToolDefinition]:
        """
        Get the catalog as a list of ToolDefinitions.
        """
        return [tool.definition for tool in self.catalog]

    def register_tool(self, tool: Callable) -> None:
        """
        Register a tool to the catalog.
        """
        self.catalog.add_tool(tool)

    def register_toolkit(self, toolkit: Toolkit) -> None:
        """
        Register a toolkit to the catalog.
        """
        self.catalog.add_toolkit(toolkit)

    async def invoke_tool(self, tool_request: InvokeToolRequest) -> InvokeToolResponse:
        """
        Invoke a tool using the ToolExecutor.
        """
        tool_name = tool_request.tool.name
        tool = self.catalog.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found in catalog.")

        materialized_tool = self.catalog[tool_name]

        start_time = time.time()

        response = await ToolExecutor.run(
            func=materialized_tool.tool,
            definition=materialized_tool.definition,
            input_model=materialized_tool.input_model,
            output_model=materialized_tool.output_model,
            context=tool_request.context or ToolContext(),
            **tool_request.inputs or {},
        )
        if response.code == 200 and response.data is not None:
            output = ToolCallOutput(value=response.data.result)
        else:
            output = ToolCallOutput(error=ToolCallError(message=response.msg))

        end_time = time.time()  # End time in seconds
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        return InvokeToolResponse(
            invocation_id=tool_request.invocation_id,
            duration=duration_ms,
            finished_at=datetime.now().isoformat(),
            success=response.code == 200,
            output=output,
        )

    def health_check(self) -> dict[str, Any]:
        """
        Provide a health check that serves as a heartbeat of actor health.
        """
        return {"status": "ok", "tool_count": len(self.catalog.tools.keys())}

    def register_routes(self, router: Router) -> None:
        """
        Register the necessary routes to the application.
        """
        for component_cls in self.default_components:
            component_cls(self).register(router)
