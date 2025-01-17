import pytest
from arcade.sdk import ToolAuthorizationContext, ToolContext


@pytest.fixture
def mock_context():
    mock_auth = ToolAuthorizationContext(token="fake-token")  # noqa: S106
    return ToolContext(authorization=mock_auth)


@pytest.fixture
def mock_slack_client(mocker):
    mock_client = mocker.patch("arcade_slack.tools.chat.AsyncWebClient", autospec=True)
    return mock_client.return_value
