import importlib.util
import os
import readline
import threading
import uuid
import webbrowser
from typing import Any, Optional
from urllib.parse import urlencode

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from arcade.cli.authn import LocalAuthCallbackServer, check_existing_login
from arcade.cli.utils import (
    OrderCommands,
    apply_config_overrides,
    create_cli_catalog,
    display_streamed_markdown,
    markdownify_urls,
    validate_and_get_config,
)
from arcade.client import Arcade
from arcade.client.errors import EngineNotHealthyError, EngineOfflineError

cli = typer.Typer(
    cls=OrderCommands,
)
console = Console()


@cli.command(help="Log in to Arcade Cloud")
def login(
    host: str = typer.Option(
        "https://cloud.arcade-ai.com",
        "-h",
        "--host",
        help="The Arcade Cloud host to log in to.",
    ),
) -> None:
    """
    Logs the user into Arcade Cloud.
    """

    if check_existing_login():
        return

    # Start the HTTP server in a new thread
    state = str(uuid.uuid4())
    auth_server = LocalAuthCallbackServer(state)
    server_thread = threading.Thread(target=auth_server.run_server)
    server_thread.start()

    try:
        # Open the browser for user login
        callback_uri = "http://localhost:9905/callback"
        params = urlencode({"callback_uri": callback_uri, "state": state})
        login_url = f"https://{host}/api/v1/auth/cli_login?{params}"
        console.print("Opening a browser to log you in...")
        webbrowser.open(login_url)

        # Wait for the server thread to finish
        server_thread.join()
    except KeyboardInterrupt:
        auth_server.shutdown_server()
    finally:
        if server_thread.is_alive():
            server_thread.join()  # Ensure the server thread completes and cleans up


@cli.command(help="Log out of Arcade Cloud")
def logout() -> None:
    """
    Logs the user out of Arcade Cloud.
    """

    # If ~/.arcade/arcade.toml exists, delete it
    config_file_path = os.path.expanduser("~/.arcade/arcade.toml")
    if os.path.exists(config_file_path):
        os.remove(config_file_path)
        console.print("You're now logged out.", style="bold")
    else:
        console.print("You're not logged in.", style="bold red")


@cli.command(help="Create a new toolkit package directory")
def new(
    directory: str = typer.Option(os.getcwd(), "--dir", help="tools directory path"),
) -> None:
    """
    Creates a new toolkit with the given name, description, and result type.
    """
    from arcade.cli.new import create_new_toolkit

    try:
        create_new_toolkit(directory)
    except Exception as e:
        error_message = f"❌ Failed to create new Toolkit: {escape(str(e))}"
        console.print(error_message, style="bold red")


@cli.command(help="Show the available tools in an actor or toolkit directory")
def show(
    toolkit: Optional[str] = typer.Option(
        None, "-t", "--toolkit", help="The toolkit to show the tools of"
    ),
    actor: Optional[str] = typer.Option(None, help="A running actor address to list tools from"),
) -> None:
    """
    Show the available tools in an actor or toolkit
    """

    try:
        catalog = create_cli_catalog(toolkit=toolkit)

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


@cli.command(help="Chat with a language model")
def chat(
    model: str = typer.Option("gpt-4o", "-m", help="The model to use for prediction."),
    stream: bool = typer.Option(
        False, "-s", "--stream", is_flag=True, help="Stream the tool output."
    ),
    host: str = typer.Option(
        None,
        "-h",
        "--host",
        help="The Arcade Engine address to send chat requests to.",
    ),
    port: int = typer.Option(
        None,
        "-p",
        "--port",
        help="The port of the Arcade Engine.",
    ),
    force_tls: bool = typer.Option(
        False,
        "--tls",
        help="Whether to force TLS for the connection to the Arcade Engine. If not specified, the connection will use TLS if the engine URL uses a 'https' scheme.",
    ),
    force_no_tls: bool = typer.Option(
        False,
        "--no-tls",
        help="Whether to disable TLS for the connection to the Arcade Engine.",
    ),
) -> None:
    """
    Chat with a language model.
    """
    config = validate_and_get_config()

    if not force_tls and not force_no_tls:
        tls_input = None
    elif force_no_tls:
        tls_input = False
    else:
        tls_input = True
    apply_config_overrides(config, host, port, tls_input)

    client = Arcade(api_key=config.api.key, base_url=config.engine_url)
    user_email = config.user.email if config.user else None
    user_attribution = f"({user_email})" if user_email else ""

    try:
        # start messages conversation
        messages: list[dict[str, Any]] = []

        chat_header = Text.assemble(
            "\n",
            (
                "=== Arcade AI Chat ===",
                "bold magenta underline",
            ),
            "\n",
            "\n",
            "Chatting with Arcade Engine at ",
            (
                config.engine_url,
                "bold blue",
            ),
        )
        console.print(chat_header)

        # Try to hit /health endpoint on engine and warn if it is down
        log_engine_health(client)

        while True:
            console.print(f"\n[magenta][bold]User[/bold] {user_attribution}:[/magenta] ")

            # Use input() instead of console.input() to leverage readline history
            user_input = input()

            # Add the input to history
            readline.add_history(user_input)

            messages.append({"role": "user", "content": user_input})

            if stream:
                # TODO Fix this in the client so users don't deal with these
                # typing issues
                stream_response = client.chat.completions.create(  # type: ignore[call-overload]
                    model=model,
                    messages=messages,
                    tool_choice="generate",
                    user=user_email,
                    stream=True,
                )
                role, message_content = display_streamed_markdown(stream_response, model)
            else:
                response = client.chat.completions.create(  # type: ignore[call-overload]
                    model=model,
                    messages=messages,
                    tool_choice="generate",
                    user=user_email,
                    stream=False,
                )
                message_content = response.choices[0].message.content or ""
                role = response.choices[0].message.role

                if role == "assistant":
                    message_content = markdownify_urls(message_content)
                    console.print(
                        f"\n[bold blue]Assistant ({model}):[/bold blue] ", Markdown(message_content)
                    )
                else:
                    console.print(f"\n[bold magenta]{role}:[/bold magenta] {message_content}")

            messages.append({"role": role, "content": message_content})

    except KeyboardInterrupt:
        console.print("Chat stopped by user.", style="bold blue")
        typer.Exit()

    except RuntimeError as e:
        error_message = f"❌ Failed to run tool{': ' + escape(str(e)) if str(e) else ''}"
        console.print(error_message, style="bold red")
        raise typer.Exit()


@cli.command(help="Start an Actor server with specified configurations.")
def dev(
    host: str = typer.Option(
        "127.0.0.1", help="Host for the app, from settings by default.", show_default=True
    ),
    port: int = typer.Option(
        "8000", "-p", "--port", help="Port for the app, defaults to ", show_default=True
    ),
    disable_auth: bool = typer.Option(
        False,
        "--no-auth",
        help="Disable authentication for the actor. Not recommended for production.",
        show_default=True,
    ),
) -> None:
    """
    Starts the actor with host, port, and reload options. Uses
    Uvicorn as ASGI actor. Parameters allow runtime configuration.
    """

    if disable_auth:
        console.print(
            "⚠️ Actor authentication is disabled. Not recommended for production.",
            style="bold yellow",
        )

    from arcade.cli.serve import serve_default_actor

    try:
        serve_default_actor(host, port, disable_auth)
    except KeyboardInterrupt:
        console.print("actor stopped by user.", style="bold red")
        typer.Exit()
    except Exception as e:
        error_message = f"❌ Failed to start Arcade Actor: {escape(str(e))}"
        console.print(error_message, style="bold red")
        raise typer.Exit(code=1)


@cli.command(help="Show/edit configuration details of the Arcade Engine")
def config(
    action: str = typer.Argument("show", help="The action to take (show/edit)"),
    key: str = typer.Option(
        None, "--key", "-k", help="The configuration key to edit (e.g., 'api.key')"
    ),
    val: str = typer.Option(None, "--val", "-v", help="The value of the configuration to edit"),
) -> None:
    """
    Show/edit configuration details of the Arcade Engine
    """
    config = validate_and_get_config()

    if action == "show":
        display_config_as_table(config)
    elif action == "edit":
        if not key or val is None:
            console.print("❌ Key and value must be provided for editing.", style="bold red")
            raise typer.Exit(code=1)

        keys = key.split(".")
        if len(keys) != 2:
            console.print("❌ Invalid key format. Use 'section.name' format.", style="bold red")
            raise typer.Exit(code=1)

        section, name = keys
        section_dict = getattr(config, section, None)
        if section_dict and hasattr(section_dict, name):
            setattr(section_dict, name, val)
            config.save_to_file()
            console.print("✅ Configuration updated successfully.", style="bold green")
        else:
            console.print(
                f"❌ Invalid configuration name: {name} in section: {section}", style="bold red"
            )
            raise typer.Exit(code=1)
    else:
        console.print(f"❌ Invalid action: {action}", style="bold red")
        raise typer.Exit(code=1)


def log_engine_health(client: Arcade) -> None:
    try:
        client.health.check()

    except EngineNotHealthyError as e:
        console.print(
            "[bold][yellow]⚠️ Warning: "
            + str(e)
            + " ("
            + "[/yellow]"
            + "[red]"
            + str(e.status_code)
            + "[/red]"
            + "[yellow])[/yellow][/bold]"
        )
    except EngineOfflineError:
        console.print(
            "⚠️ Warning: Arcade Engine was unreachable. (Is it running?)",
            style="bold yellow",
        )


def display_config_as_table(config) -> None:  # type: ignore[no-untyped-def]
    """
    Display the configuration details as a table using Rich library.
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Section")
    table.add_column("Name")
    table.add_column("Value")

    for section_name in config.model_dump():
        section = getattr(config, section_name)
        if section:
            section = section.dict()
            first = True
            for name, value in section.items():
                if first:
                    table.add_row(section_name, name, str(value))
                    first = False
                else:
                    table.add_row("", name, str(value))
            table.add_row("", "", "")

    console.print(table)


@cli.command(help="Run evaluation suites in a directory")
def evals(
    directory: str = typer.Argument(".", help="Directory containing evaluation files"),
    show_details: bool = typer.Option(False, "--details", "-d", help="Show detailed results"),
):
    """
    Finds all files starting with 'eval_' in the given directory,
    executes any functions decorated with @tool_eval, and displays the results.
    """
    eval_files = [f for f in os.listdir(directory) if f.startswith("eval_") and f.endswith(".py")]

    if not eval_files:
        console.print("No evaluation files found.", style="bold yellow")
        return

    for file in eval_files:
        file_path = os.path.join(directory, file)
        module_name = file[:-3]  # Remove .py extension

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        eval_functions = [
            obj
            for name, obj in module.__dict__.items()
            if callable(obj) and hasattr(obj, "__tool_eval__")
        ]

        if not eval_functions:
            console.print(f"No @tool_eval functions found in {file}", style="bold yellow")
            continue

        for func in eval_functions:
            console.print(f"\nRunning evaluation from {file}: {func.__name__}", style="bold blue")
            results = func()
            display_eval_results(results, show_details=show_details)


def display_eval_results(results: list[dict[str, Any]], show_details: bool = False) -> None:
    """
    Display evaluation results in a more readable format with color-coded matches.

    Args:
        results: List of dictionaries containing evaluation results for each model.
        show_details: Whether to show detailed results for each case.
    """
    for model_results in results:
        model = model_results.get("model", "Unknown Model")
        cases = model_results.get("cases", [])

        table = Table(
            title=f"Evaluation Results for {model}", show_header=True, header_style="bold magenta"
        )
        table.add_column("Case", style="cyan", no_wrap=True)
        table.add_column("Expected Tool", style="green")
        table.add_column("Predicted Tool", style="yellow")
        table.add_column("Score", justify="right")
        table.add_column("Status", justify="center")

        for case in cases:
            status = "✅" if case["evaluation"]["pass"] else "❌"
            if case["evaluation"].get("warning"):
                status = "⚠️"

            table.add_row(
                case["input"][:30] + "..." if len(case["input"]) > 30 else case["input"],
                case["expected_tool"],
                case["predicted_tool"],
                f"{case['evaluation']['score']:.2f}",
                status,
            )

        console.print(table)

        if not show_details:
            continue

        # Display detailed results in a panel
        for case in cases:
            detailed_results = (
                f"[bold]Case:[/bold] {case['input']}\n\n"
                f"[bold]Expected Tool:[/bold] {case['expected_tool']}\n"
                f"[bold]Predicted Tool:[/bold] {case['predicted_tool']}\n\n"
                f"[bold]Expected Args:[/bold]\n{format_args(case['expected_args'])}\n"
                f"[bold]Predicted Args:[/bold]\n{format_args(case['predicted_args'])}\n\n"
                f"[bold]Evaluation:[/bold]\n{format_evaluation(case['evaluation'])}\n"
            )
            console.print(Panel(detailed_results, title="Detailed Results", expand=False))


def format_args(args: dict[str, Any]) -> str:
    """Format argument dictionary for display."""
    return "\n".join(f"  {k}: {v}" for k, v in args.items())


def format_evaluation(evaluation: dict[str, Any]) -> str:
    """
    Format evaluation results with color-coded matches and accurate score ranges.

    Args:
        evaluation: A dictionary containing evaluation results.

    Returns:
        A formatted string representation of the evaluation results.
    """
    result = []
    result.append(f"  Overall Score: {evaluation['score']:.2f}")

    # Determine and add the overall result status
    if evaluation["pass"]:
        result.append("  [green]Result: Pass[/green]")
        # Early return if passed, skipping detailed results
        # TODO: Make this optional
        return "\n".join(result)
    elif evaluation.get("warning"):
        result.append("  [yellow]Result: Warning[/yellow]")
    elif evaluation.get("fail"):
        result.append("  [red]Result: Fail[/red]")
    else:
        result.append("  [bold red]Result: Unknown[/bold red]")

    # Add critic results header if we didn't pass
    result.append("\n[bold]Critic Results:[/bold]")

    # Process each critic result
    for critic in evaluation.get("critic_results", []):
        match_color = "green" if critic.get("match") else "red"
        weight = critic.get("weight", 1.0)
        max_score = critic.get("max_score", 1.0)
        field = critic.get("field", "Unknown")

        critic_result = (
            f"  [bold]{field}:[/bold] "
            f"[{match_color}]"
            f"Match: {critic.get('match', False)}, "
            f"Score: {critic.get('score', 0):.2f}/{max_score:.2f} "
            f"(Weight: {weight:.2f})"
            f"[/{match_color}]"
        )
        result.append(critic_result)

    return "\n".join(result)
