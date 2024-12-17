from typing import Any, Callable

from arcadepy.types.shared import ToolDefinition
from common_arcade.exceptions import ToolExecutionError
from common_arcade.manager import BaseArcadeManager
from common_arcade.utils import tool_definition_to_pydantic_model

from crewai_arcade.structured import StructuredTool


class CrewAIToolManager(BaseArcadeManager):  # type: ignore[no-any-unimported]
    """CrewAI-specific implementation of the BaseArcadeManager."""

    def create_tool_function(self, tool_name: str, **kwargs: Any) -> Callable[..., Any]:
        """Overrides BaseArcadeManager.create_tool_function."""

        def tool_function(*args: Any, **kwargs: Any) -> Any:
            # Handle authorization if required
            if self.requires_auth(tool_name):
                if not self.user_id:
                    error_message = f"Authorization required for {tool_name}."
                    return ToolExecutionError(error_message)

                # Get authorization status
                auth_response = self.authorize(tool_name, self.user_id)
                if not self.is_authorized(auth_response.authorization_id):
                    return ToolExecutionError(
                        f"Authorization failed for {tool_name}. "
                        f"URL: {auth_response.authorization_url}"
                    )

            # Tool execution
            response = self.client.tools.execute(
                tool_name=tool_name, inputs=kwargs, user_id=self.user_id or None
            )
            if response.success:
                return response.output.value
            return ToolExecutionError(f"Execution failed for {tool_name}: {response.error}")

        return tool_function

    def wrap_tool(
        self, tool_name: str, tool_definition: ToolDefinition, **kwargs: Any
    ) -> StructuredTool:
        """Wrap a tool as a CrewAI StructuredTool.

        Args:
            tool_name: The name of the tool to wrap.
            tool_definition: The definition of the tool to wrap.
            **kwargs: Additional keyword arguments for tool configuration.

        Returns:
            A StructuredTool instance.
        """
        description = tool_definition.description or "No description provided."
        args_schema = tool_definition_to_pydantic_model(tool_definition)
        tool_function = self.create_tool_function(tool_name, **kwargs)

        return StructuredTool.from_function(
            func=tool_function,
            name=tool_name,
            description=description,
            args_schema=args_schema,
        )
