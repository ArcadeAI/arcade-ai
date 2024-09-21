import os
import logging
import time
from datetime import datetime
from typing import Any, Callable, ClassVar, cast

from arcade.actor.core.common import Actor, Router
from arcade.actor.core.components import (
    ActorComponent,
    CallToolComponent,
    CatalogComponent,
    HealthCheckComponent,
)
from arcade.core.catalog import ToolCatalog, Toolkit
from arcade.core.executor import ToolExecutor
from arcade.core.schema import (
    ToolCallRequest,
    ToolCallResponse,
    ToolDefinition,
)

DEFAULT_TOOLKIT_NAME = "Tools"


logger = logging.getLogger(__name__)


class BaseActor(Actor):
    """
    A base actor class that provides a default implementation for registering tools and invoking them.
    Actor implementations for specific web frameworks will inherit from this class.
    """

    base_path = "/actor"  # By default, prefix all our routes with /actor

    default_components: ClassVar[tuple[type[ActorComponent], ...]] = (
        CatalogComponent,
        CallToolComponent,
        HealthCheckComponent,
    )

    def __init__(self, secret: str | None = None, disable_auth: bool = False) -> None:
        """
        Initialize the BaseActor with an empty ToolCatalog.
        If no secret is provided, the actor will use the ARCADE_ACTOR_SECRET environment variable.
        """
        self.catalog = ToolCatalog()
        self.disable_auth = disable_auth
        if disable_auth:
            logger.warning(
                "Warning: Actor is running without authentication. Not recommended for production."
            )

        self.secret = self._set_secret(secret, disable_auth)

    def _set_secret(self, secret: str | None, disable_auth: bool) -> str:
        if disable_auth:
            return ""

        # If secret is provided, use it
        if secret is not None:
            return secret

        # If secret is not provided, try to get it from environment variables
        env_secret = os.environ.get("ARCADE_ACTOR_SECRET")
        if env_secret is not None:
            return env_secret

        raise ValueError(
            "No secret provided for actor. Set the ARCADE_ACTOR_SECRET environment variable."
        )

    def get_catalog(self) -> list[ToolDefinition]:
        """
        Get the catalog as a list of ToolDefinitions.
        """
        return [tool.definition for tool in self.catalog]

    def register_tool(self, tool: Callable, toolkit_name: str | None = None) -> None:
        """
        Register a tool to the catalog.
        """
        self.catalog.add_tool(tool, toolkit_name or DEFAULT_TOOLKIT_NAME)

    def register_toolkit(self, toolkit: Toolkit) -> None:
        """
        Register a toolkit to the catalog.
        """
        self.catalog.add_toolkit(toolkit)

    async def call_tool(self, tool_request: ToolCallRequest) -> ToolCallResponse:
        """
        Call (invoke) a tool using the ToolExecutor.
        """
        tool_fqname = tool_request.tool.get_fully_qualified_name()

        try:
            materialized_tool = self.catalog.get_tool(tool_fqname)
        except KeyError:
            raise ValueError(
                f"Tool {tool_fqname} not found in catalog with toolkit version {tool_request.tool.version}."
            )

        start_time = time.time()

        output = await ToolExecutor.run(
            func=materialized_tool.tool,
            definition=materialized_tool.definition,
            input_model=materialized_tool.input_model,
            output_model=materialized_tool.output_model,
            context=tool_request.context,
            **tool_request.inputs or {},
        )

        end_time = time.time()  # End time in seconds
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        return ToolCallResponse(
            invocation_id=tool_request.invocation_id or "",
            duration=duration_ms,
            finished_at=datetime.now().isoformat(),
            success=not output.error,
            output=output,
        )

    def health_check(self) -> dict[str, Any]:
        """
        Provide a health check that serves as a heartbeat of actor health.
        """
        return {"status": "ok", "tool_count": len(self.catalog)}

    def register_routes(self, router: Router) -> None:
        """
        Register the necessary routes to the application.
        """
        for component_cls in self.default_components:
            component_cls(self).register(router)
