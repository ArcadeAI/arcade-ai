"""
This example demonstrates how to directly call a tool that requires authorization.
"""

import json
import os

from arcadepy import Arcade


def call_auth_tool(client, user_id):
    """Directly call a prebuilt tool that requires authorization.

    In this example, we are
        1. Authorizing Arcade to read emails from the user's Gmail account with the user's permission to do so
        2. Reading 5 emails from the user's Gmail account
        3. Printing the emails

    Try altering this example to call a tool that requires a different authorization.
    """
    # Start the authorization process
    auth_response = client.tools.authorize(
        tool_name="Google.ListEmails",  # TODO: Does the toolkit need to be installed if I'm not using api.arcade-ai.com as the base_url?
        user_id=user_id,
    )

    # If not already authorized, then wait for the user to authorize the permissions required by the tool
    if auth_response.status != "completed":
        print(f"Click this link to authorize: {auth_response.authorization_url}")
        input("After you have authorized, press Enter to continue...")
        # client.auth.wait_for_completion(auth_response.authorization_id)

    # Prepare the inputs to the tool as a dictionary where keys are the names of the parameters expected by the tool and the values are the actual values to pass to the tool
    inputs = {"n_emails": 5}

    # Execute the tool
    response = client.tools.execute(
        tool_name="Google.ListEmails",
        inputs=json.dumps(
            inputs
        ),  # TODO why do i need to use json.dumps for this I thought this was fixed?
        user_id=user_id,
    )

    # Print the output of the tool execution.
    print(response)


if __name__ == "__main__":
    client = Arcade(
        base_url="http://localhost:9099",  # Alternatively, use http://localhost:9099 if you are running Arcade Engine locally, or any base_url if you're hosting elsewhere
        api_key=os.environ[
            "ARCADE_API_KEY"
        ],  # Alternatively, set the API key as an environment variable and Arcade will automatically use it
    )

    user_id = "you@example.com"
    call_auth_tool(client, user_id)