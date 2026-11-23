import json

from langchain_core.messages import AIMessage, HumanMessage
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

HISTORY_TTL = 1800  # 30 分钟
KEY_PREFIX = "chat:history:"

pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)
redis_client = Redis(connection_pool=pool)


def _key(session_id: str) -> str:
    return f"{KEY_PREFIX}{session_id}"


async def get_history(session_id: str) -> list:
    """从 Redis 读取会话历史，反序列化为 HumanMessage / AIMessage 列表。"""
    raw = await redis_client.get(_key(session_id))
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    history = []
    for item in data:
        role = item.get("type")
        content = item.get("content", "")
        if role == "human":
            history.append(HumanMessage(content=content))
        elif role == "ai":
            history.append(AIMessage(content=content))
    return history


async def save_history(session_id: str, messages: list) -> None:
    """将消息列表（仅保留 type 和 content）写入 Redis，30 分钟后过期。"""
    data = [
        {
            "type": "human" if isinstance(message, HumanMessage) else "ai",
            "content": message.content,
        }
        for message in messages
        if isinstance(message, (HumanMessage, AIMessage)) and isinstance(message.content, str) and message.content
    ]
    await redis_client.set(_key(session_id), json.dumps(data, ensure_ascii=False), ex=HISTORY_TTL)
