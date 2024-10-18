import time
from typing import Any

from opentelemetry import trace

from arcade.actor.core.common import Actor, ActorComponent, RequestData, Router
from arcade.core.schema import (
    ToolCallRequest,
    ToolCallResponse,
    ToolDefinition,
    ToolStatusRequest,
    ToolStatusResponse,
)


class CatalogComponent(ActorComponent):
    def __init__(self, actor: Actor) -> None:
        self.actor = actor

    def register(self, router: Router) -> None:
        """
        Register the catalog route with the router.
        """
        router.add_route("tools", self, method="GET")

    async def __call__(self, request: RequestData) -> list[ToolDefinition]:
        """
        Handle the request to get the catalog.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("Catalog"):
            return self.actor.get_catalog()


class CallToolComponent(ActorComponent):
    def __init__(self, actor: Actor) -> None:
        self.actor = actor

    def register(self, router: Router) -> None:
        """
        Register the call tool route with the router.
        """
        router.add_route("tools/invoke", self, method="POST")

    async def __call__(self, request: RequestData) -> ToolCallResponse:
        """
        Handle the request to call (invoke) a tool.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("CallTool"):
            call_tool_request_data = request.body_json
            call_tool_request = ToolCallRequest.model_validate(call_tool_request_data)
            return await self.actor.call_tool(call_tool_request)


class ToolStatusComponent(ActorComponent):
    def __init__(self, actor: Actor) -> None:
        self.actor = actor
        self.last_update_time = time.time()

    def register(self, router: Router) -> None:
        """
        Register the tool status check route with the router.
        """
        router.add_route("tools/status", self, method="POST")

    async def __call__(self, request: RequestData) -> ToolStatusResponse:
        """
        Handle long-polling requests for tool status updates.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("ToolStatusCheck"):
            call_tool_status_data = request.body_json
            call_status_request = ToolStatusRequest.model_validate(call_tool_status_data)
            return await self.actor.tool_status(call_status_request)


class HealthCheckComponent(ActorComponent):
    def __init__(self, actor: Actor) -> None:
        self.actor = actor

    def register(self, router: Router) -> None:
        """
        Register the health check route with the router.
        """
        router.add_route("health", self, method="GET", require_auth=False)

    async def __call__(self, request: RequestData) -> dict[str, Any]:
        """
        Handle the request for a health check.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("HealthCheck"):
            return self.actor.health_check()
