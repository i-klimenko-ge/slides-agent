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
agent_state: AgentState = {
    "messages": [],
    "current_slide": None,
    "current_presentation": None,
}

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
                if step.get("current_presentation") is not None:
                    agent_state["current_presentation"] = step["current_presentation"]
            except AttributeError:
                print(msg)

        print("Current slide:", agent_state.get("current_slide"))
        print("Current presentation:", agent_state.get("current_presentation"))
        return {"status": "ok"}

    return await asyncio.to_thread(_run)


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Run the slide-control FastAPI service")
    parser.add_argument("--port", type=int, default=8000, help="Port number to run the service on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the service to (default: 0.0.0.0)")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
