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
        global agent_state
        # Append the new human message to the persistent state
        agent_state["messages"] = agent_state.get("messages", []) + [
            HumanMessage(content=request.text)
        ]

        # Remember previous number of AI responses to return only new ones
        prev_ai_count = len([m for m in agent_state["messages"] if isinstance(m, AIMessage)])

        # Run the graph with the current persistent state
        agent_state = graph.invoke(agent_state)

        # Extract only the AI responses produced in this invocation
        new_ai_msgs = [
            m.content
            for m in agent_state["messages"]
            if isinstance(m, AIMessage)
        ][prev_ai_count:]

        return {
            "responses": new_ai_msgs,
            "current_slide": agent_state.get("current_slide"),
        }

    return await asyncio.to_thread(_run)
