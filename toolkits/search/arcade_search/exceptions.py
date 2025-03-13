import json
from typing import Optional

from arcade.core.errors import RetryableToolError

from arcade_search.google_maps_data import COUNTRY_CODES, LANGUAGE_CODES


class GoogleMapsRetryableError(RetryableToolError):
    pass


class CountryNotFoundError(GoogleMapsRetryableError):
    def __init__(self, country: Optional[str]) -> None:
        try:
            valid_countries = json.dumps(COUNTRY_CODES)
        except Exception:
            valid_countries = str(COUNTRY_CODES)

        super().__init__(
            f"Country not found: '{country}'",
            additional_prompt_content=f"Valid countries are: {valid_countries}",
        )


class LanguageNotFoundError(GoogleMapsRetryableError):
    def __init__(self, language: Optional[str]) -> None:
        try:
            valid_languages = json.dumps(LANGUAGE_CODES)
        except Exception:
            valid_languages = str(LANGUAGE_CODES)

        super().__init__(
            f"Language not found: '{language}'",
            additional_prompt_content=f"Valid languages are: {valid_languages}",
        )
