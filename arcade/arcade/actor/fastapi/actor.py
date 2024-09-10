import json
from typing import Any, Callable

from fastapi import FastAPI, Request

from arcade.actor.core.base import (
    BaseActor,
    Router,
)
from arcade.actor.core.common import RequestData
from arcade.actor.utils import is_async_callable


class FastAPIActor(BaseActor):
    """
    An Arcade Actor that is hosted inside a FastAPI app.
    """

    def __init__(self, app: FastAPI, *, disable_auth: bool = False) -> None:
        """
        Initialize the FastAPIActor with a FastAPI app
        instance and an empty ToolCatalog.
        """
        super().__init__(disable_auth)
        self.app = app
        self.router = FastAPIRouter(app, self)
        self.register_routes(self.router)


class FastAPIRouter(Router):
    def __init__(self, app: FastAPI, actor: BaseActor) -> None:
        self.app = app
        self.actor = actor

    def _wrap_handler(self, handler: Callable, require_auth: bool = True) -> Callable:
        """
        Wrap the handler to handle FastAPI-specific request and response.
        """

        use_auth_for_route = not self.actor.disable_auth and require_auth

        async def wrapped_handler(
            request: Request,
            _: None = Depends(validate_engine_request) if use_auth_for_route else None,
        ) -> Any:
            body_str = await request.body()
            body_json = json.loads(body_str) if body_str else {}
            request_data = RequestData(
                path=request.url.path,
                method=request.method,
                body_json=body_json,
            )
            if is_async_callable(handler):
                return await handler(request_data)
            else:
                return handler(request_data)

        return wrapped_handler

    def add_route(
        self, endpoint_path: str, handler: Callable, method: str, require_auth: bool = True
    ) -> None:
        """
        Add a route to the FastAPI application.
        """
        self.app.add_api_route(
            f"{self.actor.base_path}/{endpoint_path}",
            self._wrap_handler(handler, require_auth),
            methods=[method],
        )
