import os

from arcade_search.models import GoogleMapsDistanceUnit, GoogleMapsTravelMode

DEFAULT_GOOGLE_MAPS_LANGUAGE = os.getenv("GOOGLE_MAPS_LANGUAGE", "en")
DEFAULT_GOOGLE_MAPS_COUNTRY = os.getenv("GOOGLE_MAPS_COUNTRY", None)
DEFAULT_GOOGLE_MAPS_DISTANCE_UNIT = GoogleMapsDistanceUnit(
    os.getenv("GOOGLE_MAPS_DISTANCE_UNIT", GoogleMapsDistanceUnit.KM.value)
)
DEFAULT_GOOGLE_MAPS_TRAVEL_MODE = GoogleMapsTravelMode(
    os.getenv("GOOGLE_MAPS_TRAVEL_MODE", GoogleMapsTravelMode.BEST.value)
)
