<h3 align="center">
  <a name="readme-top"></a>
  <img
    src="https://docs.arcade.dev/images/logo/arcade-logo.png"
    style="width: 400px;"
  >
</h3>
<div align="center">
    <a href="https://github.com/arcadeai/arcade-ai/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</a>
  <img src="https://img.shields.io/github/last-commit/ArcadeAI/arcade-ai" alt="GitHub last commit">
</a>
<a href="https://github.com/arcadeai/arcade-ai/actions/workflow/main.yml">
<img src="https://img.shields.io/github/actions/workflow/status/arcadeai/arcade-ai/main.yml" alt="GitHub Actions Status">
</a>
<a href="https://img.shields.io/pypi/pyversions/arcade-ai">
  <img src="https://img.shields.io/pypi/pyversions/arcade-ai" alt="Python Version">
</a>
</div>
<div>
  <p align="center" style="display: flex; justify-content: center; gap: 10px;">
    <a href="https://x.com/TryArcade">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" style="width: 125px;height: 25px; padding-top: .8px; border-radius: 5px;" />
    </a>
    <a href="https://www.linkedin.com/company/arcade-ai" >
      <img src="https://img.shields.io/badge/Follow%20on%20LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn" style="width: 150px; padding-top: 1.5px;height: 22px; border-radius: 5px;" />
    </a>
    <a href="https://discord.com/invite/GUZEMpEZ9p">
      <img src="https://img.shields.io/badge/Join%20our%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join our Discord" style="width: 150px; padding-top: 1.5px; height: 22px; border-radius: 5px;" />
    </a>
  </p>
</div>

<p align="center" style="display: flex; justify-content: center; gap: 5px; font-size: 15px;">
    <a href="https://docs.arcade.dev/home" target="_blank">Documentation</a> •
    <a href="https://docs.arcade.dev/tools" target="_blank">Tools</a> •
    <a href="https://docs.arcade.dev/home/quickstart" target="_blank">Quickstart</a> •
    <a href="https://docs.arcade.dev/home/contact-us" target="_blank">Contact Us</a>

# Arcade Tool SDK

Arcade is a developer platform that lets you build, deploy, and manage tools for AI agents.

The Tool SDK makes it easy to create powerful, secure tools that your agents can use to interact with the world.

![Arcade Diagram](./diagram.png)

To learn more, check out our [documentation](https://docs.arcade.dev/home).

_Pst. hey, you, give us a star if you like it!_

<a href="https://github.com/ArcadeAI/arcade-ai">
  <img src="https://img.shields.io/github/stars/ArcadeAI/arcade-ai.svg" alt="GitHub stars">
</a>

## Table of Contents

-   [What is Arcade?](#what-is-arcade)
-   [Building vs. Executing Tools](#building-vs-executing-tools)
    -   [Building Tools: Traditional vs. Arcade](#building-tools-traditional-vs-arcade)
    -   [Executing Tools: Traditional vs. Arcade](#executing-tools-traditional-vs-arcade)
-   [Why Build Tools with Arcade?](#why-build-tools-with-arcade)
-   [Quickstart: Build a Tool in 5 Minutes](#quickstart-build-a-tool-in-5-minutes)
-   [Building Your Own Tools](#building-your-own-tools)
    -   [Tool SDK Installation](#tool-sdk-installation)
    -   [Creating a New Tool](#creating-a-new-tool)
    -   [Testing Your Tools](#testing-your-tools)
    -   [Sharing Your Toolkit](#sharing-your-toolkit)
-   [Using Tools with Agents](#using-tools-with-agents)
    -   [LLM API](#llm-api)
    -   [Tools API](#tools-api)
    -   [Auth API](#auth-api)
    -   [Agent Frameworks](#using-arcade-with-agent-frameworks)
-   [Client Libraries](#client-libraries)
-   [Support and Community](#support-and-community)

## The Problems with Agent Tools

Tool Calling is the process by which agents reach out to external services to gather context and perform actions.

**The Auth Problem**

Most Agent applications today are limited by the tools that can be called as agents
lack authorization to access external services on the users' behalf. Most LLM tools
today are not designed to work for multiple users. Because of this,
many tools use API keys or single tokens with credentials stored in environment
variables. This makes it nearly impossible to build tools that work for multiple users,
access user specific data, or securely integrate with external systems that require user
authentication and authorization.

This limits agents to use tools that only interact with generic services like search engines,
weather, or calculators.

**The Execution Problem**

While "Tool Calling" might seem to imply tool execution occurs in the request, in practice, the tool execution commonly occurs on the same resources as the agent (i.e. orchestration frameworks). This limits the scalability of the tool execution and prohibits the use of diverse (i.e. serverless or on-premise) compute/storage resources.

**The Tool Definition and Maintainence Problem**

Maintaining the format of a tool separately from the tool code is challenging. This is especially true when the tool is used in multiple agentic applications or when the tool is used in different LLMs that have different tool calling formats.

Arcade solves these problems by providing a standardized way to define, manage and
execute tools, a robust auth system to enable multi-user tool execution, and multiple
levels of APIs by which developers can integrate Arcade into their own applications depending
on their use case.

## Building Tools: Traditional vs. Arcade

<table>
<tr>
<th>Without Arcade</th>
<th>With Arcade</th>
</tr>
<tr>
<td style="font-size: 0.7em;">

```python
# Building a Gmail tool traditionally
# Problems:
# - Hardcoded credentials
# - Single-user design
# - Manual OAuth flow implementation
# - No standard format for LLMs

def list_emails(max_results=10):
    # Need to implement OAuth flow
    # Need to store tokens securely
    # Need to handle token refresh

    # Get credentials here? pass it in?
    # Need error handling if token not refreshed
    creds = get_credentials()
    # Cache the token?

    # Initialize Gmail API client
    # What if the user isn't authorized? kick off the auth flow?
    # in the tool call?
    service = build('gmail', 'v1', credentials=creds)

    # Call the API
    # Need to handle errors if it fails. Retry logic?
    messages = service.users().messages().list(
        userId='me', maxResults=max_results
    ).execute()

    # Format the results for the LLM? utils.py again...
    return messages

```

</td>
<td style="font-size: 0.7em;">

```python
# Building a Gmail tool with Arcade SDK
from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google
from typing import Annotated

@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_emails(
    context: ToolContext,
    max_results: Annotated[int, "Maximum emails to return"] = 10,
) -> Annotated[dict, "List of emails"]:
    """Lists emails in the user's Gmail inbox."""

    # Auth token automatically provided and managed by Arcade
    token = context.authorization.token

    # Your implementation using token
    # ...

# Tool is automatically:
# - Multi-tenant (works for any user)
# - Can access any user's data or services AS the user
# - Tool definition is created automatically
# - Formatted for all LLMs and ready to use
```

</td>
</tr>
</table>

### Executing Tools: Traditional vs. Arcade

<table>
<tr>
<th>Without Arcade</th>
<th>With Arcade</th>
</tr>
<tr>
<td style="font-size: 0.7em;">

```python
# Executing a tool traditionally
import os
import json
from openai import OpenAI
from googleapiclient.discovery import build

# Have to manually maintain a registry of all tools and schemas
TOOLS_REGISTRY = {
    "list_emails": {
        "function": list_emails,  # Function we defined earlier
        "description": "List emails from Gmail",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails"
                }
            }
        }
    }
    # Add all other tools here...
}

# Problem: Need to implement tool execution yourself
def execute_with_tools(query):
    # 1. Call LLM ... What if I want to use Anthropic?
    openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": query}
        ],
        # Manually define schema for all tools
        tools=[TOOLS_REGISTRY["list_emails"]],
        tool_choice="auto"
    )

    # 2. Parse response to see if tool should be called
    response_message = completion.choices[0].message
    # What if parsing fails? Or LLM doesn't call the tool?

    # 3. If tool should be used, execute it manually
    if hasattr(response_message, 'tool_calls'):
        results = []
        for tool_call in response_message.tool_calls:
            # 4. Need to look up which tool was called
            tool_name = tool_call.function.name
            if tool_name not in TOOLS_REGISTRY:
                results.append({"error": "Unknown tool"})
                continue

            # 5. Need credentials for THIS user somehow
            creds = get_user_credentials()  # How? Auth flow?

            # 6. Parse arguments from the LLM
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                results.append({"error": "Invalid arguments"})
                continue

            # 7. Call the tool function with args
            try:
                tool_result = TOOLS_REGISTRY[tool_name]["function"](**args)
                results.append(tool_result)
            except Exception as e:
                results.append({"error": str(e)})

        # 8. Format results for LLM
        formatted_results = json.dumps(results)

        # 9. Call LLM again with results
        second_completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": query},
                response_message,
                {"role": "function", "name": tool_name, "content": formatted_results}
            ]
        )

        return second_completion.choices[0].message.content

    return response_message.content

# Problems:
# - Must maintain tool registry manually
# - No standard interface for different tools
# - Each tool requires custom credential management
# - No way to handle multi-user scenarios
# - Manual parsing of LLM responses and tool results
# - Error handling at multiple stages
# - Complex retry logic if needed
```

</td>
<td style="font-size: 0.7em;">

```python
# Method 1: Arcade LLM API (simplest)
from openai import OpenAI
import os

# OpenAI or Arcade clients
client = OpenAI(
    base_url="https://api.arcade.dev/v1",
    api_key=os.environ["ARCADE_API_KEY"]
)

# One HTTP call
response = client.chat.completions.create(
    model="claude-3-7-sonnet", # or gpt-4o, groq, ollama, etc.
    messages=[
        {"role": "user", "content": "List my recent emails"}
    ],
    tools=["Google.ListEmails"],
    tool_choice="generate",
    user="user@example.com"  # Multi-tenant by default
)
```

```python
# Method 2: Arcade Tools API (lower level)
from arcadepy import Arcade
from openai import OpenAI

llm = OpenAI()
client = Arcade(api_key=os.environ["ARCADE_API_KEY"])

# Get the tool definition in OpenAI format (or anthropic, etc)
tool = client.tools.formatted.get(name="Google.ListEmails", format="openai")

# Get tool call from LLM
tool_call = llm.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "List my recent emails"}],
    tools=many_tools,
    tool_choice="required"
)

# Authorize the specific user if needed
auth = client.tools.authorize(
    tool_name=tool_call.tool_calls[0].function.name,
    user_id="user@example.com"
)

# OAuth flow happens automatically if needed
if auth.status != "completed":
    print(f"Please authorize: {auth.authorization_url}")
    client.auth.wait_for_completion(auth)

# token is automatically passed, no need to pass to tools
emails = client.tools.execute(
    tool_name="Google.ListEmails",
    input={"max_results": 10},
    user_id="user@example.com"
).output.value
```

</td>
</tr>
</table>

## Why Build Tools with Arcade?

Arcade solves key challenges for agent developers:

1. **Auth Native to Agents**: Authentication designed for agentic workflows — the right token is always available for each user without complex integration work.

2. **Multi-Tenant Tool Calling**: Enable your agent to take actions AS the specific user of the agent

3. **Better Agent Capabilities**: Build tools that securely connect to the services your users want your agent to integrate with (Gmail, Slack, Google Drive, Zoom, etc.) without complex integration code.

4. **Clean Codebase**: Eliminate environment variables full of API keys and complex OAuth implementations from your application code.

5. **Flexible Integration**: Choose your integration approach:

    - LLM API for the simplest experience with hundreds of pre-built tools
    - Tools API for direct execution control
    - Auth API for authentication-only integration
    - Framework connectors for LangChain, CrewAI and others

6. **Zero Schema Maintenance**: Tool definitions generate automatically from code annotations and translate to any LLM format.

7. **Built-in Evaluation**: Evaluate your tools across user scenarios, llms, and context with Arcade's tool calling evaluation framework. Ensure your tools are working as expected and are useful for your agents.

8. **Complete Tooling Ecosystem**: Built-in evaluation framework, scalable execution infrastructure, and flexible deployment options (including VPC, Docker, and Kubernetes).

Arcade lets you focus on creating useful tool functionality rather than solving complex authentication, deployment, and integration challenges.

## Quickstart: Call a Tool in 5 Minutes

```bash
# Install the Arcade CLI
pip install arcade-ai

# Log in to Arcade
arcade login

# Create a new toolkit
arcade new

# Install locally
cd mytoolkit
pip install -e .
arcade show --local

# Serve your toolkit
arcade serve
```

Now you can head to https://api.arcade.dev/workers and call your toolkits
through the playground, LLM API, or Tools API of Arcade.

## Building Your Own Tools

Arcade provides a tool SDK that allows you to build your own tools and use them in your agentic applications just like the existing tools Arcade provides. This is useful for building new tools, customizing existing tools to fit your needs, combining multiple tools, or building tools that are not yet supported by Arcade.

### Tool SDK Installation

**Prerequisites**

-   **Python 3.10+**
-   **Arcade Account:** [Sign up here](https://api.arcade.dev/signup) to get started.

Now you can install the Tool SDK through pip.

1. **Install the Arcade CLI:**

    ```bash
    pip install arcade-ai
    ```

    If you plan on writing evaluations for your tools and the LLMs you use, you will also need to install the `evals` extra.

    ```bash
    pip install arcade-ai[evals]
    ```

2. **Log in to Arcade:**
    ```bash
    arcade login
    ```
    This will prompt you to open a browser and authorize the CLI. It will then save the credentials to your machine typically in `~/.arcade/credentials.json`.

Now you're ready to build tools with Arcade!

### Creating a New Tool

1. **Generate a new toolkit:**

    ```bash
    arcade new
    ```

    This will create a new toolkit in the current directory.

    The generated toolkit includes all the scaffolding you need for a working tool. Look for the `mytoolkit/tool.py` file to customize the behavior of your tool.

2. **Install your new toolkit:**

    ```bash
    # make sure you have python and poetry installed
    python --version
    pip install "poetry<2"

    # install your new toolkit
    cd mytoolkit
    make install
    ```

3. **Show the tools in the new Toolkit:**

    ```bash
    # show the tools in Mytoolkit
    arcade show --local -T Mytoolkit

    # show the definition of a tool
    arcade show --local -t Mytoolkit.SayHello

    # show all tools installed in your local python environment
    arcade show --local
    ```

4. **Serve the toolkit:**

    ```bash
    # serve the toolkit
    arcade serve
    ```

    This will serve the toolkit at `http://localhost:8000`.

### Sharing Your Toolkit

To list your toolkit on Arcade, you can open a PR to add your toolkit to the [arcadeai/docs](https://github.com/ArcadeAI/docs) repository.

<br>
<br>

## Using Tools with Agents

Arcade provides multiple ways to use your tools with various agent frameworks. Depending on your use case, you can choose the best method for your application.

### LLM API

The LLM API provides the simplest way to integrate Arcade tools into your application. It extends the standard OpenAI API with additional capabilities:

```python
import os
from openai import OpenAI

prompt = "Send sam a note that I'll be late to the meeting"

api_key = os.environ["ARCADE_API_KEY"]
openai = OpenAI(
    base_url="https://api.arcade.dev/v1",
    api_key=api_key,
)

response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ],
    tools=["Slack.SendDmToUser"],
    tool_choice="generate",
    user="user@example.com"
)

print(response.choices[0].message.content)
```

When a user hasn't authorized a service, the API seamlessly returns an authorization link in the response:

```
To send a Slack message, please authorize access to your Slack account:
https://some.auth.url.arcade.will.generate.for.you...

```

All you need to do is show the url to the user, and from then on, the user will never have to do this again. All future requests will use the authorized token.

After authorization, the same API call returns the completed action:

```
I've sent a message to Sam letting them know you'll be late to the meeting.
```

The LLM API eliminates common integration challenges by providing:

-   Support for multiple LLM providers (OpenAI, Anthropic, Groq, Ollama)
-   Automatic tool format conversion between different LLMs
-   Built-in retry logic for failed tool calls
-   Seamless OAuth flows on demand with only the OpenAI client.
-   Reduce network calls and client code sprawl with `tool_choice` options (`"generate"` or `"execute"`)

### Tools API

Use the Tools API when you want to integrate Arcade's runtime for tool calling into your own agent framework (like LangChain or LangGraph), or if you're using your own approach and want to call Arcade tools or tools you've built with the Arcade Tool SDK.

Features:

-   Tool format retrieval for conversion between different LLMs
-   Methods for customizing Auth flows
-   Authorize tools by tool name and user id
-   Execute tools by tool name and input

Here's an example of how to use the Tools API to call a tool directly without a framework:

```python
import os
from arcadepy import Arcade

client = Arcade(api_key=os.environ["ARCADE_API_KEY"])

# Start the authorization process for Slack
auth_response = client.tools.authorize(
    tool_name="Slack.SendDmToUser",
    user_id="user@example.com",
)

# If the tool is not already authorized, prompt the user to authenticate
if auth_response.status != "completed":
    print("Please authorize by visiting:")
    print(auth_response.authorization_url)
    client.auth.wait_for_completion(auth_response)

# Execute the tool to send a Slack message after authorization
tool_input = {
    "username": "sam",
    "message": "I'll be late to the meeting"
}
response = client.tools.execute(
    tool_name="Slack.SendDmToUser",
    input=tool_input,
    user_id="user@example.com",
)
print(response)

```

### Integrating with Agent Frameworks

You can also use the Tools API with a framework like LangChain or LangGraph.

Currently Arcade provides ease-of-use integrations for the following frameworks:

-   LangChain/Langgraph
-   CrewAI
-   LlamaIndex (coming soon)

Here's an example of how to use the Tools API with LangChain/Langgraph:

```python
import os
from langchain_arcade import ArcadeToolManager
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

arcade_api_key = os.environ["ARCADE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

manager = ArcadeToolManager(api_key=arcade_api_key)
tools = manager.get_tools(tools=["Slack.SendDmToUser"])

model = ChatOpenAI(
    model="gpt-4o",
    api_key=openai_api_key,
)

bound_model = model.bind_tools(tools)
graph = create_react_agent(model=bound_model, tools=tools)

config = {
    "configurable": {
        "thread_id": "1",
        "user_id": "user@unique_id.com",
    }
}
user_input = {
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant",
        },
        {
            "role": "user",
            "content": "Send sam a note that I'll be late to the meeting",
        },
    ]
}

for chunk in graph.stream(user_input, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
```

### Arcade Auth API

The Auth API provides the lowest-level integration with Arcade, for when you only need Arcade's authentication capabilities. This API is ideal for:

-   Framework developers building their own agent systems
-   Applications with existing tool execution mechanisms
-   Developers who need fine-grained control over LLM interactions and tool execution

With the Auth API, Arcade handles all the complex authentication tasks (OAuth flow management, link creation, token storage, refresh cycles), while you retain complete control over how you interact with LLMs and execute tools.

```python
from arcadepy import Arcade
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

client = Arcade()

# Get this user UNIQUE ID from a trusted source,
# like your database or user management system
user_id = "user@example.com"

# Start the authorization process
response = client.auth.start(
    user_id=user_id,
    provider="google",
    scopes=["https://www.googleapis.com/auth/gmail.readonly"],
)

if response.status != "completed":
    print("Please complete the authorization challenge in your browser:")
    print(response.url)

# Wait for the authorization to complete
auth_response = client.auth.wait_for_completion(response)

# Use the authorized token in your own tool execution logic
token = auth_response.context.token

# Example: Using the token with your own Gmail API implementation
credentials = Credentials(token=token)
gmail_service = build('gmail', 'v1', credentials=credentials)
emails = gmail_service.users().messages().list(userId='me').execute()
```

In this approach, you're responsible for:

-   LLM interactions to determine when tools should be called
-   Parsing LLM responses to extract tool calls
-   Executing the actual tool functionality
-   Formatting results for the LLM

But you can enable the multi-user functionality of Arcade into your own tool execution logic by using the Auth API.

## Client Libraries

-   **[ArcadeAI/arcade-py](https://github.com/ArcadeAI/arcade-py):**
    The Python client for interacting with Arcade.

-   **[ArcadeAI/arcade-js](https://github.com/ArcadeAI/arcade-js):**
    The JavaScript client for interacting with Arcade.

-   **[ArcadeAI/arcade-go](https://github.com/ArcadeAI/arcade-go):** (coming soon)
    The Go client for interacting with Arcade.

## Support and Community

-   **Discord:** Join our [Discord community](https://discord.com/invite/GUZEMpEZ9p) for real-time support and discussions.
-   **GitHub:** Contribute or report issues on the [Arcade GitHub repository](https://github.com/ArcadeAI/arcade-ai).
-   **Documentation:** Find in-depth guides and API references at [Arcade Documentation](https://docs.arcade.dev).
