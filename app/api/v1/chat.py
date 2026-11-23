from fastapi import APIRouter, HTTPException

from agent.tools import execute_restart
from app.schemas.chat import ChatRequest, RestartConfirmRequest
from app.services.agent_service import get_agent_response

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    reply = await get_agent_response(request.message, request.session_id)
    return {"reply": reply}


@router.post("/restart/confirm")
async def confirm_restart(request: RestartConfirmRequest):
    try:
        message = await execute_restart(request.hostname, request.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"reply": message}
