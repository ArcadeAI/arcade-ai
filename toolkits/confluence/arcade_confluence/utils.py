def remove_none_values(data: dict) -> dict:
    """Remove all keys with None values from the dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def split_by_space(strings: list[str]) -> list[str]:
    """Split a list of strings by space and return a flattened list of words.

    Args:
        strings: A list of strings to split.

    Returns:
        A flattened list of words.

    Example:
    split_by_space(["hello world", "foobar"]) -> ["hello", "world", "foobar"]

    """
    return [word for s in strings for word in s.split()]
