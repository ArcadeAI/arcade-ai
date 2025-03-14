from enum import Enum
from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google
from pydantic import BaseModel, model_validator

from arcade_google.utils import build_sheets_service


class RecalculationInterval(str, Enum):
    RECALCULATION_INTERVAL_UNSPECIFIED = "RECALCULATION_INTERVAL_UNSPECIFIED"
    ON_CHANGE = "ON_CHANGE"
    MINUTE = "MINUTE"
    HOUR = "HOUR"


class Color(BaseModel):
    red: float
    green: float
    blue: float
    alpha: float


class ThemeColorType(str, Enum):
    THEME_COLOR_TYPE_UNSPECIFIED = "THEME_COLOR_TYPE_UNSPECIFIED"
    TEXT = "TEXT"
    BACKGROUND = "BACKGROUND"
    ACCENT1 = "ACCENT1"
    ACCENT2 = "ACCENT2"
    ACCENT3 = "ACCENT3"
    ACCENT4 = "ACCENT4"
    ACCENT5 = "ACCENT5"
    ACCENT6 = "ACCENT6"
    LINK = "LINK"


class NumberFormatType(str, Enum):
    NUMBER_FORMAT_TYPE_UNSPECIFIED = "NUMBER_FORMAT_TYPE_UNSPECIFIED"
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    PERCENT = "PERCENT"
    CURRENCY = "CURRENCY"
    DATE = "DATE"
    TIME = "TIME"
    DATE_TIME = "DATE_TIME"
    SCIENTIFIC = "SCIENTIFIC"


class NumberFormat(BaseModel):
    type: NumberFormatType
    pattern: str


class ColorStyle(BaseModel):
    rgbColor: Optional[Color] = None
    themeColor: Optional[ThemeColorType] = None


class Style(str, Enum):
    STYLE_UNSPECIFIED = "STYLE_UNSPECIFIED"
    DOTTED = "DOTTED"
    DASHED = "DASHED"
    SOLID = "SOLID"
    SOLID_MEDIUM = "SOLID_MEDIUM"
    SOLID_THICK = "SOLID_THICK"
    NONE = "NONE"
    DOUBLE = "DOUBLE"


class Border(BaseModel):
    style: Style
    width: int
    color: Optional[Color] = None
    colorStyle: Optional[ColorStyle] = None


class Borders(BaseModel):
    top: Optional[Border] = None
    bottom: Optional[Border] = None
    left: Optional[Border] = None
    right: Optional[Border] = None


class Padding(BaseModel):
    top: int
    right: int
    bottom: int
    left: int


class HorizontalAlign(str, Enum):
    HORIZONTAL_ALIGN_UNSPECIFIED = "HORIZONTAL_ALIGN_UNSPECIFIED"
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"


class VerticalAlign(str, Enum):
    VERTICAL_ALIGN_UNSPECIFIED = "VERTICAL_ALIGN_UNSPECIFIED"
    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


class WrapStrategy(str, Enum):
    WRAP_STRATEGY_UNSPECIFIED = "WRAP_STRATEGY_UNSPECIFIED"
    OVERFLOW_CELL = "OVERFLOW_CELL"
    LEGACY_WRAP = "LEGACY_WRAP"
    CLIP = "CLIP"
    WRAP = "WRAP"


class TextDirection(str, Enum):
    TEXT_DIRECTION_UNSPECIFIED = "TEXT_DIRECTION_UNSPECIFIED"
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
    RIGHT_TO_LEFT = "RIGHT_TO_LEFT"


class Link(BaseModel):
    uri: str


class TextFormat(BaseModel):
    foregroundColor: Optional[Color] = None
    foregroundColorStyle: Optional[ColorStyle] = None
    fontFamily: Optional[str] = None
    fontSize: Optional[int] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    strikethrough: Optional[bool] = None
    underline: Optional[bool] = None
    link: Optional[Link] = None


class HyperlinkDisplayType(str, Enum):
    HYPERLINK_DISPLAY_TYPE_UNSPECIFIED = "HYPERLINK_DISPLAY_TYPE_UNSPECIFIED"
    LINKED = "LINKED"
    PLAIN_TEXT = "PLAIN_TEXT"


class TextRotation(BaseModel):
    angle: Optional[int] = None
    vertical: Optional[bool] = None

    @model_validator(mode="after")
    def check_one(cls, model: "TextRotation") -> "TextRotation":
        if model.angle is not None and model.vertical is not None:
            raise ValueError("Only one of 'angle' or 'vertical' can be specified in TextRotation")
        return model


class CellFormat(BaseModel):
    numberFormat: Optional[NumberFormat] = None
    backgroundColor: Optional[Color] = None
    backgroundColorStyle: Optional[ColorStyle] = None
    borders: Optional[Borders] = None
    padding: Optional[Padding] = None
    horizontalAlignment: Optional[HorizontalAlign] = None
    verticalAlignment: Optional[VerticalAlign] = None
    wrapStrategy: Optional[WrapStrategy] = None
    textDirection: Optional[TextDirection] = None
    textFormat: Optional[TextFormat] = None
    hyperlinkDisplayType: Optional[HyperlinkDisplayType] = None
    textRotation: Optional[TextRotation] = None


class IterativeCalculationSettings(BaseModel):
    maxIterations: int
    convergenceThreshold: float


class ThemeColorPair(BaseModel):
    colorType: ThemeColorType
    color: ColorStyle


class SpreadsheetTheme(BaseModel):
    primaryFontFamily: str
    themeColors: list[ThemeColorPair]


class SpreadsheetProperties(BaseModel):
    title: str
    locale: str
    autoRecalc: RecalculationInterval
    timeZone: str
    defaultFormat: Optional[CellFormat] = None
    iterativeCalculationSettings: Optional[IterativeCalculationSettings] = None
    spreadsheetTheme: Optional[SpreadsheetTheme] = None
    importFunctionsExternalUrlAccessAllowed: bool


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
)
def create_spreadsheet(
    context: ToolContext,
    title: Annotated[str, "The title of the new spreadsheet"] = "Untitled spreadsheet",
) -> Annotated[dict, "The created spreadsheet's id and title"]:
    """Create a new blank spreadsheet with the provided title

    Returns the newly created spreadsheet's id and title
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    body = {"properties": {"title": title}}
    response = (
        service.spreadsheets().create(body=body, fields="spreadsheetId,properties/title").execute()
    )

    return {"title": response["properties"]["title"], "id": response["spreadsheetId"]}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
)
def update_sheet(
    context: ToolContext,
    spreadsheet_id: Annotated[str, "The name of the spreadsheet to update"],
    sheet_name: Annotated[str, "The name of the sheet to update"],
    start_column: Annotated[str, "The start column of the range to update"],
    end_column: Annotated[str, "The end column of the range to update"],
    start_row: Annotated[int, "The start row of the range to update"],
    end_row: Annotated[int, "The end row of the range to update"],
) -> Annotated[dict, "The updated spreadsheet's id and title"]:
    """Create a new blank spreadsheet with the provided title

    Returns the newly created spreadsheet's id and title
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    body = {
        "requests": [
            {
                "updateCells": {
                    "rows": [
                        {
                            "values": [
                                {"userEnteredValue": {"stringValue": "my string!"}},
                                {"userEnteredValue": {"numberValue": 123}},
                                {},
                                {"userEnteredValue": {"boolValue": True}},
                            ]
                        },
                        {
                            "values": [
                                {"userEnteredValue": {"stringValue": "my string2!"}},
                                {"userEnteredValue": {"numberValue": 1234}},
                                {},
                                {"userEnteredValue": {"boolValue": False}},
                            ]
                        },
                    ],
                    "start": {"rowIndex": start_row, "columnIndex": start_column},
                    "end": {"rowIndex": end_row, "columnIndex": end_column},
                }
            }
        ]
    }

    response = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    print(response)

    return {"status": "success"}


# Implements: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/get
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
)
async def get_sheet_data(
    context: ToolContext,
    spreadsheet_name: Annotated[
        Optional[str], "The name of the spreadsheet to get"
    ] = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U",
    sheet_name: Annotated[Optional[str], "The name of the sheet to get"] = "Sheet1",
    start_column: Annotated[Optional[str], "The start column of the range to get"] = "A",
    end_column: Annotated[Optional[str], "The end column of the range to get"] = "Z",
    start_row: Annotated[Optional[int], "The start row of the range to get"] = 1,
    end_row: Annotated[Optional[int], "The end row of the range to get"] = 1000,
) -> Annotated[
    dict,
    "The spreadsheet data",
]:
    """
    Get the data from a sheet in a spreadsheet.

    Returns a dictionary mapping cells to their values, organized by column letter and row number.

    For example:
    {
        "range": "Sheet1!A1:Z1000",
        "values": {
            "A": {"1": "header1", "2": "value1"},
            "B": {"1": "header2", "2": "value2"}
        }
    }
    This represents a spreadsheet where A1="header1", A2="value1", B1="header2", B2="value2".
    """
    # TODO: Validate start_column and end_column are valid column names
    # TODO: Validate start_row and end_row are valid row numbers
    # TODO: Get the spreadsheet id from the spreadsheet name
    spreadsheet_name = "10JHkLnt4BXj420EjATGno4yDSOWd1xHUI2BdwQwpcSE"
    range_ = f"'{sheet_name}'!{start_column}{start_row}:{end_column}{end_row}"

    service = build_sheets_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    results = (
        service.spreadsheets().values().get(spreadsheetId=spreadsheet_name, range=range_).execute()
    )
    return convert_to_dict(results)


# @tool(
#     requires_auth=Google(
#         scopes=["https://www.googleapis.com/auth/drive"],  # TODO: Change to drive.file
#     )
# )
# def write_to_cell(
#     context: ToolContext,
#     spreadsheet_name: Annotated[str, "The name of the spreadsheet to write to"],
#     column: Annotated[str, "The column to write to"],
#     row: Annotated[int, "The row to write to"],
#     value: Annotated[str, "The value to write to the cell"],
#     sheet_name: Annotated[Optional[str], "The name of the sheet to write to"] = "Sheet1",
# ) -> Annotated[dict, "The status of the operation"]:
#     """
#     Write a value to a cell in a spreadsheet.
#     """
#     # TODO: Validate column is a valid column name
#     # TODO: Validate row is a valid row number
#     # TODO: Figure out how to support multiple types of values e.g., strings, numbers, booleans,..
#     # TODO: Get the spreadsheet id from the spreadsheet name
#     spreadsheet_id = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U"
#     range_ = f"'{sheet_name}'!{column}{row}"

#     service = build_sheets_service(
#         context.get_auth_token_or_empty()
#     )

#     # TODO: Create enum for valueInputOption?
#     service.spreadsheets().values().update(
#         spreadsheetId=spreadsheet_id,
#         range=range_,
#         valueInputOption="USER_ENTERED",
#         body={
#             "range": range_,
#             "majorDimension": "ROWS",
#             "values": [[value]],
#         },
#     ).execute()

#     # TODO: Should we return the updated spreadsheet data? I think we should.
#     return {"status": "success"}


# @tool(
#     requires_auth=Google(
#         scopes=["https://www.googleapis.com/auth/drive"],  # TODO: Change to drive.file
#     )
# )
# def write_to_range(
#     context: ToolContext,
#     values: Annotated[list[list[str]], "The values to write to the range"],
#     start_column: Annotated[str, "The start column of the range to get"],
#     end_column: Annotated[str, "The end column of the range to get"],
#     start_row: Annotated[int, "The start row of the range to get"],
#     end_row: Annotated[int, "The end row of the range to get"],
#     spreadsheet_name: Annotated[
#         Optional[str], "The name of the spreadsheet to get"
#     ] = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U",
#     sheet_name: Annotated[Optional[str], "The name of the sheet to get"] = "Sheet1",
# ) -> Annotated[dict, "The status of the operation"]:
#     """
#     Write a values to a range in a spreadsheet.
#     """
#     # TODO: Validate start_column and end_column are valid column names
#     # TODO: Validate start_row and end_row are valid row numbers
#     # TODO: Get the spreadsheet id from the spreadsheet name
#     spreadsheet_id = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U"
#     range_ = f"'{sheet_name}'!{start_column}{start_row}:{end_column}{end_row}"

#     service = build_sheets_service(
#         context.authorization.token
#         if context.authorization and context.authorization.token
#         else ""
#     )

#     # TODO: Create enum for valueInputOption?
#     service.spreadsheets().values().update(
#         spreadsheetId=spreadsheet_id,
#         range=range_,
#         valueInputOption="USER_ENTERED",
#         body={"values": values},
#     ).execute()

#     return {"status": "success"}


def column_index_to_letter(n):
    """Convert a 0-indexed column number to its corresponding Google Sheets column letter."""
    result = ""
    while n >= 0:
        #  65 is 'A' in ASCII & 26 is the number of letters in the alphabet
        result = chr(n % 26 + 65) + result
        n = n // 26 - 1
    return result


# def convert_to_a1(sheet_data: dict) -> dict:
#     """
#     Convert sheet data in the form of:
#     {
#       "majorDimension": "ROWS",
#       "range": "Sheet1!A1:Z1000",
#       "values": [
#           [...],
#           [...]
#       ]
#     }
#     to a dictionary in the form of:
#     {
#         "A1": "value",
#         "A2": "value",
#         "B2": "value",
#         "C13": "value",
#         ...
#     }
#     """
#     a1_dict = {}
#     values = sheet_data.get("values", [])

#     if sheet_data.get("majorDimension") == "ROWS":
#         for row_index, row in enumerate(values):
#             # Ensure row is a list, even if empty
#             if not isinstance(row, list):
#                 continue
#             for col_index, cell in enumerate(row):
#                 if cell:  # only include non-empty cells
#                     col_letter = column_index_to_letter(col_index)
#                     cell_ref = f"{col_letter}{row_index + 1}"
#                     a1_dict[cell_ref] = cell
#     # TODO: Implement column-major conversion
#     return a1_dict


def convert_to_dict(sheet_data: dict) -> dict:  # noqa: C901
    """
    Convert sheet data in the form of:
    {
        "majorDimension": "ROWS",
        "range": "Sheet1!A1:Z1000",
        "values": [
            [...],
            [...],
            [...],
            ...
        ]
    }
    to a dictionary in the form of:
    {
        "A": {"1": "value", "2": "value", "13": "value"},
        "B": {"4": "value", "5": "value", "16": "value"},
        "X": {"1": "value", "78": "value", "23": "value"},
    }
    """
    result = {}
    values = sheet_data.get("values", [])
    major_dimension = sheet_data.get("majorDimension", "ROWS")

    if major_dimension == "ROWS":
        for row_index, row in enumerate(values):
            # Ensure row is a list, even if empty
            if not isinstance(row, list):
                continue
            for col_index, cell in enumerate(row):
                # Only include non-empty cells (adjust this logic if 0 or False are valid values)
                if cell:
                    col_letter = column_index_to_letter(col_index)
                    if col_letter not in result:
                        result[col_letter] = {}
                    # Use row numbers as strings
                    result[col_letter][str(row_index + 1)] = cell
    elif major_dimension == "COLUMNS":
        # If the data is column-major, each item in 'values' represents a column.
        for col_index, col in enumerate(values):
            if not isinstance(col, list):
                continue
            col_letter = column_index_to_letter(col_index)
            for row_index, cell in enumerate(col):
                if cell:
                    if col_letter not in result:
                        result[col_letter] = {}
                    result[col_letter][str(row_index + 1)] = cell

    return {"range": sheet_data.get("range"), "values": result}
