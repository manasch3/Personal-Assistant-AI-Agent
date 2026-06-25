from langchain.chat_models import init_chat_model

base_llm = init_chat_model(
    "deepseek-chat",
    model_provider="deepseek",
    temperature=0.7,
)

memory_llm = init_chat_model(
    "deepseek-chat",
    model_provider="deepseek",
    temperature=0.2,
)
