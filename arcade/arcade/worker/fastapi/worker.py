import asyncio
import http.server
import json
from typing import Any, Callable
from urllib.parse import urlparse

from opentelemetry.metrics import Meter

from arcade.worker.core.base import (
    BaseWorker,
    Router,
)
from arcade.worker.core.common import RequestData
from arcade.worker.fastapi.auth import validate_engine_request
from arcade.worker.utils import is_async_callable


# Define a simple credentials class so we can reuse the validate_engine_request function.
class SimpleHTTPAuthorizationCredentials:
    def __init__(self, scheme: str, credentials: str):
        self.scheme = scheme
        self.credentials = credentials


class HTTPWorker(BaseWorker):
    """
    An Arcade Worker that is hosted in a simple HTTP server without external dependencies.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        secret: str | None = None,
        *,
        disable_auth: bool = False,
        otel_meter: Meter | None = None,
    ) -> None:
        """
        Initialize the HTTPWorker with a host and port.
        If no secret is provided, the worker will use the ARCADE_WORKER_SECRET environment variable.
        """
        super().__init__(secret, disable_auth, otel_meter)
        self.host = host
        self.port = port
        self.router = HTTPRouter(self)
        self.register_routes(self.router)

    def start(self) -> None:
        """
        Start the built-in HTTP server.
        """
        # Set router on the request handler class so it can lookup routes.
        SimpleHTTPRequestHandler.router = self.router

        server_address = (self.host, self.port)
        try:
            # Use a multithreaded HTTP server if available.
            httpd = http.server.ThreadingHTTPServer(server_address, SimpleHTTPRequestHandler)
        except AttributeError:
            httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)
        print(f"Starting HTTP server on {self.host}:{self.port}")
        httpd.serve_forever()


class HTTPRouter(Router):
    def __init__(self, worker: BaseWorker) -> None:
        self.worker = worker
        # Store routes as a list of dictionaries holding path, method, and handler.
        self.routes: list[dict[str, Any]] = []

    def _wrap_handler(self, handler: Callable, require_auth: bool = True) -> Callable:
        """
        Wrap the handler to process an HTTP request and response.
        """

        def wrapped_handler(request_handler: http.server.BaseHTTPRequestHandler) -> None:
            # --- Authentication Check ---
            if not self.worker.disable_auth and require_auth:
                auth_header = request_handler.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    request_handler.send_response(401)
                    request_handler.send_header("Content-Type", "application/json")
                    request_handler.end_headers()
                    response = {"detail": "Unauthorized"}
                    request_handler.wfile.write(json.dumps(response).encode())
                    return

                token = auth_header[len("Bearer ") :].strip()
                creds = SimpleHTTPAuthorizationCredentials("Bearer", token)
                try:
                    asyncio.run(validate_engine_request(self.worker.secret, creds))
                except Exception as e:
                    request_handler.send_response(401)
                    request_handler.send_header("Content-Type", "application/json")
                    request_handler.end_headers()
                    response = {"detail": "Unauthorized", "error": str(e)}
                    request_handler.wfile.write(json.dumps(response).encode())
                    return

            # --- Request Body Parsing ---
            content_length = request_handler.headers.get("Content-Length")
            try:
                length = int(content_length) if content_length else 0
            except ValueError:
                length = 0
            body_bytes = request_handler.rfile.read(length) if length > 0 else b""
            body_str = body_bytes.decode("utf-8")
            try:
                body_json = json.loads(body_str) if body_str else {}
            except json.JSONDecodeError:
                body_json = {}

            # --- Prepare RequestData ---
            request_data = RequestData(
                path=request_handler.path,
                method=request_handler.command,
                body_json=body_json,
            )

            # --- Handler Invocation ---
            try:
                if is_async_callable(handler):
                    result = asyncio.run(handler(request_data))
                else:
                    result = handler(request_data)
                response_body = json.dumps(result)
                request_handler.send_response(200)
                request_handler.send_header("Content-Type", "application/json")
                request_handler.end_headers()
                request_handler.wfile.write(response_body.encode())
            except Exception as e:
                request_handler.send_response(500)
                request_handler.send_header("Content-Type", "application/json")
                request_handler.end_headers()
                response = {"detail": "Internal Server Error", "error": str(e)}
                request_handler.wfile.write(json.dumps(response).encode())

        return wrapped_handler

    def add_route(
        self, endpoint_path: str, handler: Callable, method: str, require_auth: bool = True
    ) -> None:
        """
        Add a route to the HTTP server.
        """
        # Prepend the worker's base path.
        full_path = f"{self.worker.base_path}/{endpoint_path}".replace("//", "/")
        wrapped_handler = self._wrap_handler(handler, require_auth)
        self.routes.append({
            "path": full_path,
            "method": method.upper(),
            "handler": wrapped_handler,
        })


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    # This class variable will be set by HTTPWorker.start()
    router: HTTPRouter = None

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def handle_request(self):
        # Parse the request path (ignoring any query parameters)
        parsed_path = urlparse(self.path)
        request_path = parsed_path.path
        request_method = self.command.upper()

        # Look up a matching route.
        for route in self.router.routes:
            if route["path"] == request_path and route["method"] == request_method:
                route["handler"](self)
                return
        # No matching route found; return 404.
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": "Not found"}
        self.wfile.write(json.dumps(response).encode())

    # def log_message(self, format, *args):
    #     # Override default logging to reduce noise.
    #     return
