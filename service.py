"""FastAPI service exposing slide-control endpoints and an agent interface."""

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from tools import next_slide, previous_slide
from langchain_core.messages import HumanMessage, AIMessage
from graph import graph
from state import AgentState

app = FastAPI()

# In-memory persistent state for the agent
agent_state: AgentState = {"messages": [], "current_slide": None}

class AgentRequest(BaseModel):
    text: str

@app.post("/next-slide")
async def api_next_slide():
    def _run():
        global agent_state
        result = next_slide.invoke({})
        if result.get("status") == "ok":
            agent_state["current_slide"] = result.get("slide_number")
        return result

    return await asyncio.to_thread(_run)

@app.post("/previous-slide")
async def api_previous_slide():
    def _run():
        global agent_state
        result = previous_slide.invoke({})
        if result.get("status") == "ok":
            agent_state["current_slide"] = result.get("slide_number")
        return result

    return await asyncio.to_thread(_run)

@app.post("/run-agent")
async def run_agent(request: AgentRequest):
    def _run() -> dict:
        """Run the agent and print responses as they are produced."""
        global agent_state
        # Add the human message to persistent state
        agent_state["messages"] = agent_state.get("messages", []) + [
            HumanMessage(content=request.text)
        ]

        # Stream through the graph so each response is handled immediately
        stream = graph.stream(agent_state, stream_mode="values")

        for step in stream:
            msg = step["messages"][-1]
            try:
                if msg in agent_state["messages"]:
                    continue

                if isinstance(msg, AIMessage):
                    print("Response:", msg.content)
                else:
                    msg.pretty_print()

                agent_state["messages"].append(msg)
                if step.get("current_slide") is not None:
                    agent_state["current_slide"] = step["current_slide"]
            except AttributeError:
                print(msg)

        print("Current slide:", agent_state.get("current_slide"))
        return {"status": "ok"}

    return await asyncio.to_thread(_run)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
