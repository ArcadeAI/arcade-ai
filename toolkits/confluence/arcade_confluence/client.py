from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from arcade.sdk.errors import ToolExecutionError

from arcade_confluence.utils import remove_none_values


class ConfluenceClient:
    ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
    BASE_URL = "https://api.atlassian.com/ex/confluence"
    API_VERSION = "wiki/api/v2"

    def __init__(self, token: str, user_domain: str):
        self.token = token
        self.cloud_id = self._get_cloud_id(user_domain)

    def _get_cloud_id(self, user_domain: str) -> str:
        """
        Fetch the cloudId for <user_domain>.atlassian.net
        using the OAuth2 3LO accessible-resources endpoint.

        For details on why this is necessary, see: https://developer.atlassian.com/cloud/oauth/getting-started/making-calls-to-api
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = httpx.get(self.ACCESSIBLE_RESOURCES_URL, headers=headers)
        resp.raise_for_status()
        for res in resp.json():
            if f"{user_domain}.atlassian.net" in res.get("url", ""):
                return str(res["id"])
        raise ToolExecutionError(
            message=f"Cloud ID for the domain {user_domain}.atlassian.net not found"
        )

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}/{self.cloud_id}/{self.API_VERSION}/{path.lstrip('/')}",
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    def _transform_get_spaces_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Transform the response from the GET /spaces endpoint by converting relative webui paths
        to absolute URLs using the base URL from the response.
        """
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor", [None]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        results = response.get("results", [])

        transformed_results = []
        for space in results:
            space_copy = space.copy()
            if "_links" in space_copy and "webui" in space_copy["_links"]:
                webui_path = space_copy["_links"]["webui"]
                space_copy["url"] = base_url + webui_path
                del space_copy["_links"]
            transformed_results.append(space_copy)

        results = {"spaces": transformed_results, "pagination_token": pagination_token}
        return remove_none_values(results)

    def _transform_get_space_by_id_response(
        self, response: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Transform the response from the GET /spaces/{space_id} endpoint by converting
        relative webui paths to absolute URLs using the base URL from the response.
        """
        if "_links" in response:
            base_url = response["_links"].get("base", "")
            webui_path = response["_links"].get("webui", "")
            response["url"] = f"{base_url}{webui_path}"
            del response["_links"]
        return {"space": response}
