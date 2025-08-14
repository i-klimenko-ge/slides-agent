from typing import List, Dict, Any, Optional
from langchain_core.messages import (
    BaseMessage, AIMessage, ToolMessage
)


def _ai_tool_calls(ai: AIMessage) -> List[Dict[str, Any]]:
    """Return tool calls across common LC schemas."""
    if getattr(ai, "tool_calls", None):
        return ai.tool_calls
    ak = getattr(ai, "additional_kwargs", {}) or {}
    return ak.get("tool_calls", []) or ([ak["function_call"]] if "function_call" in ak else [])

def _assistant_call_ids(ai: AIMessage) -> List[str]:
    ids = []
    for tc in _ai_tool_calls(ai):
        ids.append(tc.get("id") or (tc.get("function", {}) or {}).get("name") or tc.get("name"))
    return [i for i in ids if i]

def _tool_call_id(tool_msg: ToolMessage) -> Optional[str]:
    # LC ToolMessage usually has tool_call_id; older function-style may only have name
    return getattr(tool_msg, "tool_call_id", None) or getattr(tool_msg, "name", None)

def stitch_tool_results_next_to_calls(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Reorder so every ToolMessage appears immediately after its matching AI tool call,
    even if a later HumanMessage arrived in between. Unknown/unmatched tool results are dropped.
    """
    # 1) index positions of assistant calls
    call_pos: Dict[str, int] = {}
    for idx, m in enumerate(messages):
        if isinstance(m, AIMessage):
            for cid in _assistant_call_ids(m):
                call_pos[cid] = idx

    # 2) collect tool results by call_id; remove them from the stream for now
    pending: Dict[str, List[ToolMessage]] = {}
    linear: List[BaseMessage] = []
    for m in messages:
        if isinstance(m, ToolMessage):
            cid = _tool_call_id(m)
            if cid and cid in call_pos:
                pending.setdefault(cid, []).append(m)
            # else: drop orphan/unknown tool result (safer for GigaChat)
        else:
            linear.append(m)

    # 3) insert tool results right after their call
    i = 0
    out: List[BaseMessage] = []
    while i < len(linear):
        m = linear[i]
        out.append(m)
        if isinstance(m, AIMessage):
            for cid in _assistant_call_ids(m):
                if cid in pending:
                    out.extend(pending.pop(cid))
        i += 1

    # 4) any leftovers (calls trimmed away) are discarded to avoid orphans
    return out

def drop_orphan_tool_results(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Remove tool/function messages that lack a matching earlier assistant call."""
    seen = set()
    out: List[BaseMessage] = []
    for m in messages:
        if isinstance(m, AIMessage) and _ai_tool_calls(m):
            seen.update(_assistant_call_ids(m))
            out.append(m)
        elif isinstance(m, ToolMessage):
            if _tool_call_id(m) in seen:
                out.append(m)  # keep only if we've seen its call
            # else drop
        else:
            out.append(m)
    return out