import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mcp.drive_ingest import ingest_from_drive
from mcp.chunk import chunk_text
from mcp.embed_and_upload import embed_and_upload_chunks
from mcp.embed_qes import get_question_embedding
from mcp.search_quad import search_context
from mcp.llm_response import get_llm_response
from mcp.clear_collection import clear_collection


# Load environment variables
load_dotenv(override=True)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

port = int(os.getenv("PORT", 3000))


# Request/Response models
class IngestRequest(BaseModel):
    folderId: str


class AskRequest(BaseModel):
    question: str


class IngestResponse(BaseModel):
    message: str
    documents: int
    chunks: int


class AskResponse(BaseModel):
    question: str
    context: str
    answer: str


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest):
    """Ingest PDFs from Google Drive, chunk them, and upload to Qdrant."""
    if not request.folderId:
        raise HTTPException(status_code=400, detail="Missing folderId in request body")

    try:
        documents = ingest_from_drive(request.folderId)
        all_chunks = [
            chunk for doc in documents
            for chunk in chunk_text(doc["text"], 100, 50)
            if chunk.strip()
        ]
        embed_and_upload_chunks(all_chunks)

        return IngestResponse(
            message="Ingestion, chunking, embedding, and upload successful",
            documents=len(documents),
            chunks=len(all_chunks)
        )
    except Exception as error:
        print(f"❌ Error in /ingest: {error}")
        raise HTTPException(status_code=500, detail="Failed to ingest and update vector DB")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Answer a question using RAG."""
    if not request.question:
        raise HTTPException(status_code=400, detail="Missing question in request body")
    print(f"❓ Received question: {request.question}")

    try:
        print("🔍 Generating embedding for the question...")
        embedding = get_question_embedding(request.question)
        print(f"✅ Embedding generated successfully : length={len(embedding)}")
        print("🔎 Searching for relevant context in Qdrant...")
        context = search_context(embedding)
        print(f"✅ Context retrieved successfully : \n context={context}")
        print("💡 Generating answer from LLM...")
        answer = get_llm_response(context, request.question)
        print(f"✅ Answer generated successfully : \n answer={answer}")

        return AskResponse(
            question=request.question,
            context=context,
            answer=answer
        )
    except Exception as error:
        print(f"❌ Error in /ask: {error}")
        raise HTTPException(status_code=500, detail="Failed to generate answer")


@app.post("/clear")
def clear_db():
    """Clear all documents from the vector database."""
    result = clear_collection()

    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to clear collection"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
