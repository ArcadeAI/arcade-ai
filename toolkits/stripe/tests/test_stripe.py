from arcade_stripe.tools.stripe import run_stripe_tool


class DummyContext:
    def __init__(self, secret):
        self.secret = secret

    def get_secret(self, key: str):
        return self.secret


dummy_instances = []


class DummyStripeAPI:
    def __init__(self, secret_key, context):
        self.secret_key = secret_key
        dummy_instances.append(self)

    def run(self, method_name, **params):
        return f"secret={self.secret_key}; method={method_name}; params={params}"


def test_run_stripe_tool_invokes_dummy(monkeypatch):
    dummy_instances.clear()

    monkeypatch.setattr("arcade_stripe.tools.stripe.StripeAPI", DummyStripeAPI)

    context = DummyContext("test_secret_key")

    result = run_stripe_tool(context, "test_method", {"a": "1", "b": None})
    expected = "secret=test_secret_key; method=test_method; params={'a': '1'}"

    assert result == expected
    assert dummy_instances[0].secret_key == "test_secret_key"  # noqa: S105


def test_run_stripe_tool_with_all_params(monkeypatch):
    dummy_instances.clear()

    monkeypatch.setattr("arcade_stripe.tools.stripe.StripeAPI", DummyStripeAPI)

    context = DummyContext("another_secret")
    params = {"x": 100, "y": "value"}

    result = run_stripe_tool(context, "another_method", params)
    expected = "secret=another_secret; method=another_method; params={'x': 100, 'y': 'value'}"

    assert result == expected
    assert dummy_instances[0].secret_key == "another_secret"  # noqa: S105
