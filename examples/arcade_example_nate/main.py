from datetime import datetime
from typing import ClassVar, Union
from arcade.actor.fastapi.actor import FastAPIActor
from arcade.core.catalog import ToolCatalog
from arcade.core.executor import ToolExecutor
from arcade.core.tool import ToolDefinition
from arcade.core.toolkit import Toolkit
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from openai import AsyncOpenAI


client = AsyncOpenAI(base_url="http://localhost:6901")

app = FastAPI()

# Import toolkit
my_toolkit = Toolkit.from_directory(".")

actor = FastAPIActor(app)
actor.register_toolkit(arithmetic_toolkit)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message},
            ],
            model="gpt-4o-mini",
            max_tokens=150,
            tool_choice="execute",
        )
        return {"response": chat_completion.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
