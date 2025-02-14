"""

This is an example of how to use Arcade with CrewAI.
The example authenticates into the user's Gmail account using a custom auth handler,
retrieves their 5 most recent emails, and summarizes them.

The example assumes the following:
1. You have an Arcade API key and have set the ARCADE_API_KEY environment variable.
2. You have an OpenAI API key and have set the OPENAI_API_KEY environment variable.
3. You have installed the necessary dependencies in the requirements.txt file: `pip install -r requirements.txt`

"""

from typing import Any

from arcadepy.types.shared import AuthorizationResponse
from crewai import Agent, Crew, Task
from crewai.llm import LLM
from crewai_arcade import ArcadeToolManager


def custom_auth_handler(tool_name: str, **kwargs: dict[str, Any]) -> AuthorizationResponse:
    """Custom auth handler for the ArcadeToolManager"""
    tool_name = kwargs["tool_name"]
    tool_input = kwargs["input"]
    auth_response = kwargs["auth_response"]

    print(f"Authorization required for tool: {tool_name}")
    if "input" in kwargs:
        print(f"Requested inputs for tool '{tool_name}':")
        for input_name, input_value in tool_input.items():
            print(f"  {input_name}: {input_value}")
    print(f"\nTo authorize, visit: {auth_response.url}")

    completed_auth_response = manager.wait_for_auth(auth_response)

    return completed_auth_response


manager = ArcadeToolManager(
    user_id="user@example.com",
    auth_callback=custom_auth_handler,
)
tools = manager.get_tools(tools=["Google.ListEmails"])

crew_agent = Agent(
    role="Main Agent",
    backstory="You are a helpful assistant",
    goal="Help the user with their requests",
    tools=tools,
    allow_delegation=False,
    verbose=True,
    llm=LLM(model="gpt-4o"),
)

task = Task(
    description="Get the 5 most recent emails from the user's inbox and summarize them.",
    expected_output="A bulleted list with a one sentence summary of each email.",
    agent=crew_agent,
    tools=crew_agent.tools,
)

crew = Crew(
    agents=[crew_agent],
    tasks=[task],
    verbose=True,
    memory=True,
)

crew.kickoff()
