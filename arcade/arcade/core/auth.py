from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuthProviderType(str, Enum):
    oauth2 = "oauth2"


class ToolAuthorization(BaseModel):
    """Marks a tool as requiring authorization."""

    model_config = ConfigDict(frozen=True)

    provider_id: Optional[str] = None
    """The provider ID configured in Arcade that acts as an alias to well-known configuration."""

    provider_type: AuthProviderType
    """The type of the authorization provider."""

    id: Optional[str] = None
    """A provider's unique identifier, allowing the tool to specify a specific authorization provider. Recommended for private tools only."""

    scopes: Optional[list[str]] = None
    """The scope(s) needed for the authorized action."""


class OAuth2(ToolAuthorization):
    """Marks a tool as requiring OAuth 2.0 authorization."""

    def __init__(self, *, id: str, scopes: Optional[list[str]] = None):  # noqa: A002
        super().__init__(id=id, scopes=scopes, provider_type=AuthProviderType.oauth2)


class Atlassian(OAuth2):
    """Marks a tool as requiring Atlassian authorization."""

    provider_id: str = "atlassian"


class Discord(OAuth2):
    """Marks a tool as requiring Discord authorization."""

    provider_id: str = "discord"


class Dropbox(OAuth2):
    """Marks a tool as requiring Dropbox authorization."""

    provider_id: str = "dropbox"


class Google(OAuth2):
    """Marks a tool as requiring Google authorization."""

    provider_id: str = "google"


class Slack(OAuth2):
    """Marks a tool as requiring Slack (user token) authorization."""

    provider_id: str = "slack"


class GitHub(OAuth2):
    """Marks a tool as requiring GitHub App authorization."""

    provider_id: str = "github"


class X(OAuth2):
    """Marks a tool as requiring X (Twitter) authorization."""

    provider_id: str = "x"


class LinkedIn(OAuth2):
    """Marks a tool as requiring LinkedIn authorization."""

    provider_id: str = "linkedin"


class Spotify(OAuth2):
    """Marks a tool as requiring Spotify authorization."""

    provider_id: str = "spotify"


class Zoom(OAuth2):
    """Marks a tool as requiring Zoom authorization."""

    provider_id: str = "zoom"
