# main.py
import logging
from textwrap import dedent

from arcadepy import Arcade
from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools.spotify_tools import SpotifyPlaylistTool

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def authenticate_spotify():
    """
    Handles Spotify authentication using Arcade.
    Returns the access token if successful.
    """
    client = Arcade()
    user_id = input("Enter your email: ")

    auth_response = client.auth.start(
        user_id=user_id,
        provider="spotify",
        scopes=["playlist-read-private", "playlist-read-collaborative"],
    )

    if auth_response.status != "completed":
        logger.info("Complete authorization in your browser:")
        logger.info(auth_response.authorization_url)
        auth_response = client.auth.wait_for_completion(auth_response)

    return auth_response.context.token


def main_agent(llm, tools) -> Agent:
    """Creates the main Agent for CrewAI."""
    return Agent(
        role="Playlist Selector",
        backstory=dedent("""
            You are a music expert specializing in playlist curation. Your role is to understand
            user preferences and select the most appropriate playlist from their Spotify library.
        """),
        goal=dedent("""
            Your goal is to analyze user requests and find the perfect playlist match using
            the available tools.
        """),
        tools=tools,
        allow_delegation=False,
        verbose=True,
        llm=llm,
    )


def create_task(agent):
    return Task(
        description=dedent("""
        # Task
        You are a playlist selection expert tasked with finding the perfect playlist.

        # Guidelines
        Your responses should be:
        - Clear and specific about why you chose the playlist
        - Include the playlist name
        - Explain how it matches the user's request
        - Only select playlists from the list of available playlists

        # User Request
        Find the most suitable playlist based on this description: {user_request}
        """),
        expected_output="A selected playlist name with explanation of why it was chosen",
        agent=agent,
        tools=agent.tools,
    )


def main():
    logger.info("Welcome to Spotify Playlist Selector!")

    # Authenticate and get the Spotify token
    access_token = authenticate_spotify()
    if not access_token:
        logger.error("Authentication failed")
        return

    # Get user input for playlist selection
    user_input = input("Describe the type of playlist you want: ")

    # Initialize the Spotify tool
    playlist_tool = SpotifyPlaylistTool(access_token=access_token)

    agent = main_agent(ChatOpenAI(model_name="gpt-4o"), tools=[playlist_tool])
    task = create_task(agent)

    # Initialize crew
    crew = Crew(agents=[agent], tasks=[task], verbose=True)

    # Execute crew with user input
    crew.kickoff(inputs={"user_request": user_input})


if __name__ == "__main__":
    main()
