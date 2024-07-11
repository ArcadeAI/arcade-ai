import asyncio

import pytest

from arcade.sdk.tool import tool


def test_sync_function():
    """
    Ensures a function will run when decorated by @tool
    """

    @tool
    def sync_func(x, y):
        return x + y

    result = sync_func(1, 2)
    assert result == 3


@pytest.mark.asyncio
async def test_async_function():
    """
    Ensures an async function will run when decorated by @tool
    """

    @tool
    async def async_func(x, y):
        await asyncio.sleep(0)
        return x + y

    result = await async_func(1, 2)
    assert result == 3


def test_tool_decorator_with_name_and_description():
    @tool(name="TestTool", description="Test description")
    def test_tool(x, y):
        return x + y

    assert test_tool.__tool_name__ == "TestTool"
    assert test_tool.__tool_description__ == "Test description"