"""
This example demonstrates how to directly call a tool that does not require authorization.
"""

import os

from arcadepy import Arcade  # pip install arcade-py


def call_non_auth_tool(client: Arcade, user_id: str) -> None:
    """Directly call a prebuilt tool that does not require authorization.

    In this example, we are
        1. Preparing the inputs to the Math.Add tool
        2. Executing the tool
        3. Printing the output of the tool's execution, i.e., the result of adding 9001 and 42

    This is a simple example of calling a non-auth tool. Next, try writing your own non-auth tool for your own use case.
    """
    # Prepare the inputs to the tool as a dictionary where keys are the names of the parameters expected by the tool and the values are the actual values to pass to the tool
    inputs = {"a": 9001, "b": 42}

    # Execute the tool
    response = client.tools.execute(
        tool_name="Math.Add",
        inputs=inputs,
        user_id=user_id,
    )

    # Print the output of the tool execution
    print(response.output.value)


if __name__ == "__main__":
    arcade_api_key = os.environ[
        "ARCADE_API_KEY"
    ]  # If you forget your arcade API key, it is stored at ~/.arcade/credentials.yaml on `arcade login`
    cloud_host = "https://api.arcade-ai.com"

    client = Arcade(
        base_url=cloud_host,  # Alternatively, use http://localhost:9099 if you are running Arcade Engine locally, or any base_url if you're hosting elsewhere
        api_key=arcade_api_key,
    )

    user_id = "you@example.com"
    call_non_auth_tool(client, user_id)
