import httpx

from arcade.core.schema import ToolContext
from arcade.sdk.errors import ToolExecutionError
from arcade_spotify.tools.constants import ENDPOINTS, SPOTIFY_BASE_URL
from arcade_spotify.tools.models import PlaybackState


async def send_spotify_request(
    context: ToolContext,
    method: str,
    url: str,
    params: dict | None = None,
    json_data: dict | None = None,
) -> httpx.Response:
    """
    Send an asynchronous request to the Spotify API.

    Args:
        context: The tool context containing the authorization token.
        method: The HTTP method (GET, POST, PUT, DELETE, etc.).
        url: The full URL for the API endpoint.
        params: Query parameters to include in the request.
        json_data: JSON data to include in the request body.

    Returns:
        The response object from the API request.

    Raises:
        ToolExecutionError: If the request fails for any reason.
    """
    headers = {"Authorization": f"Bearer {context.authorization.token}"}

    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, params=params, json=json_data)

    return response


def handle_spotify_response(response: httpx.Response, url: str):
    """Handle Spotify API response

    Raise the appropriate exceptions for non-200 status codes.

    Args:
        response: The response object from the API request.
        url: The URL of the API endpoint.

    Raises:
        ToolExecutionError: If the response contains an error status code.
    """
    if 200 <= response.status_code < 300:
        return

    error_messages = {
        401: "Unauthorized: Invalid or expired token",
        403: "Forbidden: User does not have Spotify Premium, or wrong consumer key, bad nonce, expired timestamp, etc.",
        429: "Too Many Requests: Rate limit exceeded",
    }

    error_message = error_messages.get(
        response.status_code,
        f"Failed to process request: {response.text}. Status code: {response.status_code}",
    )

    raise ToolExecutionError(f"Error accessing '{url}': {error_message}")


def handle_404_playback_state(response, message, is_playing: bool) -> dict | None:
    if response.status_code == 404:
        return convert_to_playback_state({
            "is_playing": is_playing,
            "message": message,
        }).to_dict()


def get_url(endpoint: str, **kwargs) -> str:
    """
    Get the full Spotify URL for a given endpoint.

    :param endpoint: The endpoint key from ENDPOINTS
    :param kwargs: The parameters to format the URL with
    :return: The full URL
    """
    return f"{SPOTIFY_BASE_URL}{ENDPOINTS[endpoint].format(**kwargs)}"


def convert_to_playback_state(data: dict) -> PlaybackState:
    """
    Convert the Spotify API endpoint "/me/player" response data to a PlaybackState object.

    Args:
        data: The response data from the Spotify API endpoint "/me/player".

    Returns:
        An instance of PlaybackState populated with the data.
    """
    playback_state = PlaybackState(
        device_name=data.get("device", {}).get("name"),
        device_id=data.get("device", {}).get("id"),
        currently_playing_type=data.get("currently_playing_type"),
        is_playing=data.get("is_playing"),
        progress_ms=data.get("progress_ms"),
        message=data.get("message"),
    )

    if data.get("currently_playing_type") == "track":
        item = data.get("item", {})
        album = item.get("album", {})
        playback_state.album_name = album.get("name")
        playback_state.album_id = album.get("id")
        playback_state.album_artists = [artist.get("name") for artist in album.get("artists", [])]
        playback_state.album_spotify_url = album.get("external_urls", {}).get("spotify")
        playback_state.track_name = item.get("name")
        playback_state.track_id = item.get("id")
        playback_state.track_artists = [artist.get("name") for artist in item.get("artists", [])]
    elif data.get("currently_playing_type") == "episode":
        item = data.get("item", {})
        show = item.get("show", {})
        playback_state.show_name = show.get("name")
        playback_state.show_id = show.get("id")
        playback_state.show_spotify_url = show.get("external_urls", {}).get("spotify")
        playback_state.episode_name = item.get("name")
        playback_state.episode_id = item.get("id")
        playback_state.episode_spotify_url = item.get("external_urls", {}).get("spotify")

    return playback_state