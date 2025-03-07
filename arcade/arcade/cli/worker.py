import requests
import typer
from arcadepy import Arcade
from arcadepy.resources.worker import WorkerListResponse
from rich.console import Console
from rich.table import Table

from arcade.cli.utils import (
    OrderCommands,
    validate_and_get_config,
)
from arcade.core.config_model import Config

console = Console()


app = typer.Typer(
    cls=OrderCommands,
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
)

domains = {
    "prod": {
        "cloud": "https://cloud.arcade.dev",
        "api": "https://api.arcade.dev",
    },
    "dev": {
        "cloud": "https://cloud.bosslevel.dev",
        "api": "https://api.bosslevel.dev",
    },
    "local": {
        "cloud": "http://localhost:8001",
        "api": "http://localhost:9099",
    },
}


@app.command("list", help="List all workers")
def list_workers() -> None:
    config = validate_and_get_config()

    arcade = Arcade(api_key=config.api.key, base_url="http://localhost:9099")
    workers = arcade.worker.list()

    print_worker_table(workers, config)


def print_worker_table(workers: WorkerListResponse, config: Config) -> None:
    if not workers.items:
        console.print("No workers found", style="bold red")
        return

    table = Table(title="Workers")
    table.add_column("ID")
    table.add_column("Enabled")
    table.add_column("Host")
    table.add_column("Toolkits")
    for worker in workers.items:
        response = requests.get(
            f"http://localhost:9099/v1/admin/workers/{worker.id}/tools",
            headers={"Authorization": f"Bearer {config.api.key}"},
            timeout=60,
        )
        table.add_row(
            worker.id,
            str(worker.enabled),
            worker.http.uri if worker.http else "",
            "Cannot get toolkits from disabled workers"
            if not worker.enabled
            else ", ".join(get_toolkits(response.json())),
        )
    console.print(table)


def parse_deployment_response(response: dict) -> str:
    additions = response["data"]["changes"]["additions"] or []
    removals = response["data"]["changes"]["removals"] or []
    no_changes = response["data"]["changes"]["no_changes"] or []
    print_deployment_table(additions, removals, no_changes)
    return str(response["data"]["worker_endpoint"])


def print_deployment_table(additions: list, removals: list, no_changes: list) -> None:
    table = Table(title="Changed Packages")
    table.add_column("Added", justify="right", style="green")
    table.add_column("Removed", justify="right", style="red")
    table.add_column("Updated", justify="right", style="yellow")
    table.add_column("No Changes", justify="right", style="dim")
    max_rows = max(len(additions), len(removals), len(no_changes))
    for i in range(max_rows):
        addition = additions[i] if i < len(additions) else ""
        removal = removals[i] if i < len(removals) else ""
        no_change = no_changes[i] if i < len(no_changes) else ""
        table.add_row(addition, removal, "", no_change)
        console.print(table)


@app.command("enable", help="Enable a worker")
def enable_worker(worker_id: str) -> None:
    config = validate_and_get_config()
    arcade = Arcade(api_key=config.api.key, base_url="http://localhost:9099")
    arcade.worker.update(worker_id, enabled=True)


@app.command("disable", help="Disable a worker")
def disable_worker(worker_id: str) -> None:
    config = validate_and_get_config()
    arcade = Arcade(api_key=config.api.key, base_url="http://localhost:9099")
    arcade.worker.update(worker_id, enabled=False)


def get_toolkits(tools: dict) -> list[str]:
    toolkits: list[str] = []
    for tool in tools["items"]:
        if tool["toolkit"]["name"] not in toolkits:
            toolkits.append(tool["toolkit"]["name"])
    return toolkits
