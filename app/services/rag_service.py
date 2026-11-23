from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "ops_knowledge"
EMBEDDING_MODEL = "text-embedding-v3"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 复用千问兼容 OpenAI 的 embedding 接口，无需额外依赖或本地模型下载
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=settings.dashscope_api_key,
    base_url=DASHSCOPE_BASE_URL,
    check_embedding_ctx_length=False,
)

_vector_store: Chroma | None = None


def _get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )
    return _vector_store


def load_and_index_docs() -> int:
    """加载 docs/ 下的 Markdown 并写入 Chroma，已存在索引时跳过。返回新增片段数。"""
    store = _get_vector_store()

    if store.get(limit=1)["ids"]:
        return 0

    documents = [
        Document(
            page_content=path.read_text(encoding="utf-8"),
            metadata={"source": path.name},
        )
        for path in sorted(DOCS_DIR.glob("*.md"))
    ]
    if not documents:
        return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    store.add_documents(chunks)
    return len(chunks)


def search_knowledge(query: str) -> str:
    """在知识库中检索与问题最相关的 2 个片段并拼接返回。"""
    docs = _get_vector_store().similarity_search(query, k=2)
    if not docs:
        return "知识库中未找到相关内容。"

    return "\n\n".join(
        f"【{doc.metadata.get('source', '知识库')}】\n{doc.page_content}" for doc in docs
    )
