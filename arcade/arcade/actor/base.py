from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from arcade.actor.schema import (
    InvokeToolRequest,
    InvokeToolResponse,
    ToolOutput,
    ToolOutputError,
)
from arcade.core.catalog import ToolCatalog, Toolkit
from arcade.core.executor import ToolExecutor
from arcade.core.response import ToolResponse
from arcade.core.tool import ToolDefinition


class ActorComponent(ABC):
    @abstractmethod
    def register(self, router: Any) -> None:
        """
        Register the component with the given router.
        """
        pass

    @abstractmethod
    async def __call__(self, request: Any) -> Any:
        """
        Handle the request.
        """
        pass


class BaseActor:
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
        response = await ToolExecutor.run(
            func=materialized_tool.tool,
            input_model=materialized_tool.input_model,
            output_model=materialized_tool.output_model,
            **tool_request.inputs,
        )
        if response.code == 200:
            output = ToolOutput(value=response.data.result)
        else:
            output = ToolOutput(error=ToolOutputError(message=response.msg))

        return InvokeToolResponse(
            invocation_id=tool_request.invocation_id,
            finished_at=datetime.now().isoformat(),
            success=response.code == 200,
            output=output,
        )

    def health_check(self) -> dict[str, str]:
        """
        Provide a health check that serves as a heartbeat of actor health.
        """
        return {"status": "healthy"}

    def register_routes(self, router: Any) -> None:
        """
        Register the necessary routes to the application.
        """
        catalog_component = CatalogComponent(self)
        invoke_tool_component = InvokeToolComponent(self)
        health_check_component = HealthCheckComponent(self)

        catalog_component.register(router)
        invoke_tool_component.register(router)
        health_check_component.register(router)


class CatalogComponent(ActorComponent):
    def __init__(self, actor: BaseActor) -> None:
        self.actor = actor

    def register(self, router: Any) -> None:
        """
        Register the catalog route with the router.
        """
        router.add_route("/catalog", self, methods=["GET"])

    async def __call__(self, request: Any) -> list[ToolDefinition]:
        """
        Handle the request to get the catalog.
        """
        return self.actor.get_catalog()


class InvokeToolComponent(ActorComponent):
    def __init__(self, actor: BaseActor) -> None:
        self.actor = actor

    def register(self, router: Any) -> None:
        """
        Register the invoke tool route with the router.
        """
        router.add_route("/invoke/<tool_name>", self, methods=["POST"])

    async def __call__(self, request: Any) -> ToolResponse:
        """
        Handle the request to invoke a tool.
        """
        tool_name = request.path_params["tool_name"]
        input_data = await request.json()
        return await self.actor.invoke_tool(tool_name, input_data)


class HealthCheckComponent(ActorComponent):
    def __init__(self, actor: BaseActor) -> None:
        self.actor = actor

    def register(self, router: Any) -> None:
        """
        Register the health check route with the router.
        """
        router.add_route("/health", self, methods=["GET"])

    async def __call__(self, request: Any) -> dict[str, str]:
        """
        Handle the request for a health check.
        """
        return self.actor.health_check()