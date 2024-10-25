import time

# Import necessary classes and modules
from langchain_arcade import ArcadeToolManager
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# Initialize the tool manager and fetch tools compatible with langgraph
tool_manager = ArcadeToolManager()
tools = tool_manager.get_tools(langgraph=True)
tool_node = ToolNode(tools)

# Create a language model instance and bind it with the tools
model = ChatOpenAI(model="gpt-4o")
model_with_tools = model.bind_tools(tools)


# Function to invoke the model and get a response
def call_agent(state):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    # Return the updated message history
    return {"messages": [*messages, response]}


# Function to determine the next step in the workflow based on the last message
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        tool_name = last_message.tool_calls[0]["name"]
        if tool_manager.requires_auth(tool_name):
            return "authorization"  # Proceed to authorization if required
        else:
            return "tools"  # Proceed to tool execution if no authorization is needed
    return END  # End the workflow if no tool calls are present


# Function to handle authorization for tools that require it
def authorize(state: MessagesState, config: dict):
    user_id = config["configurable"].get("user_id")
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    auth_response = tool_manager.authorize(tool_name, user_id)
    if auth_response.status == "completed":
        # Authorization completed successfully; continue
        return {"messages": state["messages"]}
    else:
        # Prompt the user to visit the authorization URL
        print(f"Visit the following URL to authorize: {auth_response.authorization_url}")
        # Wait until authorization is completed
        while not tool_manager.is_authorized(auth_response.authorization_id):
            time.sleep(1)
        return {"messages": state["messages"]}


# Build the workflow graph using StateGraph
workflow = StateGraph(MessagesState)

# Add nodes (steps) to the graph
workflow.add_node("agent", call_agent)
workflow.add_node("tools", tool_node)
workflow.add_node("authorization", authorize)

# Define the edges and control flow between nodes
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["authorization", "tools", END])
workflow.add_edge("authorization", "tools")
workflow.add_edge("tools", "agent")

# Set up memory for checkpointing the state
memory = MemorySaver()

# Compile the graph with the checkpointer
graph = workflow.compile(checkpointer=memory)

# Define the input messages from the user
inputs = {
    "messages": [HumanMessage(content="Star arcadeai/arcade-ai on GitHub!")],
}

# Configuration with thread and user IDs for authorization purposes
config = {
    "configurable": {
        "thread_id": "4",
        "user_id": "sam@arcade-ai.com",
    }
}

# Run the graph and stream the outputs
for chunk in graph.stream(inputs, config=config, stream_mode="values"):
    # Pretty-print the last message in the chunk
    chunk["messages"][-1].pretty_print()
