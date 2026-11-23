import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.chat import router as chat_router
from app.services.rag_service import load_and_index_docs

logger = logging.getLogger("opsagent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="OpsAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1")


@app.on_event("startup")
def init_knowledge_base() -> None:
    try:
        added = load_and_index_docs()
        if added:
            logger.info("RAG 知识库初始化完成，新增 %s 个片段", added)
        else:
            logger.info("RAG 知识库已存在索引，跳过初始化")
    except Exception:
        logger.exception("RAG 知识库初始化失败，检索工具将不可用")


@app.get("/health")
async def health():
    return {"status": "ok"}
