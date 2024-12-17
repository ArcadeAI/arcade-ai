import logging
import os
from textwrap import dedent

from arcadepy import Arcade
from crewai import Agent, Crew, Process, Task
from crewai_arcade.manager import CrewAIToolManager
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

arcade_client = Arcade()
user_id = os.getenv("ARCADE_USER_ID")

manager = CrewAIToolManager(arcade_client, user_id)
# Retrieve the tools from the specified toolkit
tools = manager.get_tools(toolkits=["github", "slack", "google"])


def main_agent(llm, tools) -> Agent:
    """Creates an Agent for handling both PR reviews and calendar management."""
    return Agent(
        role="Workflow Coordinator",
        backstory=dedent("""
                You are the Code Review Coordinator. Your purpose is to handle multiple tasks including
                monitoring GitHub PRs, coordinating with team members through Slack, and managing
                calendar events efficiently.
            """),
        goal=dedent("""
                Your objectives are to:
                1. Identify open PRs and ensure proper communication through Slack
                2. Create and manage calendar events while handling time zones appropriately
            """),
        tools=tools,
        allow_delegation=True,
        verbose=True,
        llm=llm,
    )


def workflow_tasks(agent):
    pr_check_task = Task(
        description=dedent("""
        # Task: PR Review Check
        Check for open PRs in the pampa-labs repository called 'gabriela'.

        # Process
        1. Use GitHub tools to search for open PRs
        2. Return the PR details if found

        # Expected Format
        - PR check results including PR number, title, and URL

        # User Request
        {user_request}
        """),
        expected_output="A detailed report of found PRs with their details.",
        agent=agent,
        tools=agent.tools,
    )

    calendar_task = Task(
        description=dedent("""
        # Task: Schedule Review Call
        Create a calendar event for the PR review.

        # Process
        1. Use Google Calendar tools to create a 30-minute review event with lautaro
        2. Include PR details in the event description


        # Expected Format
        - Confirmation of calendar event creation with details
        - Event time, duration, and description

        # User Request
        {user_request}
        """),
        expected_output="Confirmation of calendar event creation with all relevant details.",
        agent=agent,
        tools=agent.tools,
    )

    notification_task = Task(
        description=dedent("""
        # Task: Slack Notification
        Notify relevant team members about the PR and scheduled review.

        # Process
        1. Use "Slack.SendDmToUser" tool to notify user 'lautaro'
        2. Include PR details and scheduled review time in the message

        # Expected Format
        - Confirmation of Slack notification sent
        - Message content summary

        # User Request
        {user_request}
        """),
        expected_output="Confirmation of Slack notification sent with message details.",
        agent=agent,
        tools=agent.tools,
    )

    return [pr_check_task, calendar_task, notification_task]


def main():
    logger.info("Starting the workflow.")
    agent = main_agent(ChatOpenAI(model_name="gpt-4o"), tools=tools)

    tasks = workflow_tasks(agent)

    crew = Crew(
        agents=[agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    # Execute the workflow
    result = crew.kickoff(
        inputs={"user_request": """Check for any open PRs. Today is 12.03.2024"""}
    )
    logger.info(f"Workflow executed: {result}")


if __name__ == "__main__":
    main()
