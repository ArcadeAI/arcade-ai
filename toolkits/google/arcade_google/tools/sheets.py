from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google

from arcade_google.tools.utils import build_sheets_service


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
    """
    # TODO: Validate start_column and end_column are valid column names
    # TODO: Validate start_row and end_row are valid row numbers
    # TODO: Get the spreadsheet id from the spreadsheet name
    spreadsheet_name = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U"
    range_ = f"'{sheet_name}'!{start_column}{start_row}:{end_column}{end_row}"

    service = build_sheets_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    results = (
        service.spreadsheets().values().get(spreadsheetId=spreadsheet_name, range=range_).execute()
    )

    return convert_to_a1(results)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive"],  # TODO: Change to drive.file
    )
)
def write_to_cell(
    context: ToolContext,
    spreadsheet_name: Annotated[str, "The name of the spreadsheet to write to"],
    column: Annotated[str, "The column to write to"],
    row: Annotated[int, "The row to write to"],
    value: Annotated[str, "The value to write to the cell"],
    sheet_name: Annotated[Optional[str], "The name of the sheet to write to"] = "Sheet1",
) -> Annotated[dict, "The status of the operation"]:
    """
    Write a value to a cell in a spreadsheet.
    """
    # TODO: Validate column is a valid column name
    # TODO: Validate row is a valid row number
    # TODO: Figure out how to support multiple types of values e.g., strings, numbers, booleans, etc
    # TODO: Get the spreadsheet id from the spreadsheet name
    spreadsheet_id = "1v4Gp6-a3hWdR-dc4kCUdM0D4vV1OmL7mMgV5g76jL4U"
    range_ = f"'{sheet_name}'!{column}{row}"

    service = build_sheets_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    # TODO: Create enum for valueInputOption?
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption="USER_ENTERED",
        body={
            "range": range_,
            "majorDimension": "ROWS",
            "values": [[value]],
        },
    ).execute()

    # TODO: Should we return the updated spreadsheet data? I think we should.
    return {"status": "success"}


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


def convert_to_a1(sheet_data: dict) -> dict:
    """
    Convert sheet data in the form of:
    {
      "majorDimension": "ROWS",
      "range": "Sheet1!A1:Z1000",
      "values": [
          [...],
          [...]
      ]
    }
    to a dictionary with A1 notation keys for non-empty cells.
    """
    a1_dict = {}
    values = sheet_data.get("values", [])

    if sheet_data.get("majorDimension") == "ROWS":
        for row_index, row in enumerate(values):
            # Ensure row is a list, even if empty
            if not isinstance(row, list):
                continue
            for col_index, cell in enumerate(row):
                if cell:  # only include non-empty cells
                    col_letter = column_index_to_letter(col_index)
                    cell_ref = f"{col_letter}{row_index + 1}"
                    a1_dict[cell_ref] = cell
    # TODO: Implement column-major conversion
    return a1_dict
