import os

from google.oauth2.credentials import Credentials
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    build_resource_service,
)
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Step 1: Install required packages
# Run the following in your terminal:
# %pip install -qU langchain-google-community[gmail]
# %pip install -qU langchain-openai
# %pip install -qU langgraph
#
# Step 2: Set environment variables for LangChain and OpenAI API keys
# Uncomment the following lines if you have the LangSmith API key
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
# Step 3: Authenticate with Gmail
# credentials = get_gmail_credentials(
#    token_file="token.json",
#    scopes=["https://mail.google.com/"],
#    client_secrets_file="credentials.json",
# )
# alternative way to authenticate with arcade
from arcade.client import Arcade, AuthProvider

client = Arcade(base_url="http://localhost:9099", api_key=os.environ["ARCADE_API_KEY"])

challenge = client.auth.authorize(
    provider=AuthProvider.google,
    scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    user_id="example_user_id",
)

if challenge.state != "completed":
    print(f"Please visit this URL to authorize: {challenge.auth_url}")
    input("Press Enter after you've completed the authorization...")
    challenge = client.auth.poll_authorization(challenge.auth_id)
    if challenge.state != "completed":
        print("Authorization not completed. Please try again.")
        exit(1)


creds = Credentials(challenge.context.authorization.token)
api_resource = build_resource_service(credentials=creds)
toolkit = GmailToolkit(api_resource=api_resource)

# Step 4: Get available tools
tools = toolkit.get_tools()

# Step 5: Initialize the LLM and create an agent
llm = ChatOpenAI(model="gpt-4o")
agent_executor = create_react_agent(llm, tools)

# Step 6: Draft an email using the agent
example_query = "Read my latest emails to me and summarize them."
events = agent_executor.stream(
    {"messages": [("user", example_query)]},
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()
