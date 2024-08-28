import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel

from arcade.core.schema import ToolCallRequest, ToolCallResponse, ToolDefinition

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class LoggingMixin:
    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


class RequestData(BaseModel):
    """
    The raw data for a request to an actor.
    This is not intended to represent everything about an HTTP request,
    but just the essential info a framework integration will need to extract from the request.
    """

    path: str
    """The path of the request."""
    method: str
    """The method of the request."""
    body_json: dict | None = None
    """The deserialized body of the request (e.g. JSON)"""


class Router(ABC, LoggingMixin):
    """
    A router is responsible for adding routes to the underlying framework hosting the actor.
    """

    @abstractmethod
    def add_route(self, endpoint_path: str, handler: Callable, method: str) -> None:
        """
        Add a route to the router.
        """
        self.logger.debug(f"Adding route: {method} {endpoint_path}")
        pass


class Actor(ABC, LoggingMixin):
    """
    An Actor represents a collection of tools that is hosted inside a web framework
    and can be called by an Engine.
    """

    @abstractmethod
    def get_catalog(self) -> list[ToolDefinition]:
        self.logger.debug("Getting catalog")

    @abstractmethod
    async def call_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        self.logger.debug(f"Calling tool: {request.tool_name}")

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        self.logger.debug("Performing health check")


class ActorComponent(ABC):
    def __init__(self, actor: Actor) -> None:
        self.actor = actor

    @abstractmethod
    def register(self, router: Router) -> None:
        """
        Register the component with the given router.
        """
        pass

    @abstractmethod
    async def __call__(self, request: RequestData) -> Any:
        """
        Handle the request.
        """
        pass
