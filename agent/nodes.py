from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.tools import check_server_status, issue_restart_token, search_knowledge
from app.core.config import settings

llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.dashscope_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

tools = [check_server_status, search_knowledge, issue_restart_token]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(
    content=(
        "你是 OpsAgent 运维助手。查询服务器状态时调用 check_server_status。"
        "当用户询问运维流程、排查步骤、操作规范或你不知道如何解决时，先调用 search_knowledge 查阅内部知识库。"
        "当用户要求重启服务器时，必须先调用 issue_restart_token 申请一次性重启令牌，"
        "然后把工具返回的 JSON 原样附加在回复末尾，提示用户点击确认重启。"
        "禁止声称已经执行重启，重启只能由用户在前端点击确认后完成。"
    )
)


async def chat_node(state: AgentState) -> dict:
    response = await llm_with_tools.ainvoke([SYSTEM_PROMPT, *state["messages"]])
    return {"messages": [response]}


tool_node = ToolNode(tools)
