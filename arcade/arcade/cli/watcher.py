import asyncio
import threading

from loguru import logger

from arcade.actor.fastapi.actor import FastAPIActor
from arcade.core.schema import FullyQualifiedName
from arcade.core.toolkit import Toolkit


class ToolkitWatcher:
    def __init__(
        self,
        initial: list[Toolkit],
        actor: FastAPIActor,
        shutdown_event: threading.Event,
    ):
        self.current_tools: list[FullyQualifiedName] = self._list_tools(initial)
        self.actor = actor
        self.shutdown_event = shutdown_event

    async def start(self, interval: int = 1) -> None:
        while not self.shutdown_event.is_set():
            try:
                new_toolkits = Toolkit.find_all_arcade_toolkits()
                new_tools = self._list_tools(new_toolkits)
                if new_tools != self.current_tools:
                    logger.info("Toolkit changes detected. Updating actor's catalog...")

                    for tool in new_tools:
                        if tool not in self.current_tools:
                            logger.info(f"New tool added:  {tool}")

                    for tool in self.current_tools:
                        if tool not in new_tools:
                            logger.info(f"Toolkit removed: {tool}")

                    self.actor.clear_catalog()
                    for toolkit in new_toolkits:
                        self.actor.register_toolkit(toolkit)

                    self.current_tools = new_tools

                    logger.info("Actor's catalog has been updated.")
                else:
                    pass

            except Exception:
                logger.exception("Error while polling toolkits")

            await asyncio.sleep(interval)

    def _list_tools(self, toolkits: list[Toolkit]) -> list[FullyQualifiedName]:
        tools_list = []
        for toolkit in toolkits:
            for _, tools in toolkit.tools.items():
                if len(tools) != 0:
                    tools_list.extend([
                        FullyQualifiedName(tool, toolkit.name, toolkit.version) for tool in tools
                    ])
        return tools_list
