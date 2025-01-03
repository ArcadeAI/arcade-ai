from unittest.mock import MagicMock, Mock, patch

import pytest
from arcadepy.types.shared import ToolDefinition
from common_arcade.exceptions import ToolExecutionError
from crewai_arcade.manager import CrewAIToolManager


@pytest.fixture
def manager():
    """Fixture to create a CrewAIToolManager instance with mocked client and user_id."""
    manager = CrewAIToolManager()
    manager.client = MagicMock()
    manager.user_id = "test_user"
    return manager


@patch("crewai_arcade.manager.CrewAIToolManager.requires_auth")
@patch("crewai_arcade.manager.CrewAIToolManager.authorize")
@patch("crewai_arcade.manager.CrewAIToolManager.is_authorized")
def test_create_tool_function_success(
    mock_is_authorized, mock_authorize, mock_requires_auth, manager
):
    """Test that the tool function executes successfully when authorized."""
    mock_requires_auth.return_value = True
    mock_authorize.return_value = MagicMock(
        authorization_id="auth_id", authorization_url="http://auth.url"
    )
    mock_is_authorized.return_value = True
    manager.client.tools.execute.return_value = MagicMock(
        success=True, output=MagicMock(value="result")
    )

    tool_function = manager.create_tool_function("test_tool")
    result = tool_function()

    assert result == "result"
    manager.client.tools.execute.assert_called_once()


@patch("crewai_arcade.manager.CrewAIToolManager.requires_auth")
@patch("crewai_arcade.manager.CrewAIToolManager.authorize")
@patch("crewai_arcade.manager.CrewAIToolManager.is_authorized")
def test_create_tool_function_unauthorized(
    mock_is_authorized, mock_authorize, mock_requires_auth, manager
):
    """Test that the tool function returns a ToolExecutionError when unauthorized."""
    mock_requires_auth.return_value = True
    mock_is_authorized.return_value = False

    tool_function = manager.create_tool_function("test_tool")
    result = tool_function()
    print(result)
    assert isinstance(result, ToolExecutionError)


@patch("crewai_arcade.manager.CrewAIToolManager.requires_auth")
@patch("crewai_arcade.manager.CrewAIToolManager.authorize")
@patch("crewai_arcade.manager.CrewAIToolManager.is_authorized")
def test_create_tool_function_execution_failure(
    mock_is_authorized, mock_authorize, mock_requires_auth, manager
):
    """Test that the tool function returns a ToolExecutionError on execution failure."""
    mock_requires_auth.return_value = True
    mock_authorize.return_value = MagicMock(
        authorization_id="auth_id", authorization_url="http://auth.url"
    )
    mock_is_authorized.return_value = True
    manager.client.tools.execute.return_value = MagicMock(success=False, error="error")

    tool_function = manager.create_tool_function("test_tool")
    result = tool_function()
    assert isinstance(result, ToolExecutionError)


@patch("crewai_arcade.manager.StructuredTool.from_function")
@patch("crewai_arcade.manager.tool_definition_to_pydantic_model")
def test_wrap_tool(mock_tool_definition_to_pydantic_model, mock_from_function, manager):
    """Test the wrap_tool method to ensure it correctly wraps a tool function."""

    mock_tool_definition_to_pydantic_model.return_value = "args_schema"
    mock_from_function.return_value = "structured_tool"

    tool_definition = Mock(spec=ToolDefinition)
    tool_definition.description = "Test tool"
    tool_name = "test_tool"

    tool_function = manager.create_tool_function(tool_name)

    # Ensure wrap_tool uses the pre-created tool_function
    with patch.object(manager, "create_tool_function", return_value=tool_function):
        result = manager.wrap_tool(tool_name, tool_definition)
    assert result == "structured_tool"

    mock_tool_definition_to_pydantic_model.assert_called_once_with(tool_definition)

    mock_from_function.assert_called_once_with(
        func=tool_function,  # Use the pre-created tool_function
        name=tool_name,
        description=tool_definition.description,
        args_schema="args_schema",
    )
