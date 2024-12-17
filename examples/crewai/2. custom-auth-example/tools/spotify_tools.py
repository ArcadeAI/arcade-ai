from typing import Any

import requests
from crewai.tools import BaseTool
from pydantic import Field


class SpotifyAPIError(Exception):
    """Custom exception for Spotify API related errors."""

    pass


class SpotifyDataProcessingError(Exception):
    """Custom exception for data processing related errors."""

    pass


class SpotifyPlaylistTool(BaseTool):
    """Tool to fetch all playlists from Spotify."""

    name: str = "spotify_playlist_tool"
    description: str = "Gets all available Spotify playlists"
    access_token: str = Field(..., description="Spotify API access token")
    timeout: int = Field(default=30, description="Request timeout in seconds")

    def _run(self) -> str:
        """
        Fetches and returns all playlist names.

        Returns:
            str: List of all playlist names

        Raises:
            SpotifyAPIError: If there's an error communicating with Spotify API
            SpotifyDataProcessingError: If there's an error processing the response data
        """
        try:
            # Fetch playlists from Spotify
            url = "https://api.spotify.com/v1/me/playlists"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Extract playlist names
            playlists = response.json()
            playlist_names = [playlist["name"] for playlist in playlists["items"]]

            return "\n".join(playlist_names)

        except requests.exceptions.RequestException as e:
            raise SpotifyAPIError(f"Failed to fetch playlists: {e!s}") from e
        except (KeyError, IndexError) as e:
            raise SpotifyDataProcessingError(f"Error processing playlist data: {e!s}") from e

    def _arun(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Async is not implemented for this tool.")
