import json
import uuid

from langchain_core.tools import tool

from app.services.memory_service import redis_client
from app.services.rag_service import search_knowledge as search_knowledge_docs

RESTART_TOKEN_TTL = 300


@tool
def check_server_status(hostname: str) -> dict:
    """查询指定服务器的运行状态（CPU、内存、健康状态）。

    Args:
        hostname: 服务器主机名，例如 web-01、db-02。
    """
    if "web" in hostname.lower():
        return {"cpu": "75%", "mem": "80%", "status": "warning"}
    return {"cpu": "20%", "mem": "30%", "status": "healthy"}


@tool
def search_knowledge(query: str) -> str:
    """当用户询问运维流程、排查步骤、操作规范或你不知道如何解决时，请调用此工具查阅内部知识库。

    Args:
        query: 要检索的问题，例如「web 服务器 CPU 飙高怎么排查」。
    """
    return search_knowledge_docs(query)


@tool
async def issue_restart_token(hostname: str) -> str:
    """重启服务器属于高危操作，调用本工具为目标主机签发一次性重启令牌。

    调用后必须把返回的 JSON 原样展示给用户，由用户点击确认后才能执行重启。

    Args:
        hostname: 需要重启的服务器主机名。
    """
    token = str(uuid.uuid4())
    await redis_client.set(f"restart_token:{token}", hostname, ex=RESTART_TOKEN_TTL)
    return json.dumps(
        {
            "action": "restart",
            "hostname": hostname,
            "token": token,
            "message": "高危操作已受理，请确认",
        },
        ensure_ascii=False,
    )


async def execute_restart(hostname: str, token: str) -> str:
    """校验一次性令牌并执行重启（模拟）。GETDEL 原子消费令牌，杜绝并发重复使用。"""
    key = f"restart_token:{token}"
    stored_hostname = await redis_client.getdel(key)
    if not stored_hostname:
        raise ValueError("令牌无效或已过期，请重新发起重启申请")
    if stored_hostname != hostname:
        raise ValueError("令牌与目标主机不匹配，令牌已失效")

    return f"服务器 {hostname} 重启成功（模拟）"
