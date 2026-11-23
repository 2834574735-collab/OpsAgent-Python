from langgraph.graph import END, StateGraph

from agent.nodes import chat_node, tool_node
from agent.state import AgentState


def route_after_chat(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


builder = StateGraph(AgentState)
builder.add_node("chat_node", chat_node)
builder.add_node("tool_node", tool_node)
builder.set_entry_point("chat_node")
builder.add_conditional_edges(
    "chat_node",
    route_after_chat,
    {"tool_node": "tool_node", END: END},
)
builder.add_edge("tool_node", "chat_node")

graph = builder.compile()
