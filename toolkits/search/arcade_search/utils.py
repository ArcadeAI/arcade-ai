from datetime import datetime
from typing import Any, Optional, cast
from zoneinfo import ZoneInfo

from arcade_search.constants import (
    DEFAULT_GOOGLE_MAPS_COUNTRY,
    DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT,
    DEFAULT_GOOGLE_MAPS_LANGUAGE,
    DEFAULT_GOOGLE_MAPS_TRAVEL_MODE,
)
from arcade_search.exceptions import CountryNotFoundError, LanguageNotFoundError
from arcade_search.google_maps_data import COUNTRY_CODES, LANGUAGE_CODES
from arcade_search.models import GoogleMapsDistanceUnit, GoogleMapsTravelMode


def get_google_maps_directions(
    serp_client: Any,
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

    :param serp_client: SerpAPI client to use in the Google Maps search.
    :param origin_address: Origin address.
    :param destination_address: Destination address.
    :param origin_latitude: Origin latitude.
    :param origin_longitude: Origin longitude.
    :param destination_latitude: Destination latitude.
    :param destination_longitude: Destination longitude.
    :param language: Language to use in the Google Maps search. Defaults to 'en' (English).
    :param country: 2-letter country code to use in the Google Maps search. Defaults to None
        (no country is specified).
    :param distance_unit: Distance unit to use in the Google Maps search. Defaults to 'km'
        (kilometers).
    :param travel_mode: Travel mode to use in the Google Maps search. Defaults to 'best'
        (best mode).
    """
    language = language.lower()

    if language not in LANGUAGE_CODES:
        raise LanguageNotFoundError(language)

    params = {
        "engine": "google_maps_directions",
        "hl": language,
        "distance_unit": google_maps_distance_unit_to_serpapi(distance_unit),
        "travel_mode": google_maps_travel_mode_to_serpapi(travel_mode),
    }

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

    search = serp_client.search(params)
    results = cast(dict[str, Any], search.as_dict())

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
        GoogleMapsTravelMode.TWO_WHEELER: 9,
        GoogleMapsTravelMode.TRANSIT: 3,
        GoogleMapsTravelMode.WALKING: 2,
        GoogleMapsTravelMode.CYCLING: 1,
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
