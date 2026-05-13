import os
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.auth import create_token, verify_admin, ADMIN_USERNAME, ADMIN_PASSWORD
from src.vector_store import VectorStore
from src.ingestion import ingest_from_drive, ingest_pdf_bytes, ingest_docx_bytes, ingest_url
from src.llm import generate_answer

logger = logging.getLogger(__name__)

vs = VectorStore()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    vs.init()
    logger.info("RAG API v2 ready")
    yield


app = FastAPI(title="RAG API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
def login(req: LoginRequest):
    if req.username != ADMIN_USERNAME or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(req.username), "expires_in": 28800}


# ── Admin: Ingest ─────────────────────────────────────────────────────────────

class DriveIngestRequest(BaseModel):
    folder_id: str
    clear_first: bool = True


@app.post("/admin/ingest/drive")
@limiter.limit("5/minute")
def ingest_drive(request: Request, body: DriveIngestRequest, admin=Depends(verify_admin)):
    if body.clear_first:
        vs.clear()
    docs = ingest_from_drive(body.folder_id)
    if not docs:
        return {"documents": 0, "chunks": 0, "message": "No supported files found in folder"}
    total = sum(vs.add_document(d["text"], "drive", d["name"], d["id"]) for d in docs)
    return {"documents": len(docs), "chunks": total}


@app.post("/admin/ingest/file")
@limiter.limit("10/minute")
async def ingest_file(
    request: Request,
    file: UploadFile = File(...),
    clear_first: bool = Form(False),
    admin=Depends(verify_admin),
):
    content = await file.read()
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        text = ingest_pdf_bytes(content)
    elif ext == "docx":
        text = ingest_docx_bytes(content)
    elif ext in ("txt", "md"):
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(400, f"Unsupported file type .{ext} — supported: pdf, docx, txt, md")

    if not text.strip():
        raise HTTPException(400, "Could not extract text from file")

    if clear_first:
        vs.clear()

    chunks = vs.add_document(text, "upload", filename, str(uuid.uuid4()))
    return {"filename": filename, "chunks": chunks}


class URLIngestRequest(BaseModel):
    url: str
    clear_first: bool = False


@app.post("/admin/ingest/url")
@limiter.limit("5/minute")
def ingest_from_url(request: Request, body: URLIngestRequest, admin=Depends(verify_admin)):
    try:
        text = ingest_url(body.url)
    except Exception as exc:
        raise HTTPException(400, f"Failed to fetch URL: {exc}")
    if not text.strip():
        raise HTTPException(400, "No text content found at URL")
    if body.clear_first:
        vs.clear()
    chunks = vs.add_document(text, "url", body.url, str(uuid.uuid4()))
    return {"url": body.url, "chunks": chunks}


class TextIngestRequest(BaseModel):
    text: str
    title: str = "Manual Entry"
    clear_first: bool = False


@app.post("/admin/ingest/text")
def ingest_text(body: TextIngestRequest, admin=Depends(verify_admin)):
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    if body.clear_first:
        vs.clear()
    chunks = vs.add_document(body.text, "text", body.title, str(uuid.uuid4()))
    return {"title": body.title, "chunks": chunks}


# ── Admin: Documents ──────────────────────────────────────────────────────────

@app.get("/admin/documents")
def list_documents(admin=Depends(verify_admin)):
    return vs.list_documents()


@app.delete("/admin/documents/{doc_id}")
def delete_document(doc_id: str, admin=Depends(verify_admin)):
    vs.delete_document(doc_id)
    return {"deleted": doc_id}


@app.delete("/admin/collection")
def clear_collection(admin=Depends(verify_admin)):
    vs.clear()
    return {"message": "Knowledge base cleared"}


@app.get("/admin/stats")
def get_stats(admin=Depends(verify_admin)):
    return vs.get_stats()


# ── Chat (WordPress plugin + admin test) ──────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@app.post("/ask")
@limiter.limit("60/minute")
def ask(request: Request, body: ChatRequest):
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Question cannot be empty")
    context = vs.search(q)
    if not context:
        return {
            "question": q,
            "answer": "I don't have information about that in the knowledge base.",
            "context": "",
        }
    answer = generate_answer(q, context)
    return {"question": q, "answer": answer, "context": context}


# ── Health & Frontend ─────────────────────────────────────────────────────────

@app.get("/health")
def health():
    stats = vs.get_stats()
    return {"status": "ok", "version": "2.0.0", "chunks": stats.get("total_chunks", 0)}


@app.get("/")
def frontend():
    return FileResponse("index.html")
