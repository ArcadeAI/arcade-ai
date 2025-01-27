import logging
import os
from datetime import datetime
from textwrap import dedent

from arcadepy import Arcade
from crewai import Agent, Crew, Task
from crewai_arcade.manager import CrewAIToolManager
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

arcade_client = Arcade()
user_id = os.getenv("ARCADE_USER_ID")

manager = CrewAIToolManager(arcade_client, user_id)
# Retrieve the tools from the specified toolkit
tools = manager.get_tools(toolkits=["google"])


def main_agent(llm, tools) -> Agent:
    """Creates the main Agent for CrewAI with specified role, backstory, and goal."""
    return Agent(
        role="Main Agent",
        backstory=dedent("""
                You are the main Agent. Your purpose is to provide expertise and guidance within this team,
                with a specific focus on problem-solving and efficient decision-making.
            """),
        goal=dedent("""
                Your objective is to support the team with high-quality insights and effective assistance,
                leveraging the tools and knowledge at your disposal.
            """),
        tools=tools,
        allow_delegation=False,
        verbose=True,
        llm=llm,
    )


def task(agent):
    return Task(
        description=dedent("""
        # Task
        You are an AI assistant designed to help the team.

        # Guidelines
        Your responses should be:
        - Friendly and approachable, using a warm tone

        # Context
        The attendees are {attendees}

        # User Request
        Complete the following request using the tools at your disposal: {user_request}
        """),
        expected_output="A friendly and helpful response in Spanish following the given guidelines.",
        agent=agent,
        tools=agent.tools,
    )


def main():
    logger.info("Starting the CrewAI agent workflow.")
    agent = main_agent(ChatOpenAI(model_name="gpt-4o"), tools=tools)
    task_instance = task(agent)

    crew = Crew(
        agents=[agent],
        tasks=[task_instance],
        verbose=True,
    )

    user_inputs = [
        {
            "attendees": "",
            "user_request": f"Please schedule a calendar event for {datetime.now().strftime('%Y-%m-%d')} from 10:00 PM to 11:00 PM Argentina time. The event is a meeting combined with team building activities.",
        },
    ]

    # Execute the workflow for each user input
    for input_data in user_inputs:
        workflow = crew.kickoff(inputs=input_data)
        logger.info(f"Workflow executed: {workflow}")


if __name__ == "__main__":
    main()
