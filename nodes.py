import json
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from state import AgentState
from model import get_model
from tools import (
    open_presentation_tool,
    close_presentation_tool,
    open_slide,
    list_presentations_tool,
)
from prompts import create_system_prompt, get_react_instructions

# Map name → tool
tools_by_name = {
    tool.name: tool
    for tool in [
        open_presentation_tool,
        close_presentation_tool,
        open_slide,
        list_presentations_tool,
    ]
}

def reflect_node(state: AgentState, config: RunnableConfig):
    """1) Reflect, plan & choose one tool call."""


    current_slide_info = (
        f"\n\nТекущий слайд: {state['current_slide']}" if state.get('current_slide') else ""
    )

    system = SystemMessage(
        create_system_prompt() +
        get_react_instructions() +
        current_slide_info
    )

    tools_list = [
        open_presentation_tool,
        close_presentation_tool,
        open_slide,
        list_presentations_tool,
    ]

    model = get_model(tools_list)
    response = model.invoke([system] + list(state["messages"]), config)

    return {"messages": [response]}

def use_tool_node(state: AgentState):
    """2) Execute the tool call chosen in reflect_node."""
    outputs = []
    last = state["messages"][-1]
    current_slide = state.get("current_slide")

    for call in last.tool_calls:
        result = tools_by_name[call["name"]].invoke(call["args"])

        if call["name"] == open_slide.name and result.get("status") == "ok":
            current_slide = result.get("slide_number")
        elif call["name"] == open_presentation_tool.name and result.get("status") == "ok":
            current_slide = 1
        elif call["name"] == close_presentation_tool.name and result.get("status") == "ok":
            current_slide = None

        outputs.append(
            ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                name=call["name"],
                tool_call_id=call["id"],
            )
        )
    return {"messages": outputs, "current_slide": current_slide}

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