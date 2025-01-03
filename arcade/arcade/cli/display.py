from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from arcade.core.schema import ToolDefinition

if TYPE_CHECKING:
    from arcade.sdk.eval.eval import EvaluationResult
console = Console()


def display_tools_table(tools: list[ToolDefinition]) -> None:
    """
    Display a table of tools with their name, description, package, and version.
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Package")
    table.add_column("Version")

    for tool in sorted(tools, key=lambda x: x.toolkit.name):
        table.add_row(
            str(tool.get_fully_qualified_name()),
            tool.description.split("\n")[0] if tool.description else "",
            tool.toolkit.name,
            tool.toolkit.version,
        )
    console.print(f"Found {len(tools)} tools.")
    console.print(table)


def display_tool_details(tool: ToolDefinition) -> None:
    """
    Display detailed information about a specific tool using multiple panels.
    """
    # Description Panel
    description_panel = Panel(
        tool.description or "No description available.",
        title=f"Tool: {tool.name}",
        border_style="cyan",
    )

    # Inputs Panel
    inputs = tool.inputs.parameters
    if inputs:
        inputs_table = Table(show_header=True, header_style="bold green")
        inputs_table.add_column("Name", style="cyan")
        inputs_table.add_column("Type", style="magenta")
        inputs_table.add_column("Required", style="yellow")
        inputs_table.add_column("Description", style="white")
        inputs_table.add_column("Default", style="blue")
        for param in inputs:
            # Since InputParameter does not have a default field, we use "N/A"
            default_value = "N/A"
            if param.value_schema.enum:
                default_value = f"One of {param.value_schema.enum}"
            inputs_table.add_row(
                param.name,
                param.value_schema.val_type,
                str(param.required),
                param.description or "",
                default_value,
            )
        inputs_panel = Panel(
            inputs_table,
            title="Input Parameters",
            border_style="green",
        )
    else:
        inputs_panel = Panel(
            "No input parameters.",
            title="Input Parameters",
            border_style="green",
        )

    # Output Panel
    output = tool.output
    if output:
        output_description = output.description or "No description available."
        output_types = ", ".join(output.available_modes)
        output_val_type = output.value_schema.val_type if output.value_schema else "N/A"
        output_details = Text.assemble(
            ("Description: ", "bold"),
            (output_description, ""),
            "\n",
            ("Available Modes: ", "bold"),
            (output_types, ""),
            "\n",
            ("Value Type: ", "bold"),
            (output_val_type, ""),
        )
        output_panel = Panel(
            output_details,
            title="Expected Output",
            border_style="blue",
        )
    else:
        output_panel = Panel(
            "No output information available.",
            title="Expected Output",
            border_style="blue",
        )

    # Combine all panels vertically
    console.print(description_panel)
    console.print(inputs_panel)
    console.print(output_panel)


def display_tool_messages(tool_messages: list[dict]) -> None:
    for message in tool_messages:
        if message["role"] == "assistant":
            for tool_call in message.get("tool_calls", []):
                console.print(
                    f"[bold]Called tool '{tool_call['function']['name']}' with parameters:[/bold] {tool_call['function']['arguments']}",
                    style="dim",
                )
        elif message["role"] == "tool":
            console.print(
                f"[bold]'{message['name']}' tool returned:[/bold] {message['content']}", style="dim"
            )


def display_eval_results(  # noqa: C901
    results: list[tuple[str, list[dict[str, Any]]]], show_details: bool = False
) -> None:
    """
    Display evaluation results in a format inspired by pytest's output.

    Args:
        results: List of tuples containing suite name and evaluation results for each model.
        show_details: Whether to show detailed results for each case.
    """
    total_passed = 0
    total_failed = 0
    total_warned = 0
    total_cases = 0
    total_score = 0

    model_averages = []  # List to store average scores for each model

    for suite_name, suite_result in results:
        for model_results in suite_result:
            model = model_results.get("model", "Unknown Model")
            rubric = model_results.get("rubric", "Unknown Rubric")
            cases = model_results.get("cases", [])
            total_cases += len(cases)

            # Initialize model-specific score tracking
            model_total_score = 0
            model_total_cases = len(cases)
            model_passed = 0
            model_failed = 0

            console.print(f"[bold]Model:[/bold] [bold magenta]{model}[/bold magenta]")
            if show_details:
                console.print(f"[bold magenta]{rubric}[/bold magenta]")

            for case in cases:
                evaluation = case["evaluation"]
                status = (
                    "[green]PASSED[/green]"
                    if evaluation.passed
                    else "[yellow]WARNED[/yellow]"
                    if evaluation.warning
                    else "[red]FAILED[/red]"
                )
                if evaluation.passed:
                    total_passed += 1
                    model_passed += 1
                elif evaluation.warning:
                    total_warned += 1
                else:
                    total_failed += 1
                    model_failed += 1

                total_score += evaluation.score
                model_total_score += evaluation.score

                # Display one-line summary for each case with score as a percentage
                score_percentage = evaluation.score * 100
                console.print(f"{status} {case['name']} -- Score: {score_percentage:.2f}%")

                if show_details:
                    # Show detailed information for each case
                    console.print(f"[bold]User Input:[/bold] {case['input']}\n")
                    console.print("[bold]Details:[/bold]")
                    console.print(_format_evaluation(evaluation))
                    console.print("-" * 80)

            # Calculate the average score for the current model
            model_average_score_percentage = (
                (model_total_score / model_total_cases) * 100 if model_total_cases > 0 else 0
            )
            model_averages.append((
                suite_name,
                model,
                model_average_score_percentage,
                model_total_cases,
                model_passed,
                model_failed,
            ))

    # Display results for each model only if there is more than one model
    console.print("\n[bold]Model Results:[/bold]\n" + "-" * 40)
    for (
        suite_name,
        model,
        avg_score,
        model_total_cases,
        model_passed,
        model_failed,
    ) in model_averages:
        console.print(
            f"[blue]{suite_name} {model} Results:[/blue]\n"
            f"  Total: {model_total_cases}\n"
            f"  Passed: {model_passed}\n"
            f"  Failed: {model_failed}\n"
            f"  Average Score: {avg_score:.2f}%\n" + "-" * 40
        )

    # Calculate average score percentage
    average_score_percentage = (total_score / total_cases) * 100 if total_cases > 0 else 0

    # Summary
    summary = (
        f"\n[bold]Summary:[/bold]\n"
        f"  Total: {total_cases}\n"
        f"  [green]Passed: {total_passed}[/green]\n"
    )
    if total_warned > 0:
        summary += f"  [yellow]Warnings: {total_warned}[/yellow]\n"
    if total_failed > 0:
        summary += f"  [red]Failed: {total_failed}[/red]\n"
    summary += f"  [blue]Average Score: {average_score_percentage:.2f}%[/blue]\n"
    console.print(summary)


def _format_evaluation(evaluation: "EvaluationResult") -> str:
    """
    Format evaluation results with color-coded matches and scores.

    Args:
        evaluation: An EvaluationResult object containing the evaluation results.

    Returns:
        A formatted string representation of the evaluation details.
    """
    result_lines = []
    if evaluation.failure_reason:
        result_lines.append(f"[bold red]Failure Reason:[/bold red] {evaluation.failure_reason}")
    else:
        for critic_result in evaluation.results:
            match_color = "green" if critic_result["match"] else "red"
            field = critic_result["field"]
            score = critic_result["score"]
            weight = critic_result["weight"]
            expected = critic_result["expected"]
            actual = critic_result["actual"]

            result_lines.append(
                f"[bold]{field}:[/bold] "
                f"[{match_color}]Match: {critic_result['match']}"
                f"\n     Score: {score:.2f}/{weight:.2f}[/{match_color}]"
                f"\n     Expected: {expected}"
                f"\n     Actual: {actual}"
            )
    return "\n".join(result_lines)


def display_arcade_chat_header(base_url: str, stream: bool) -> None:
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
            base_url,
            "bold blue",
        ),
    )
    if stream:
        chat_header.append(" (streaming)")
    console.print(chat_header)
