from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    topic: str
    search_queries: list[str]
    queries_done: int
    raw_results: list[dict[str, Any]]
    structured_data: list[dict[str, Any]]
    synthesis: str
    report_markdown: str
    error: str | None

    