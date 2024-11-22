import os
from pathlib import Path

import toml

from arcade.core.schema import InputParameter, ToolDefinition
from arcade.sdk import ToolCatalog, Toolkit


def get_toolkit_name_from_toml(directory: str) -> str:
    """
    Extract toolkit name from pyproject.toml data.

    Args:
        directory: Directory containing pyproject.toml

    Returns:
        The toolkit name from pyproject.toml

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist in directory
        ValueError: If pyproject.toml is not a valid TOML file
        KeyError: If toolkit name cannot be found in pyproject.toml under [tool.poetry.name]
    """
    pyproject_path = Path(directory) / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found in directory: {directory}")

    try:
        with open(pyproject_path) as f:
            pyproject_data = toml.load(f)
        return str(pyproject_data["tool"]["poetry"]["name"])
    except toml.TomlDecodeError as e:
        raise ValueError(f"Error parsing pyproject.toml: {e}")
    except KeyError:
        raise KeyError("Toolkit name not found in pyproject.toml under [tool.poetry.name]")


def create_metadata_table(toolkit: Toolkit, package_name: str) -> str:
    """
    Create a markdown table with metadata about the toolkit.
    """
    # Extracting information from the toolkit
    toolkit_name = toolkit.name
    version = toolkit.version
    description = toolkit.description
    authors = ", ".join(toolkit.author)
    repository = toolkit.repository

    # Metadata table about the toolkit
    toolkit_metadata_table = f"""
|             |                |
|-------------|----------------|
| Name        | {toolkit_name} |
| Package     | {package_name} |
| Repository  | {repository}   |
| Version     | {version}      |
| Description | {description}  |
| Author      | {authors}      |"""
    return toolkit_metadata_table


def create_tool_toc_table(toolkit: Toolkit) -> str:
    """
    Create a markdown table with TOC about the tools in the toolkit.
    """
    catalog = ToolCatalog()
    catalog.add_toolkit(toolkit)
    tools = [t.definition for t in list(catalog)]
    tool_name_to_description = {tool.name: tool.description for tool in tools}

    tool_toc_table = """
| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
"""

    for tool_name, description in tool_name_to_description.items():
        description_preview = description.split("\n")[0]
        tool_toc_table += f"| {tool_name} | {description_preview} |\n"

    return tool_toc_table


def create_tool_parameter_details(param: InputParameter) -> str:
    """Create markdown documentation for a single tool parameter."""
    param_parts = []

    # Basic parameter info
    param_parts.append(f"- `{param.name}`")
    param_parts.append(f"*({param.value_schema.val_type}, ")
    param_parts.append("required" if param.required else "optional")
    param_parts.append(")*")

    # Parameter description
    if param.description:
        param_parts.append(f" {param.description}")

    # Enum values if present
    if param.value_schema.enum:
        enum_str = ", ".join(f"'{val}'" for val in param.value_schema.enum)
        param_parts.append(f", Valid values are {enum_str}")

    return "".join(param_parts) + "\n"


def create_single_tool_details(tool: ToolDefinition) -> str:
    """Create markdown documentation for a single tool."""
    # Create tool header section
    tool_section = [f"### {tool.name}\n", f"{tool.description}\n\n"]

    # Document parameters if present
    parameters = tool.inputs.parameters
    if parameters:
        tool_section.append("#### Parameters\n")

        # Document each parameter
        for param in parameters:
            tool_section.append(create_tool_parameter_details(param))

    return "".join(tool_section)


def create_tool_details(toolkit: Toolkit) -> str:
    """
    Generate detailed markdown documentation for all tools in the toolkit.

    This function creates a markdown section for each tool that includes:
    - Tool name
    - Tool description
    - Parameter details including type, required/optional status, description and valid values

    Args:
        toolkit: The Toolkit object containing the tools to document

    Returns:
        A string containing the markdown documentation for all tools
    """
    catalog = ToolCatalog()
    catalog.add_toolkit(toolkit)
    tools = [t.definition for t in list(catalog)]

    tool_separator = "\n---\n\n"
    all_tool_sections = [create_single_tool_details(tool) + tool_separator for tool in tools]
    all_tool_sections[-1] = all_tool_sections[-1].rstrip(tool_separator)

    return "".join(all_tool_sections)


def create_toolkit_docs(directory: str) -> None:
    """
    Creates docs for a toolkit package.
    """
    package_name = get_toolkit_name_from_toml(directory)
    toolkit = Toolkit.from_package(package_name)

    title = f"# {toolkit.name.capitalize()} Toolkit"
    metadata_table = create_metadata_table(toolkit, package_name)
    tool_toc_table = create_tool_toc_table(toolkit)
    tool_details = create_tool_details(toolkit)

    # Create the REFERENCE.md file in the directory
    reference_md_path = os.path.join(directory, "REFERENCE.md")

    # Write the content to the file
    with open(reference_md_path, "w") as f:
        f.write(f"""{title}

{metadata_table}

{tool_toc_table}

{tool_details}
""")
