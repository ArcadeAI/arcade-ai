def remove_none_values(data: dict) -> dict:
    """Remove all keys with None values from the dictionary."""
    return {k: v for k, v in data.items() if v is not None}
