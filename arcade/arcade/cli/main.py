import asyncio
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from typer.core import TyperGroup
from typer.models import Context


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context):
        """Return list of commands in the order appear."""
        return list(self.commands)  # get commands using self.commands


console = Console()
cli = typer.Typer(
    cls=OrderCommands,
)


@cli.command(help="Log in to Arcade Cloud")
def login(
    username: str = typer.Option(..., prompt="Username", help="Your Arcade Cloud username"),
    api_key: str = typer.Option(None, prompt="API Key", help="Your Arcade Cloud API Key"),
):
    """
    Logs the user into Arcade Cloud.
    """
    # Here you would add the logic to authenticate the user with Arcade Cloud
    pass


@cli.command(help="Create a new toolkit package directory")
def new(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path"),
):
    """
    Creates a new toolkit with the given name, description, and result type.
    """
    from arcade.cli.new import create_new_toolkit

    try:
        create_new_toolkit(directory)
    except Exception as e:
        error_message = f"❌ Failed to create new Toolkit: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Show the available tools in an actor or toolkit directory")
def show(
    toolkit: str = typer.Argument(..., help="The toolkit to show the tools of"),
    actor: str = typer.Option(
        "http://localhost:8000", help="A running actor address to list tools from"
    ),
):
    """
    Show the available tools in an actor or toolkit
    """

    from arcade.core.catalog import ToolCatalog
    from arcade.core.toolkit import Toolkit

    try:
        # load the toolkit from python package
        loaded_toolkit = Toolkit.from_package(toolkit)

        # create a tool catalog and add the toolkit
        catalog = ToolCatalog()
        catalog.add_toolkit(loaded_toolkit)

        # Create a table with Rich library
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Description")
        table.add_column("Toolkit")
        table.add_column("Version")

        for tool in catalog:
            table.add_row(tool.name, tool.description, tool.meta.toolkit, tool.version)

        console.print(table)

    except Exception as e:
        # better error message here
        error_message = f"❌ Failed to List tools: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Run a tool using an LLM to predict the arguments")
def run(
    toolkit: str = typer.Argument(..., help="The toolkit to add to model calls"),
    prompt: str = typer.Argument(..., help="The prompt to use for context"),
    model: str = typer.Option("gpt-3.5-turbo", "-m", help="The model to use for prediction."),
    tool: str = typer.Option(None, "-t", "--tool", help="The name of the tool to run."),
    choice: str = typer.Option(
        "required", "-c", "--choice", help="The value of the tool choice argument"
    ),
    actor: Optional[str] = typer.Option(
        None, "-a", "--actor", help="The actor to use for prediction."
    ),
):
    """
    Run a tool using an LLM to predict the arguments.
    """
    from arcade.core.catalog import ToolCatalog
    from arcade.core.client import EngineClient
    from arcade.core.executor import ToolExecutor
    from arcade.core.toolkit import Toolkit

    try:
        # load the toolkit from python package
        loaded_toolkit = Toolkit.from_package(toolkit)

        # create a tool catalog and add the toolkit
        catalog = ToolCatalog()
        catalog.add_toolkit(loaded_toolkit)

        # if user specified a tool
        if tool:
            # check if the tool is in the catalog/toolkit
            if tool not in catalog:
                console.print(f"❌ Tool not found in toolkit: {toolkit}", style="bold red")
                raise typer.Exit(code=1)
            else:
                tools = [catalog[tool]]
        else:
            # use all the tools in the catalog
            tools = list(catalog)

        if catalog.is_empty():
            console.print(f"❌ No tools found in toolkit: {toolkit}", style="bold red")
            raise typer.Exit(code=1)

        # TODO put in the engine url from config
        client = EngineClient()
        calls = client.call_tool(tools, tool_choice=choice, prompt=prompt, model=model)

        messages = [
            {"role": "user", "content": prompt},
        ]

        for tool_name, parameters in calls.items():
            called_tool = catalog[tool_name]
            console.print(f"Running tool: {tool_name} with params: {parameters}", style="bold blue")

            output = asyncio.run(
                ToolExecutor.run(
                    called_tool.tool,
                    called_tool.input_model,
                    called_tool.output_model,
                    **parameters,
                )
            )
            if output.code != 200:
                console.print(output.msg, style="bold red")
                if output.data:
                    console.print(output.data.result, style="bold red")
            else:
                # TODO: Add the tool results to the response in a safer way
                messages += [
                    {
                        "role": "assistant",
                        "content": f"Results of Tool {tool_name}: {str(output.data.result)}",
                    },
                ]
            response = client.complete(model=model, messages=messages)
            console.print(response.choices[0].message.content, style="bold green")

    except RuntimeError as e:
        error_message = f"❌ Failed to run tool{': '+ escape(str(e)) if str(e) else ''}"
        console.print(error_message, style="bold red")


@cli.command(help="Execute eval suite wthin /evals")
def evals(
    module: str = typer.Option(..., help="The name of the module to run evals on"),
):
    """
    Execute eval suite wthin /evals
    """
    pass


@cli.command(help="Manage the Arcade Engine (start/stop/restart)")
def engine(
    action: str = typer.Argument("start", help="The action to take (start/stop/restart)"),
    host: str = typer.Option("localhost", "--host", "-h", help="The host of the engine"),
    port: int = typer.Option(6901, "--port", "-p", help="The port of the engine"),
):
    """
    Manage the Arcade Engine (start/stop/restart)
    """
    pass


@cli.command(help="Manage credientials stored in the Arcade Engine")
def credentials(
    action: str = typer.Argument("show", help="The action to take (add/remove/show)"),
    name: str = typer.Option(None, "--name", "-n", help="The name of the credential to add/remove"),
    val: str = typer.Option(None, "--val", "-v", help="The value of the credential to add/remove"),
):
    """
    Manage credientials stored in the Arcade Engine
    """
    pass


@cli.command(help="Show/edit configuration details of the Arcade Engine")
def config(
    action: str = typer.Argument("show", help="The action to take (show/edit)"),
    name: str = typer.Option(None, "--name", "-n", help="The name of the configuration to edit"),
    val: str = typer.Option(None, "--val", "-v", help="The value of the configuration to edit"),
):
    """
    Show/edit configuration details of the Arcade Engine
    """
    pass
