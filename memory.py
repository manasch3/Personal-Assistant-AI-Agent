import uuid
from typing import List

from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from langgraph.store.base import BaseStore

from llm import memory_llm

LTM_SYSTEM_PROMPT = """
You are Kiro with access to optional long-term user memory.

Use memory ONLY when it improves accuracy or relevance.
Do NOT force personalization.
Do NOT repeatedly mention the user’s name.

User memory:
{user_memory}
""".strip()

MEMORY_PROMPT = """
You manage long-term memory for an AI assistant.

Existing user memory:
{existing_memory}

TASK
- Extract ONLY stable, factual, long-term user information.

ALLOWED TO STORE
- User name (if explicitly stated)
- Education or role
- Long-term projects
- Preferred tools or frameworks
- Explicit learning preferences (only if clearly stated)

DO NOT STORE
- Tone or friendliness
- Temporary emotions
- Apologies or frustrations
- One-off questions
- Short-term preferences

RULES
- Each memory must be a short atomic fact.
- If the meaning already exists, mark is_new = false.
- If nothing is memory-worthy, return should_write = false.
- Never infer or guess.
""".strip()

class MemoryItem(BaseModel):
    text: str = Field(description="Atomic memory fact")
    is_new: bool

class MemoryDecision(BaseModel):
    should_write: bool
    memories: List[MemoryItem] = Field(default_factory=list)

memory_extractor = memory_llm.with_structured_output(MemoryDecision)

def remember_node(state: dict, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]
    namespace = ("user", user_id, "memory")

    existing_items = store.search(namespace)
    existing_memory = (
        "\n".join(i.value["data"] for i in existing_items)
        if existing_items
        else "(empty)"
    )

    last_user_message = state["messages"][-1].content

    if len(last_user_message.strip()) < 10:
        return {}  # Skip memory extraction for trivially short messages

    decision: MemoryDecision = memory_extractor.invoke(
        [
            SystemMessage(
                content=MEMORY_PROMPT.format(
                    existing_memory=existing_memory
                )
            ),
            {"role": "user", "content": last_user_message},
        ]
    )

    if decision.should_write:
        for mem in decision.memories:
            if mem.is_new:
                store.put(
                    namespace,
                    str(uuid.uuid4()),
                    {"data": mem.text}
                )

    return {}