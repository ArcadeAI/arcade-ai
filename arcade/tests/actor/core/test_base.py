import asyncio
import os
from unittest import mock

import pytest

from arcade.actor.core.base import BaseActor
from arcade.core.schema import ToolStatusRequest, ToolStatusResponse


@pytest.mark.asyncio
@mock.patch.dict(os.environ, {"ARCADE_ACTOR_SECRET": "test-secret"})
class TestBaseActor:
    async def test_tool_status_different_uuid(self):
        actor = BaseActor()
        actor.uuid = "actor-uuid"
        request = ToolStatusRequest(uuid="different-uuid")

        response = await actor.tool_status(request)

        assert isinstance(response, ToolStatusResponse)
        assert response.uuid == actor.uuid

    async def test_tool_status_timeout(self):
        actor = BaseActor()
        actor.uuid = "actor-uuid"
        request = ToolStatusRequest(uuid="actor-uuid")

        # Mock _wait_for_catalog_update to simulate timeout
        original_wait_for_catalog_update = actor._wait_for_catalog_update

        async def mock_wait_for_catalog_update(uuid: str, timeout: float = 0.5):
            await asyncio.sleep(timeout)
            raise asyncio.TimeoutError()

        actor._wait_for_catalog_update = mock_wait_for_catalog_update

        response = await actor.tool_status(request)

        assert isinstance(response, ToolStatusResponse)
        assert response.uuid == actor.uuid

        # Cleanup
        actor._wait_for_catalog_update = original_wait_for_catalog_update

    async def test_wait_for_catalog_update_update_happens(self):
        actor = BaseActor()
        actor.uuid = "actor-uuid"

        wait_task = asyncio.create_task(actor._wait_for_catalog_update("actor-uuid", timeout=1.0))

        # Simulate catalog update after 0.1 second
        await asyncio.sleep(0.1)
        actor.uuid = "new-actor-uuid"

        await wait_task

        assert True

    async def test_wait_for_catalog_update_timeout(self):
        actor = BaseActor()
        actor.uuid = "actor-uuid"

        wait_task = asyncio.create_task(actor._wait_for_catalog_update("actor-uuid", timeout=0.5))

        with pytest.raises(asyncio.TimeoutError):
            await wait_task
