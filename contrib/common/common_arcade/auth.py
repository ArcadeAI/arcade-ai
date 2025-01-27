import logging
import time

from arcadepy import Arcade
from arcadepy.types.shared import AuthorizationResponse, ToolDefinition

logger = logging.getLogger(__name__)


class ArcadeAuthMixin:
    """Mixin class providing authentication-related functionality for Arcade tools."""

    client: Arcade
    _tools: dict[str, ToolDefinition]

    def authorize(self, tool_name: str, user_id: str) -> AuthorizationResponse:
        """Authorize a user for a tool.

        Args:
            tool_name: The name of the tool to authorize.
            user_id: The user ID to authorize.

        Returns:
            AuthorizationResponse
        """
        return self.client.tools.authorize(tool_name=tool_name, user_id=user_id)

    def wait_for_completion(
        self, auth_response: AuthorizationResponse, timeout: int = 120
    ) -> AuthorizationResponse:
        """Wait for an authorization process to complete.

        Args:
            auth_response: The authorization response from the initial authorize call.
            timeout: Maximum time to wait in seconds (default: 300 seconds / 5 minutes)

        Returns:
            AuthorizationResponse with completed status

        Raises:
            TimeoutError: If authorization process takes longer than timeout
        """
        logger.info(f"Authorization URL: {auth_response.authorization_url}")
        print(f"\nAuthorization URL: {auth_response.authorization_url}\n")
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                timeout_msg = f"Authorization timed out after {timeout} seconds. URL: {auth_response.authorization_url}"
                logger.error(timeout_msg)
                print(f"\nError: {timeout_msg}\n")
                return auth_response

            # Use the built-in wait parameter (max 59 seconds)
            auth_response = self.client.auth.status(
                authorization_id=auth_response.authorization_id,  # type: ignore[arg-type]
                wait=60,
            )
            logger.info(f"Waiting for authorization completion... Status: {auth_response.status}")
            print(f"Authorization status: {auth_response.status}")

            if auth_response.status == "completed":
                print("\nAuthorization completed successfully!\n")
                return auth_response

    def is_authorized(self, authorization_id: str) -> bool:
        """Check if a tool authorization is complete."""
        return self.client.auth.status(authorization_id=authorization_id).status == "completed"

    def requires_auth(self, tool_name: str) -> bool:
        """Check if a tool requires authorization."""
        tool_def = self._tools.get(tool_name)
        if tool_def is None or tool_def.requirements is None:
            return False
        return tool_def.requirements.authorization is not None
