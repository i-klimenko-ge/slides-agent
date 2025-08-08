from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from tools import next_slide, previous_slide
from langchain_core.messages import HumanMessage, AIMessage
from graph import graph

app = FastAPI()

class AgentRequest(BaseModel):
    text: str

@app.post("/next-slide")
async def api_next_slide():
    return await asyncio.to_thread(lambda: next_slide.invoke({}))

@app.post("/previous-slide")
async def api_previous_slide():
    return await asyncio.to_thread(lambda: previous_slide.invoke({}))

@app.post("/run-agent")
async def run_agent(request: AgentRequest):
    def _run() -> dict:
        state = {"messages": [HumanMessage(content=request.text)], "current_slide": None}
        result = graph.invoke(state)
        responses = [m.content for m in result["messages"] if isinstance(m, AIMessage)]
        return {"responses": responses, "current_slide": result.get("current_slide")}

    return await asyncio.to_thread(_run)
