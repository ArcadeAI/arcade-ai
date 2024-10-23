import asyncio
import threading
import unittest
from unittest.mock import MagicMock, patch

from arcade.actor.fastapi.actor import FastAPIActor
from arcade.cli.watcher import FullyQualifiedName, ToolkitWatcher
from arcade.core.toolkit import Toolkit


class TestToolkitWatcher(unittest.IsolatedAsyncioTestCase):
    async def test_start_detects_toolkit_changes(self):
        # Setup initial toolkits
        initial_toolkit = MagicMock(spec=Toolkit)
        initial_toolkit.name = "Toolkit1"
        initial_toolkit.version = "1.0.0"
        initial_toolkit.tools = {"group1": ["ToolA"]}
        initial = [initial_toolkit]

        # Mock actor
        actor = MagicMock(spec=FastAPIActor)
        actor.register_toolkit = MagicMock()
        actor.clear_catalog = MagicMock()

        # Create shutdown event
        shutdown_event = threading.Event()

        # Instantiate ToolkitWatcher
        watcher = ToolkitWatcher(initial=initial, actor=actor, shutdown_event=shutdown_event)

        # Mock Toolkit.find_all_arcade_toolkits to return updated toolkits on the second call
        updated_toolkit = MagicMock(spec=Toolkit)
        updated_toolkit.name = "Toolkit1"
        updated_toolkit.version = "1.0.1"
        updated_toolkit.tools = {"group1": ["ToolA", "ToolB"]}

        with patch(
            "arcade.core.toolkit.Toolkit.find_all_arcade_toolkits",
            side_effect=[initial, [updated_toolkit], []],
        ):
            # Run watcher.start() in background
            async def run_watcher():
                await watcher.start(interval=0.5)

            watcher_task = asyncio.create_task(run_watcher())

            # Allow some time for the watcher to process
            await asyncio.sleep(0.7)

            # Trigger shutdown to stop the watcher
            shutdown_event.set()

            # Await the watcher task to finish
            await watcher_task

            # Assertions
            actor.clear_catalog.assert_called()
            actor.register_toolkit.assert_called_with(updated_toolkit)

            # Check that current_tools has been updated
            expected_tools = [
                FullyQualifiedName("ToolA", "Toolkit1", "1.0.1"),
                FullyQualifiedName("ToolB", "Toolkit1", "1.0.1"),
            ]
            self.assertEqual(watcher.current_tools, expected_tools)

    async def test_start_no_changes(self):
        # Setup initial toolkits
        initial_toolkit = MagicMock(spec=Toolkit)
        initial_toolkit.name = "Toolkit1"
        initial_toolkit.version = "1.0.0"
        initial_toolkit.tools = {"group1": ["ToolA"]}
        initial = [initial_toolkit]

        # Mock actor
        actor = MagicMock(spec=FastAPIActor)
        actor.register_toolkit = MagicMock()
        actor.clear_catalog = MagicMock()

        # Create shutdown event
        shutdown_event = threading.Event()

        # Instantiate ToolkitWatcher
        watcher = ToolkitWatcher(initial=initial, actor=actor, shutdown_event=shutdown_event)

        # Mock Toolkit.find_all_arcade_toolkits to always return the initial toolkit
        with patch("arcade.core.toolkit.Toolkit.find_all_arcade_toolkits", return_value=initial):
            # Run watcher.start() in background
            async def run_watcher():
                await watcher.start(interval=0.1)

            watcher_task = asyncio.create_task(run_watcher())

            # Allow some time for the watcher to process
            await asyncio.sleep(0.3)

            # Trigger shutdown to stop the watcher
            shutdown_event.set()

            # Await the watcher task to finish
            await watcher_task

            # Assert that actor.clear_catalog was never called since there were no changes
            actor.clear_catalog.assert_not_called()
            actor.register_toolkit.assert_not_called()

    async def test_start_handles_exception(self):
        # Setup initial toolkits
        initial_toolkit = MagicMock(spec=Toolkit)
        initial_toolkit.name = "Toolkit1"
        initial_toolkit.version = "1.0.0"
        initial_toolkit.tools = {"group1": ["ToolA"]}
        initial = [initial_toolkit]

        # Mock actor
        actor = MagicMock(spec=FastAPIActor)
        actor.register_toolkit = MagicMock()
        actor.clear_catalog = MagicMock()

        # Create shutdown event
        shutdown_event = threading.Event()

        # Instantiate ToolkitWatcher
        watcher = ToolkitWatcher(initial=initial, actor=actor, shutdown_event=shutdown_event)

        # Mock Toolkit.find_all_arcade_toolkits to raise an exception
        with patch(
            "arcade.core.toolkit.Toolkit.find_all_arcade_toolkits",
            side_effect=Exception("Test Exception"),
        ):
            # Run watcher.start() in background
            async def run_watcher():
                await watcher.start(interval=0.1)

            watcher_task = asyncio.create_task(run_watcher())

            # Allow some time for the watcher to process
            await asyncio.sleep(0.3)

            # Trigger shutdown to stop the watcher
            shutdown_event.set()

            # Await the watcher task to finish
            await watcher_task

            # Since the exception is caught and logged, we can check that it does not crash
            # Assert that actor.clear_catalog was never called
            actor.clear_catalog.assert_not_called()


if __name__ == "__main__":
    unittest.main()
