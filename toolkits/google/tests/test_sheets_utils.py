import pytest

from arcade_google.models import SheetDataInput
from arcade_google.utils import (
    col_to_index,
    compute_sheet_data_dimensions,
    index_to_col,
    is_col_greater,
)


@pytest.fixture
def sheet_data_input_fixture():
    data = {
        1: {
            "A": "name",
            "B": "age",
            "C": "email",
            "D": "score",
            "E": "gender",
            "F": "city",
            "G": "country",
            "H": "registration_date",
        },
        2: {
            "A": "John Doe",
            "B": 28,
            "C": "johndoe@example.com",
            "D": 85.4,
            "E": "Male",
            "F": "New York",
            "G": "USA",
            "H": "2023-01-15",
        },
        10: {
            "A": "Nate Green",
            "B": 30,
            "C": "nateg@example.com",
            "D": 88,
            "E": "Male",
            "F": "Orlando",
            "G": "USA",
            "H": "2024-02-01",
        },
        43: {
            "A": 100,
            "B": 300,
            "H": 123,
            "I": "=SUM(SEQUENCE(10))",
        },
        44: {
            "A": 456,
            "B": 234,
            "H": 123,
            "I": "=SUM(SEQUENCE(10))",
        },
    }
    return SheetDataInput(data=data)


@pytest.mark.parametrize(
    "col, expected_index",
    [
        ("A", 0),
        ("B", 1),
        ("Z", 25),
        ("AA", 26 + 0),
        ("AZ", (1 * 26) + 25),
        ("BA", (2 * 26) + 0),
        ("ZZ", (26 * 26) + 25),
        ("AAA", (1 * 26 * 26) + (1 * 26) + 0),
        ("AAB", (1 * 26 * 26) + (1 * 26) + 1),
        ("QED", (17 * 26 * 26) + (5 * 26) + 3),
    ],
)
def test_col_to_index(col, expected_index):
    assert col_to_index(col) == expected_index


@pytest.mark.parametrize(
    "index, expected_col",
    [
        (0, "A"),
        (1, "B"),
        (25, "Z"),
        (26 + 0, "AA"),
        ((1 * 26) + 25, "AZ"),
        ((2 * 26) + 0, "BA"),
        ((26 * 26) + 25, "ZZ"),
        ((1 * 26 * 26) + (1 * 26) + 0, "AAA"),
        ((1 * 26 * 26) + (1 * 26) + 1, "AAB"),
        ((17 * 26 * 26) + (5 * 26) + 3, "QED"),
    ],
)
def test_index_to_col(index, expected_col):
    assert index_to_col(index) == expected_col


@pytest.mark.parametrize(
    "col1, col2, expected_result",
    [
        ("A", "B", False),
        ("B", "A", True),
        ("AA", "AB", False),
        ("AB", "AA", True),
        ("A", "AA", False),
        ("AA", "A", True),
        ("Z", "AA", False),
        ("AA", "Z", True),
        ("AAA", "AAB", False),
        ("AAB", "AAA", True),
        ("QED", "QEE", False),
        ("QEE", "QED", True),
    ],
)
def test_is_col_greater(col1, col2, expected_result):
    assert is_col_greater(col1, col2) == expected_result


# A simple fake SheetDataInput class to simulate the fixture
class FakeSheetDataInput:
    def __init__(self, data):
        self.data = data


def test_compute_sheet_data_dimensions(sheet_data_input_fixture):
    (min_row, max_row), (min_col_index, max_col_index) = compute_sheet_data_dimensions(
        sheet_data_input_fixture
    )

    expected_min_row = 1
    expected_max_row = 44
    expected_min_col_index = 0  # Column "A"
    expected_max_col_index = 8  # Column "I"

    assert min_row == expected_min_row
    assert max_row == expected_max_row
    assert min_col_index == expected_min_col_index
    assert max_col_index == expected_max_col_index
