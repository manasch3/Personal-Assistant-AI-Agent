import re
from datetime import datetime
from typing import Annotated, TypedDict

from dateutil import parser as dateutil_parser
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore

from brain import build_chatbot_instructions
from llm import base_llm
from memory import LTM_SYSTEM_PROMPT, remember_node
from tools import tools

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------------------------------------------------------
# Time guard helpers (inline — only used by chat_node)
# ---------------------------------------------------------------------------

_DATE_PATTERN = re.compile(
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})"
    r"|(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})"
    r"|(?:\d{4}-\d{2}-\d{2})"
    r"|(?:\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)

def _extract_date_status(text: str):
    """Return 'future', 'present', 'past', or None if no recognisable date found."""
    match = _DATE_PATTERN.search(text)
    if not match:
        return None
    try:
        found_date = dateutil_parser.parse(match.group()).date()
        today = datetime.now().date()
        if found_date > today:
            return "future"
        elif found_date == today:
            return "present"
        return "past"
    except Exception:
        return None


def _is_future_event_query(user_text: str) -> bool:
    """Ask the LLM with a tiny prompt whether the user is asking about a future event."""
    result = base_llm.invoke(
        [
            SystemMessage(content="Answer ONLY with YES or NO.\nIs the user asking about a future or upcoming event?"),
            HumanMessage(content=user_text),
        ]
    )
    return result.content.strip().upper() == "YES"


# ---------------------------------------------------------------------------
# LLM with tools bound
# ---------------------------------------------------------------------------

_llm_with_tools = base_llm.bind_tools(tools, parallel_tool_calls=False)


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def chat_node(state: ChatState, config: RunnableConfig, *, store) -> dict:
    user_id = config["configurable"]["user_id"]
    namespace = ("user", user_id, "memory")

    # Load long-term memory for this user
    items = store.search(namespace)
    user_memory = "\n".join(i.value["data"] for i in items) if items else ""

    system_message = SystemMessage(
        content=(
            build_chatbot_instructions()
            + "\n\n"
            + LTM_SYSTEM_PROMPT.format(user_memory=user_memory or "(empty)")
        )
    )

    # Find the actual last human message (not a ToolMessage on re-entry after tools)
    last_user_msg = next(
        (msg.content for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)),
        None,
    )

    response = _llm_with_tools.invoke([system_message] + state["messages"])

    # Time guard: only run when the LLM gave a direct text response (no tool calls)
    # and that response contains a date — avoids wasting an extra LLM call otherwise.
    if not response.tool_calls and last_user_msg:
        date_status = _extract_date_status(response.content)
        if date_status in ("past", "present") and _is_future_event_query(last_user_msg):
            response = base_llm.invoke(
                [system_message]
                + state["messages"]
                + [SystemMessage(content="The next event date cannot be reliably determined. Inform the user.")]
            )

    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

_graph = StateGraph(ChatState)
_graph.add_node("remember", remember_node)
_graph.add_node("chat", chat_node)
_graph.add_node("tools", ToolNode(tools))

_graph.add_edge(START, "remember")
_graph.add_edge("remember", "chat")
_graph.add_conditional_edges("chat", tools_condition)
_graph.add_edge("tools", "chat")

agent = _graph.compile(
    checkpointer=InMemorySaver(),
    store=InMemoryStore()
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_CONFIG = {"configurable": {"thread_id": "ui", "user_id": "manas"}}


def _extract_used_tools(messages: list) -> list[str]:
    """Return deduplicated list of tool names used since the last human message."""
    last_human_idx = next(
        (i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)),
        None,
    )
    if last_human_idx is None:
        return []
    seen = []
    for msg in messages[last_human_idx + 1:]:
        if isinstance(msg, ToolMessage) and msg.name and msg.name not in seen:
            seen.append(msg.name)
    return seen


def get_response(user_message: str, history: dict) -> dict:
    """
    Send a user message to the agent and return the reply.

    Args:
        user_message: The raw user input string.
        history:      The current conversation state dict ({"messages": [...]}).

    Returns:
        {
            "reply":   str        — the assistant's response text,
            "tools":   list[str]  — tool names used this turn (may be empty),
            "history": dict       — updated conversation state to pass on the next call,
        }
    """
    history["messages"].append(HumanMessage(content=user_message))
    history = agent.invoke(history, config=_CONFIG)
    return {
        "reply":   history["messages"][-1].content,
        "tools":   _extract_used_tools(history["messages"]),
        "history": history,
    }
