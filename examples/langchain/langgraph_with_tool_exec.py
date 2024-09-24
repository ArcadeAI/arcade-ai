import json
import os
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, START, StateGraph

from arcade.client import Arcade

client = Arcade(api_key=os.environ["ARCADE_API_KEY"], base_url="http://127.0.0.1:9099")


class State(TypedDict):
    emails: Any


def step_1(state: State, config) -> State:
    user_id = config["configurable"]["user_id"]

    challenge = client.tool.authorize(
        tool_name="ListEmails",
        user_id=user_id,
    )

    if challenge.status != "completed":
        raise NodeInterrupt(f"Please visit this URL to authorize: {challenge.auth_url}")

    result = client.tool.run(
        tool_name="ListEmails",
        user_id=user_id,
        tool_version="default",
        inputs=json.dumps({"n_emails": 5}),
    )
    return {"emails": result}


builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", END)

# Set up memory
memory = MemorySaver()

# Compile the graph with memory
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "2", "user_id": "sam@arcade-ai.com"}}
result = graph.invoke({"emails": None}, config=config)
state = graph.get_state({"configurable": {"thread_id": "2"}})
print("interrupted state\n----------")
print(state)
print("----------")
input()
result = graph.invoke({"emails": None}, config=config)
state = graph.get_state({"configurable": {"thread_id": "2"}})
print("final state\n----------")
print(state)
print("----------")
print("final result\n----------")
print(result)
print("----------")
