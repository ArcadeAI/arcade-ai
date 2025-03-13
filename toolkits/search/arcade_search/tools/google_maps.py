from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from serpapi import Client as SerpClient

from arcade_search.constants import (
    DEFAULT_GOOGLE_MAPS_COUNTRY,
    DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    DEFAULT_GOOGLE_MAPS_LANGUAGE,
    DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
)
from arcade_search.models import GoogleMapsDistanceUnit, GoogleMapsTravelMode
from arcade_search.utils import get_google_maps_directions


@tool(requires_secrets=["SERP_API_KEY"])
async def get_directions_between_addresses(
    context: ToolContext,
    origin_address: Annotated[str, "The origin address"],
    destination_address: Annotated[str, "The destination address"],
    language: Annotated[
        str,
        "2-letter language code to use in the Google Maps search. "
        f"Defaults to '{DEFAULT_GOOGLE_MAPS_LANGUAGE}'.",
    ] = DEFAULT_GOOGLE_MAPS_LANGUAGE,
    country: Annotated[
        Optional[str],
        f"2-letter country code to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_COUNTRY}'.",
    ] = DEFAULT_GOOGLE_MAPS_COUNTRY,
    distance_unit: Annotated[
        GoogleMapsDistanceUnit,
        f"Distance unit to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT}'.",
    ] = DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    travel_mode: Annotated[
        GoogleMapsTravelMode,
        f"Travel mode to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_TRAVEL_MODE}'.",
    ] = DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
) -> Annotated[dict, "The directions from Google Maps"]:
    """Get directions from Google Maps."""
    api_key = context.get_secret("SERP_API_KEY")
    client = SerpClient(api_key=api_key)

    return get_google_maps_directions(
        serp_client=client,
        origin_address=origin_address,
        destination_address=destination_address,
        language=language,
        country=country,
        distance_unit=distance_unit,
        travel_mode=travel_mode,
    )


@tool(requires_secrets=["SERP_API_KEY"])
async def get_directions_between_coordinates(
    context: ToolContext,
    origin_latitude: Annotated[str, "The origin latitude"],
    origin_longitude: Annotated[str, "The origin longitude"],
    destination_latitude: Annotated[str, "The destination latitude"],
    destination_longitude: Annotated[str, "The destination longitude"],
    language: Annotated[
        str,
        "2-letter language code to use in the Google Maps search. "
        f"Defaults to '{DEFAULT_GOOGLE_MAPS_LANGUAGE}'.",
    ] = DEFAULT_GOOGLE_MAPS_LANGUAGE,
    country: Annotated[
        Optional[str],
        f"2-letter country code to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_COUNTRY}'.",
    ] = DEFAULT_GOOGLE_MAPS_COUNTRY,
    distance_unit: Annotated[
        GoogleMapsDistanceUnit,
        f"Distance unit to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT}'.",
    ] = DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    travel_mode: Annotated[
        GoogleMapsTravelMode,
        f"Travel mode to use in the Google Maps search. Defaults to "
        f"'{DEFAULT_GOOGLE_MAPS_TRAVEL_MODE}'.",
    ] = DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
) -> Annotated[dict, "The directions from Google Maps"]:
    """Get directions from Google Maps."""
    api_key = context.get_secret("SERP_API_KEY")
    client = SerpClient(api_key=api_key)

    return get_google_maps_directions(
        serp_client=client,
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        language=language,
        country=country,
        distance_unit=distance_unit,
        travel_mode=travel_mode,
    )
