from typing import Annotated, Any

from arcade.sdk import ToolContext, tool
from arcade.sdk.errors import ToolExecutionError

from arcade_search.constants import (
    DEFAULT_GOOGLE_SHOPPING_COUNTRY,
    DEFAULT_GOOGLE_SHOPPING_LANGUAGE,
)
from arcade_search.google_data import GOOGLE_DOMAIN_BY_COUNTRY_CODE
from arcade_search.utils import (
    call_serpapi,
    extract_shopping_results,
    prepare_params,
    resolve_country_code,
    resolve_language_code,
)


@tool(requires_secrets=["SERP_API_KEY"])
async def search_shopping_products(
    context: ToolContext,
    keywords: Annotated[
        str,
        "Keywords to search for products in Google Shopping. E.g. 'Apple iPhone'.",
    ],
    country_code: Annotated[
        str,
        "2-character country code to search for products in Google Shopping. "
        f"E.g. 'us' (United States). Defaults to '{DEFAULT_GOOGLE_SHOPPING_COUNTRY}'.",
    ] = DEFAULT_GOOGLE_SHOPPING_COUNTRY,
    language_code: Annotated[
        str,
        "2-character language code to search for news articles. E.g. 'en' (English). "
        f"Defaults to '{DEFAULT_GOOGLE_SHOPPING_LANGUAGE}'.",
    ] = DEFAULT_GOOGLE_SHOPPING_LANGUAGE,
) -> Annotated[dict[str, list[dict[str, Any]]], "News results."]:
    """Search for news articles related to a given query."""
    country_code = resolve_country_code(country_code, DEFAULT_GOOGLE_SHOPPING_COUNTRY, "us")
    language_code = resolve_language_code(language_code, DEFAULT_GOOGLE_SHOPPING_LANGUAGE, "en")
    google_domain = GOOGLE_DOMAIN_BY_COUNTRY_CODE.get(country_code, "google.com")

    params = prepare_params(
        "google_shopping",
        q=keywords,
        gl=country_code,
        hl=language_code,
        google_domain=google_domain,
    )

    response = call_serpapi(context, params)

    if response.get("error"):
        error_msg = response.get("error") or "Unknown Google Shopping Error"
        raise ToolExecutionError(error_msg)

    return {
        "products": extract_shopping_results(response),
    }
