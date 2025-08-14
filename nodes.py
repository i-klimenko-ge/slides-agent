"""Graph nodes that plan actions and execute slide-control tools."""

import json
import time
from langchain_core.messages import SystemMessage, HumanMessage, trim_messages
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from state import AgentState
from model import get_model
from tools import (
    open_presentation_tool,
    open_slide,
    next_slide,
    previous_slide,
    list_presentations_tool,
    list_slides_tool,
)
from helpers import stitch_tool_results_next_to_calls, drop_orphan_tool_results
from prompts import create_system_prompt

# Shared list of slide-control tools
slide_tools = [
    open_presentation_tool,
    open_slide,
    next_slide,
    previous_slide,
    list_presentations_tool,
    list_slides_tool,
]

# Prebuilt node for executing tools
tool_node = ToolNode(slide_tools)

def reflect_node(state: AgentState, config: RunnableConfig, max_attempts = 5):
    """1) Reflect, plan & choose one tool call."""

    system = SystemMessage(
        create_system_prompt()
        + get_presentation_info(state)
    )

    model = get_model(slide_tools)

    # Stitch history so tool results sit right after their assistant call
    history = stitch_tool_results_next_to_calls(list(state["messages"]))

    conversation = [system] + history

    conversation = trim_messages(
        conversation,
        token_counter=model,
        max_tokens=10000,
        strategy="last",
        start_on="human",
        include_system=True,
        allow_partial=False,
    )

    # drop any orphans that trimming might have created
    conversation = drop_orphan_tool_results(conversation)

    # retry invoking the model in case of transient failures
    for attempt in range(1, max_attempts + 1):
        try:
            response = model.invoke(conversation, config)
            break
        except Exception:
            if attempt == max_attempts:
                raise
            coef = 0.2
            time.sleep(coef * (2 ** (attempt - 1)))

    return {"messages": [response]}

def use_tool_node(state: AgentState, config: RunnableConfig):
    """2) Execute the tool call chosen in reflect_node using ToolNode."""
    # Run tools with the prebuilt ToolNode
    result = tool_node.invoke(state, config)

    current_slide = state.get("current_slide")
    current_presentation = state.get("current_presentation")
    outputs = result["messages"]

    # Inspect tool results to track the current slide and presentation
    for message in outputs:
        try:
            data = json.loads(message.content)
        except json.JSONDecodeError:
            continue

        if message.name == open_slide.name and data.get("status") == "ok":
            current_slide = data.get("slide_number")
        elif message.name == open_presentation_tool.name and data.get("status") == "ok":
            current_slide = 1
            current_presentation = data.get("presentation_name")
        elif (
            message.name in {next_slide.name, previous_slide.name}
            and data.get("status") == "ok"
        ):
            current_slide = data.get("slide_number")

    return {
        "messages": outputs,
        "current_slide": current_slide,
        "current_presentation": current_presentation,
    }

def should_use_tool(state: AgentState):
    """If the last LLM output included a tool call, go to execute; otherwise end."""
    last = state["messages"][-1]
    return "use_tool" if last.tool_calls else "end"

def get_searches_left(state: AgentState, max_searches: int = 5):
    searches = 0

    for m in reversed(state["messages"]):
        if m.name == 'search_rag':
            searches += 1
        # counting down searches to the last human message
        elif isinstance(m, HumanMessage):
            break
    return max_searches - searches

def get_presentation_info(state: AgentState):

    current_presentation = state['current_presentation'] if state.get('current_presentation') else "Нет"
    current_slide = state['current_slide'] if state.get('current_slide') else "Нет"

    return f"\n\nТекущая презентация: {current_presentation}\nТекущий слайд: {current_slide}"
