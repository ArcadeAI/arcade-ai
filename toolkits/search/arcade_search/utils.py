import re
from datetime import datetime
from typing import Any, Optional, cast
from zoneinfo import ZoneInfo

from arcade.sdk import ToolContext
from arcade.sdk.errors import ToolExecutionError
from serpapi import Client as SerpClient

from arcade_search.constants import (
    DEFAULT_GOOGLE_MAPS_COUNTRY,
    DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    DEFAULT_GOOGLE_MAPS_LANGUAGE,
    DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
)
from arcade_search.enums import GoogleMapsDistanceUnit, GoogleMapsTravelMode
from arcade_search.exceptions import CountryNotFoundError, LanguageNotFoundError
from arcade_search.google_maps_data import COUNTRY_CODES, LANGUAGE_CODES


# ------------------------------------------------------------------------------------------------
# General SerpAPI utils
# ------------------------------------------------------------------------------------------------
def prepare_params(engine: str, **kwargs: Any) -> dict[str, Any]:
    """
    Prepares a parameters dictionary for the SerpAPI call.

    Parameters:
        engine: The engine name (e.g., "google", "google_finance").
        kwargs: Any additional parameters to include.

    Returns:
        A dictionary containing the base parameters plus any extras,
        excluding any parameters whose value is None.
    """
    params = {"engine": engine}
    params.update({k: v for k, v in kwargs.items() if v is not None})
    return params


def call_serpapi(context: ToolContext, params: dict) -> dict:
    """
    Execute a search query using the SerpAPI client and return the results as a dictionary.

    Args:
        context: The tool context containing required secrets.
        params: A dictionary of parameters for the SerpAPI search.

    Returns:
        The search results as a dictionary.
    """
    api_key = context.get_secret("SERP_API_KEY")
    client = SerpClient(api_key=api_key)
    try:
        search = client.search(params)
        return cast(dict[str, Any], search.as_dict())  # type: ignore[no-any-return]
    except Exception as e:
        # SerpAPI error messages sometimes contain the API key, so we need to sanitize it
        sanitized_e = re.sub(r"(api_key=)[^ &]+", r"\1***", str(e))
        raise ToolExecutionError(
            message="Failed to fetch search results",
            developer_message=sanitized_e,
        )


# ------------------------------------------------------------------------------------------------
# Google Maps utils
# ------------------------------------------------------------------------------------------------
def get_google_maps_directions(
    context: ToolContext,
    origin_address: Optional[str] = None,
    destination_address: Optional[str] = None,
    origin_latitude: Optional[str] = None,
    origin_longitude: Optional[str] = None,
    destination_latitude: Optional[str] = None,
    destination_longitude: Optional[str] = None,
    language: str = DEFAULT_GOOGLE_MAPS_LANGUAGE,
    country: Optional[str] = DEFAULT_GOOGLE_MAPS_COUNTRY,
    distance_unit: GoogleMapsDistanceUnit = DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    travel_mode: GoogleMapsTravelMode = DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
) -> dict:
    """Get directions from Google Maps.

    Provide either all(origin_address, destination_address) or
    all(origin_latitude, origin_longitude, destination_latitude, destination_longitude).

    Args:
        context: Tool context containing required Serp API Key secret.
        origin_address: Origin address.
        destination_address: Destination address.
        origin_latitude: Origin latitude.
        origin_longitude: Origin longitude.
        destination_latitude: Destination latitude.
        destination_longitude: Destination longitude.
        language: Language to use in the Google Maps search. Defaults to 'en' (English).
        country: 2-letter country code to use in the Google Maps search. Defaults to None
            (no country is specified).
        distance_unit: Distance unit to use in the Google Maps search. Defaults to 'km'
            (kilometers).
        travel_mode: Travel mode to use in the Google Maps search. Defaults to 'best'
            (best mode).

    Returns:
        The directions from Google Maps.
    """
    language = language.lower()

    if language not in LANGUAGE_CODES:
        raise LanguageNotFoundError(language)

    params = prepare_params(
        engine="google_maps_directions",
        hl=language,
        distance_unit=google_maps_distance_unit_to_serpapi(distance_unit),
        travel_mode=google_maps_travel_mode_to_serpapi(travel_mode),
    )

    if any([
        origin_latitude,
        origin_longitude,
        destination_latitude,
        destination_longitude,
    ]) and any([origin_address, destination_address]):
        raise ValueError("Either coordinates or addresses must be provided, not both")

    elif all([origin_latitude, origin_longitude, destination_latitude, destination_longitude]):
        params["start_coords"] = f"{origin_latitude},{origin_longitude}"
        params["end_coords"] = f"{destination_latitude},{destination_longitude}"

    elif all([origin_address, destination_address]):
        params["start_addr"] = str(origin_address)
        params["end_addr"] = str(destination_address)

    else:
        raise ValueError("Either coordinates or addresses must be provided")

    if country:
        country = country.lower()
        if country not in COUNTRY_CODES:
            raise CountryNotFoundError(country)
        params["gl"] = country

    results = call_serpapi(context, params)

    for direction in results["directions"]:
        if "arrive_around" in direction:
            direction["arrive_around"] = enrich_google_maps_arrive_around(
                direction["arrive_around"]
            )

    return results


def google_maps_travel_mode_to_serpapi(travel_mode: GoogleMapsTravelMode) -> int:
    data = {
        GoogleMapsTravelMode.BEST: 6,
        GoogleMapsTravelMode.DRIVING: 0,
        GoogleMapsTravelMode.MOTORCYCLE: 9,
        GoogleMapsTravelMode.PUBLIC_TRANSPORTATION: 3,
        GoogleMapsTravelMode.WALKING: 2,
        GoogleMapsTravelMode.BICYCLE: 1,
        GoogleMapsTravelMode.FLIGHT: 4,
    }
    return data[travel_mode]


def google_maps_distance_unit_to_serpapi(distance_unit: GoogleMapsDistanceUnit) -> int:
    data = {
        GoogleMapsDistanceUnit.KM: 0,
        GoogleMapsDistanceUnit.MILES: 1,
    }
    return data[distance_unit]


def enrich_google_maps_arrive_around(timestamp: Optional[int]) -> dict[str, Any]:
    if not timestamp:
        return {}

    dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).isoformat()
    return {"datetime": dt, "timestamp": timestamp}


# ------------------------------------------------------------------------------------------------
# Google Flights utils
# ------------------------------------------------------------------------------------------------
def parse_flight_results(results: dict[str, Any]) -> dict[str, Any]:
    """Parse the flight results from the Google Flights API

    Note: Best flights is not always returned from the API.
    """
    flight_data = {}
    flights = []

    if "best_flights" in results:
        flights.extend(results["best_flights"])
    if "other_flights" in results:
        flights.extend(results["other_flights"])
    if "price_insights" in results:
        flight_data["price_insights"] = results["price_insights"]

    flight_data["flights"] = flights

    return flight_data
