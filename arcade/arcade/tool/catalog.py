import asyncio
import inspect
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    cast,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from arcade.actor.core.conf import settings
from arcade.apm.base import ToolPack
from arcade.sdk.annotations import Inferrable
from arcade.tool.errors import ToolDefinitionError
from arcade.tool.schemas import (
    InputParameter,
    ToolDefinition,
    ToolInputs,
    ToolOutput,
    ToolRequirements,
    ValueSchema,
)
from arcade.utils import (
    does_function_return_value,
    first_or_none,
    is_string_literal,
    snake_to_pascal_case,
)

WireType = Literal["string", "integer", "float", "boolean", "json"]


class ToolMeta(BaseModel):
    """
    Metadata for a tool once it's been materialized.
    """

    module: str
    path: Optional[str] = None
    date_added: datetime = Field(default_factory=datetime.now)
    date_updated: datetime = Field(default_factory=datetime.now)


class MaterializedTool(BaseModel):
    """
    Data structure that holds tool information while stored in the Catalog
    """

    tool: Callable
    definition: ToolDefinition
    meta: ToolMeta

    # Thought (Sam): Should generate create these from ToolDefinition?
    input_model: type[BaseModel]
    output_model: type[BaseModel]

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def version(self) -> str:
        return self.definition.version

    @property
    def description(self) -> str:
        return self.definition.description


# TODO make a generate for catalog type


class ToolCatalog:
    """Singleton class that holds all tools for a given actor"""

    def __init__(self, tools_dir: Path = settings.TOOLS_DIR):
        self.tools: dict[str, MaterializedTool] = self.read_tools(tools_dir)

    @staticmethod
    def read_tools(directory: Path) -> dict[str, MaterializedTool]:
        """
        Create tool definitions from a directory of python files
        """

        toolpack = ToolPack.from_lock_file(directory)
        sys.path.append(str(Path(directory).resolve() / "tools"))

        tools: dict[str, MaterializedTool] = {}
        for name, tool_spec in toolpack.tools.items():
            module_name, versioned_tool = tool_spec.split(".", 1)
            func_name, version = versioned_tool.split("@")

            module = import_module(module_name)
            tool_func = getattr(module, func_name)
            input_model, output_model = create_func_models(tool_func)
            tool_name = snake_to_pascal_case(
                name
            )  # TODO make sure this follows create_tool_definition
            tools[tool_name] = MaterializedTool(
                definition=ToolCatalog.create_tool_definition(tool_func, version),
                tool=tool_func,
                meta=ToolMeta(module=module_name, path=module.__file__),
                input_model=input_model,
                output_model=output_model,
            )

        return tools

    @staticmethod
    def create_tool_definition(tool: Callable, version: str) -> ToolDefinition:
        """
        Given a tool function, create a ToolDefinition
        """

        tool_name = getattr(tool, "__tool_name__", tool.__name__)

        # Hard requirement: tools must have descriptions
        tool_description = getattr(tool, "__tool_description__", None)
        if tool_description is None:
            raise ToolDefinitionError(f"Tool {tool_name} is missing a description")

        # If the function returns a value, it must have a type annotation
        if does_function_return_value(tool) and tool.__annotations__.get("return") is None:
            raise ToolDefinitionError(f"Tool {tool_name} must have a return type annotation")

        return ToolDefinition(
            name=tool_name,
            description=tool_description,
            version=version,
            inputs=create_input_definition(tool),
            output=create_output_definition(tool),
            requirements=ToolRequirements(
                authorization=getattr(tool, "__tool_requires_auth__", None),
            ),
        )

    def __getitem__(self, name: str) -> MaterializedTool:
        # TODO error handling
        for tool_name, tool in self.tools.items():
            if tool_name == name:
                return tool
        raise KeyError(f"Tool {name} not found.")

    def __iter__(self) -> Iterator[MaterializedTool]:
        yield from self.tools.values()

    def get_tool(self, name: str) -> Optional[Callable]:
        for tool in self.tools.values():
            if tool.definition.name == name:
                return tool.tool
        raise ValueError(f"Tool {name} not found.")

    def list_tools(self) -> list[dict[str, str]]:
        def get_tool_endpoint(t: MaterializedTool) -> str:
            return f"/tool/{t.meta.module}/{t.definition.name}"

        return [
            {
                "name": t.definition.name,
                "description": t.definition.description,
                "version": t.version,
                "endpoint": get_tool_endpoint(t),
            }
            for t in self.tools.values()
        ]


def create_input_definition(func: Callable) -> ToolInputs:
    """
    Create an input model for a function based on its parameters.
    """
    input_parameters = []
    for _, param in inspect.signature(func, follow_wrapped=True).parameters.items():
        tool_field_info = extract_field_info(param)

        is_enum = False
        enum_values: list[str] = []

        # Special case: Literal["string1", "string2"] can be enumerated on the wire
        if is_string_literal(tool_field_info.field_type):
            is_enum = True
            enum_values = [str(e) for e in get_args(tool_field_info.field_type)]

        # If the field has a default value, it is not required
        # If the field is optional, it is not required
        has_default_value = tool_field_info.default is not None
        is_required = not tool_field_info.is_optional and not has_default_value

        input_parameters.append(
            InputParameter(
                name=tool_field_info.name,
                description=tool_field_info.description,
                required=is_required,
                inferrable=tool_field_info.is_inferrable,
                value_schema=ValueSchema(
                    val_type=tool_field_info.wire_type,
                    enum=enum_values if is_enum else None,
                ),
            )
        )

    return ToolInputs(parameters=input_parameters)


def create_output_definition(func: Callable) -> ToolOutput:
    """
    Create an output model for a function based on its return annotation.
    """
    return_type = inspect.signature(func, follow_wrapped=True).return_annotation
    description = "No description provided."

    if return_type is inspect.Signature.empty:
        return ToolOutput(
            value_schema=None,
            description="No description provided.",
            available_modes=["null"],
        )

    if hasattr(return_type, "__metadata__"):
        description = return_type.__metadata__[0] if return_type.__metadata__ else None
        return_type = return_type.__origin__

    # Unwrap Optional types
    is_optional = False
    if get_origin(return_type) is Union and type(None) in get_args(return_type):
        return_type = next(arg for arg in get_args(return_type) if arg is not type(None))
        is_optional = True

    wire_type = get_wire_type(return_type)

    available_modes = ["value", "error"]

    if is_optional:
        available_modes.append("null")

    return ToolOutput(
        description=description,
        available_modes=available_modes,
        value_schema=ValueSchema(val_type=wire_type),
    )


@dataclass
class ToolFieldInfo:
    name: str
    default: Any
    original_type: type
    field_type: type
    description: str | None = None
    wire_type: WireType | None = None
    is_optional: bool = True
    is_inferrable: bool = True


def extract_field_info(param: inspect.Parameter) -> ToolFieldInfo:
    """
    Extract type and field parameters from a function parameter.
    """
    annotation = param.annotation
    if annotation == inspect.Parameter.empty:
        raise TypeError(f"Parameter {param} has no type annotation.")

    # Get the majority of the param info from either the Pydantic Field() or regular inspection
    if isinstance(param.default, FieldInfo):
        field_info = extract_pydantic_field_info(param)
    else:
        field_info = extract_regular_field_info(param)

    metadata = getattr(annotation, "__metadata__", [])
    str_annotations = [m for m in metadata if isinstance(m, str)]

    # Get the description from annotations, if present
    if len(str_annotations) == 0:
        pass
    elif len(str_annotations) == 1:
        field_info.description = str_annotations[0]
    elif len(str_annotations) == 2:
        field_info.name = str_annotations[0]
        field_info.description = str_annotations[1]
    else:
        raise ToolDefinitionError(
            f"Parameter {param} has too many string annotations. Expected 0, 1, or 2, got {len(str_annotations)}."
        )

    # Get the Inferrable annotation, if it exists
    inferrable_annotation = first_or_none(Inferrable, get_args(annotation))

    # Params are inferrable by default
    field_info.is_inferrable = inferrable_annotation.value if inferrable_annotation else True

    # Get the wire type
    field_info.wire_type = (
        get_wire_type(str)
        if is_string_literal(field_info.field_type)
        else get_wire_type(field_info.field_type)
    )

    # Reality check
    if field_info.description is None:
        raise ToolDefinitionError(f"Parameter {field_info.name} is missing a description")

    if field_info.wire_type is None:
        raise ToolDefinitionError(f"Unknown parameter type: {field_info.field_type}")

    return field_info


def extract_regular_field_info(param: inspect.Parameter) -> ToolFieldInfo:
    # If the param is Annotated[], unwrap the annotation to get the "real" type
    # Otherwise, use the literal type
    annotation = param.annotation
    original_type = annotation.__args__[0] if get_origin(annotation) is Annotated else annotation
    field_type = original_type

    # Unwrap Optional types
    is_optional = False
    if get_origin(field_type) is Union and type(None) in get_args(field_type):
        field_type = next(arg for arg in get_args(field_type) if arg is not type(None))
        is_optional = True

    return ToolFieldInfo(
        name=param.name,
        default=param.default if param.default is not inspect.Parameter.empty else None,
        is_optional=is_optional,
        original_type=original_type,
        field_type=field_type,
    )


def extract_pydantic_field_info(param: inspect.Parameter) -> ToolFieldInfo:
    default_value = None if param.default.default is PydanticUndefined else param.default.default

    if param.default.default_factory is not None:
        if callable(param.default.default_factory):
            default_value = param.default.default_factory()
        else:
            raise ToolDefinitionError(f"Default factory for parameter {param} is not callable.")

    # If the param is Annotated[], unwrap the annotation to get the "real" type
    # Otherwise, use the literal type
    original_type = (
        param.annotation.__args__[0]
        if get_origin(param.annotation) is Annotated
        else param.annotation
    )
    field_type = original_type

    # Unwrap Optional types
    is_optional = False
    if get_origin(field_type) is Union and type(None) in get_args(field_type):
        field_type = next(arg for arg in get_args(field_type) if arg is not type(None))
        is_optional = True

    return ToolFieldInfo(
        name=param.name,
        description=param.default.description,
        default=default_value,
        is_optional=is_optional,
        original_type=original_type,
        field_type=field_type,
    )


def get_wire_type(
    _type: type,
) -> WireType:
    """
    Mapping between Python types and HTTP/JSON types
    """
    type_mapping = {
        str: "string",
        bool: "boolean",
        int: "integer",
        float: "float",
        dict: "json",
        list: "json",
        BaseModel: "json",
    }

    wire_type = type_mapping.get(_type)
    if wire_type:
        return cast(Literal["string", "integer", "float", "boolean", "json"], wire_type)
    elif hasattr(_type, "__origin__"):
        # account for "list[str]" and "dict[str, int]" and "Optional[str]" and other typing types
        origin = _type.__origin__
        if origin in [list, dict]:
            return "json"
    elif issubclass(_type, BaseModel):
        return "json"
    raise ToolDefinitionError(f"Unsupported parameter type: {_type}")


def create_func_models(func: Callable) -> tuple[type[BaseModel], type[BaseModel]]:
    """
    Analyze a function to create corresponding Pydantic models for its input and output.
    """
    input_fields = {}
    # TODO figure this out (Sam)
    if asyncio.iscoroutinefunction(func) and hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    for name, param in inspect.signature(func, follow_wrapped=True).parameters.items():
        # TODO make this cleaner
        tool_field_info = extract_field_info(param)
        param_fields = {
            "default": tool_field_info.default,
            "description": tool_field_info.description,
            # TODO more here?
        }
        input_fields[name] = (tool_field_info.field_type, Field(**param_fields))

    input_model = create_model(f"{snake_to_pascal_case(func.__name__)}Input", **input_fields)  # type: ignore[call-overload]

    output_model = determine_output_model(func)

    return input_model, output_model


def determine_output_model(func: Callable) -> type[BaseModel]:
    """
    Determine the output model for a function based on its return annotation.
    """
    return_annotation = inspect.signature(func).return_annotation
    output_model_name = f"{snake_to_pascal_case(func.__name__)}Output"
    if return_annotation is inspect.Signature.empty:
        return create_model(output_model_name)
    elif hasattr(return_annotation, "__origin__"):
        if hasattr(return_annotation, "__metadata__"):
            field_type = return_annotation.__args__[0]
            description = (
                return_annotation.__metadata__[0] if return_annotation.__metadata__ else ""
            )
            if description:
                return create_model(
                    output_model_name,
                    result=(field_type, Field(description=str(description))),
                )
        # when the return_annotation has an __origin__ attribute
        # and does not have a __metadata__ attribute.
        return create_model(
            output_model_name,
            result=(
                return_annotation,
                Field(description="No description provided."),
            ),
        )
    else:
        # Handle simple return types (like str)
        return create_model(
            output_model_name,
            result=(return_annotation, Field(description="No description provided.")),
        )
