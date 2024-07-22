import asyncio
from typing import Callable

from fastapi import FastAPI, Request

from arcade.actor.base import BaseActor


class FastAPIActor(BaseActor):
    def __init__(self, app: FastAPI) -> None:
        """
        Initialize the FastAPIActor with a FastAPI app
        instance and an empty ToolCatalog.
        """
        super().__init__()
        self.app = app
        self.router = FastAPIRouter(app)
        self.register_routes()


class FastAPIRouter:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def add_route(self, path: str, handler: Callable, methods: str) -> None:
        """
        Add a route to the FastAPI application.
        """
        for method in methods:
            if method == "GET":
                self.app.get(path)(self.wrap_handler(handler))
            elif method == "POST":
                self.app.post(path)(self.wrap_handler(handler))
            elif method == "PUT":
                self.app.put(path)(self.wrap_handler(handler))
            elif method == "DELETE":
                self.app.delete(path)(self.wrap_handler(handler))
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    def wrap_handler(self, handler: Callable) -> Callable:
        """
        Wrap the handler to handle FastAPI-specific request and response.
        """

        async def wrapped_handler(request: Request):
            if asyncio.iscoroutinefunction(handler):
                return await handler(request)
            else:
                return handler(request)

        return wrapped_handler
