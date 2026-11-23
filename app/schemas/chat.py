from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


class RestartConfirmRequest(BaseModel):
    hostname: str
    token: str
