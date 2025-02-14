import pytest

from arcade.core.schema import ToolAuthorizationContext, ToolContext, ToolSecretItem


def test_get_auth_token_or_empty_with_token():
    expected_token = "test_token"  # noqa: S105
    auth_context = ToolAuthorizationContext(token=expected_token)
    tool_context = ToolContext(authorization=auth_context)

    actual_token = tool_context.get_auth_token_or_empty()

    assert actual_token == expected_token


def test_get_auth_token_or_empty_without_token():
    auth_context = ToolAuthorizationContext(token=None)
    tool_context = ToolContext(authorization=auth_context)

    assert tool_context.get_auth_token_or_empty() == ""


def test_get_auth_token_or_empty_no_authorization():
    tool_context = ToolContext(authorization=None)

    assert tool_context.get_auth_token_or_empty() == ""


def test_get_secret_valid():
    key_id = "my_key"
    val = "secret_value"
    secrets = {key_id: ToolSecretItem(value=val)}
    tool_context = ToolContext(secrets=secrets)

    # When the secret exists, get_secret should return its value.
    actual_secret = tool_context.get_secret(key_id)
    assert actual_secret == val


def test_get_secret_key_not_found():
    key_id = "nonexistent_key"
    secrets = {"other_key": ToolSecretItem(value="another_secret")}
    tool_context = ToolContext(secrets=secrets)

    # When the key is not found, get_secret should raise a ValueError.
    with pytest.raises(ValueError, match=f"Secret {key_id} not found in context."):
        tool_context.get_secret(key_id)


def test_get_secret_when_secrets_is_none():
    tool_context = ToolContext(secrets=None)

    # When no secrets dictionary is provided, get_secret should raise a ValueError.
    with pytest.raises(ValueError, match="Secret missing_key not found in context."):
        tool_context.get_secret("missing_key")
