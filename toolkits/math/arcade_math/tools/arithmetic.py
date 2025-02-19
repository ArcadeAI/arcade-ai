import math
from statistics import median as stats_median
from typing import Annotated

from arcade.sdk import tool


@tool
def add(
    a: Annotated[int, "The first number"], b: Annotated[int, "The second number"]
) -> Annotated[int, "The sum of the two numbers"]:
    """
    Add two numbers together
    """
    return a + b


@tool
def subtract(
    a: Annotated[int, "The first number"], b: Annotated[int, "The second number"]
) -> Annotated[int, "The difference of the two numbers"]:
    """
    Subtract two numbers
    """
    return a - b


# TODO: Add BSON serialization support and flip this back to `int``
@tool
def multiply(
    a: Annotated[str, "The first number"], b: Annotated[str, "The second number"]
) -> Annotated[str, "The product of the two numbers as a string"]:
    """
    Multiply two numbers together
    """
    return str(int(a) * int(b))


@tool
def divide(
    a: Annotated[int, "The first number"], b: Annotated[int, "The second number"]
) -> Annotated[float, "The quotient of the two numbers"]:
    """
    Divide two numbers
    """
    return a / b


@tool
def sqrt(
    a: Annotated[int, "The number to square root"],
) -> Annotated[float, "The square root of the number"]:
    """
    Get the square root of a number
    """
    return math.sqrt(a)


@tool
def sum_list(
    numbers: Annotated[list[float], "The list of numbers"],
) -> Annotated[float, "The sum of the numbers in the list"]:
    """
    Sum all numbers in a list
    """
    return sum(numbers)


@tool
def sum_range(
    start: Annotated[int, "The start of the range to sum"],
    end: Annotated[int, "The end of the range to sum"],
) -> Annotated[int, "The sum of the numbers in the list"]:
    """
    Sum all numbers from start through end
    """
    return sum(list(range(start, end + 1)))


# ---------------------
# Additional useful tools
# ---------------------


@tool
def mod(
    a: Annotated[int, "The dividend"],
    b: Annotated[int, "The divisor"],
) -> Annotated[int, "The remainder after dividing a by b"]:
    """
    Calculate the remainder (modulus) of one number divided by another.
    """
    return a % b


@tool
def power(
    a: Annotated[int, "The base number"],
    b: Annotated[int, "The exponent"],
) -> Annotated[int, "The result of raising a to the power of b"]:
    """
    Calculate one number raised to the power of another.
    """
    return a**b


@tool
def abs_val(
    a: Annotated[int, "The number"],
) -> Annotated[int, "The absolute value of the number"]:
    """
    Calculate the absolute value of a number.
    """
    return abs(a)


@tool
def log(
    a: Annotated[float, "The number to take the logarithm of"],
    base: Annotated[float, "The logarithmic base"],
) -> Annotated[float, "The logarithm of the number with the specified base"]:
    """
    Calculate the logarithm of a number with a given base.
    """
    return math.log(a, base)


@tool
def avg(
    numbers: Annotated[list[float], "The list of numbers"],
) -> Annotated[float, "The average (mean) of the numbers in the list"]:
    """
    Calculate the average (mean) of a list of numbers.
    Returns 0.0 if the list is empty.
    """
    return sum(numbers) / len(numbers) if numbers else 0.0


@tool
def median(
    numbers: Annotated[list[float], "A list of numbers"],
) -> Annotated[float, "The median value of the numbers in the list"]:
    """
    Calculate the median of a list of numbers.
    If the list is empty, returns 0.0.
    """
    return stats_median(numbers) if numbers else 0.0


@tool
def factorial(
    a: Annotated[int, "The non-negative integer to compute the factorial for"],
) -> Annotated[int, "The factorial of the number"]:
    """
    Compute the factorial of a non-negative integer.
    Returns 1 for 0.
    """
    return math.factorial(a)


@tool
def deg_to_rad(
    degrees: Annotated[float, "Angle in degrees"],
) -> Annotated[float, "Angle in radians"]:
    """
    Convert an angle from degrees to radians.
    """
    return math.radians(degrees)


@tool
def rad_to_deg(
    radians: Annotated[float, "Angle in radians"],
) -> Annotated[float, "Angle in degrees"]:
    """
    Convert an angle from radians to degrees.
    """
    return math.degrees(radians)


@tool
def ceil(
    a: Annotated[float, "The number to round up"],
) -> Annotated[int, "The smallest integer greater than or equal to the number"]:
    """
    Return the ceiling of a number.
    """
    return math.ceil(a)


@tool
def floor(
    a: Annotated[float, "The number to round down"],
) -> Annotated[int, "The largest integer less than or equal to the number"]:
    """
    Return the floor of a number.
    """
    return math.floor(a)


@tool
def round_num(
    value: Annotated[float, "The number to round"],
    ndigits: Annotated[int, "The number of digits after the decimal point"],
) -> Annotated[float, "The number rounded to the specified number of digits"]:
    """
    Round a number to a specified number of digits.
    """
    return round(value, ndigits)


@tool
def gcd(
    a: Annotated[int, "First integer"],
    b: Annotated[int, "Second integer"],
) -> Annotated[int, "The greatest common divisor of a and b"]:
    """
    Calculate the greatest common divisor (GCD) of two integers.
    """
    return math.gcd(a, b)


@tool
def lcm(
    a: Annotated[int, "First integer"],
    b: Annotated[int, "Second integer"],
) -> Annotated[int, "The least common multiple of a and b"]:
    """
    Calculate the least common multiple (LCM) of two integers.
    Returns 0 if either integer is 0.
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)
