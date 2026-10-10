"""
main.py - The web server. Every URL (endpoint) of the API is defined in this file.

Start the server with:
    uvicorn app.main:app --reload

Then open http://localhost:8000/docs to try every endpoint in your browser.

A quick FastAPI reminder:
    @app.get("/health")             -> this function runs when someone visits GET /health
    def chat(request: ChatRequest)  -> FastAPI reads the JSON body into a ChatRequest object
    raise HTTPException(404, "...") -> send an error back to the client
    return {...}                    -> sent back to the client as JSON
"""
import json

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import ai_models, chat, config, database, documents, memory, vector_store

app = FastAPI(title=config.APP_NAME,
              description="Chatbot backend with tool calling, memory and RAG over PDFs.")

# Allow web pages on other addresses (e.g. a React app on localhost:3000) to call this API.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    """Runs once when the server starts."""
    database.create_tables()
    vector_store.connect()
    if ai_models.llm is None:   # the tests put fake models here before starting
        ai_models.load_models()


# =================================================================== security

def check_api_key(x_api_key: str = Header(default=None)):
    """If an API_KEY is set in .env, every /api request must send it in the X-API-Key header."""
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(401, "Invalid or missing X-API-Key header")


# Adding this to an endpoint makes it run check_api_key() first.
PROTECTED = [Depends(check_api_key)]


# ============================================================ request formats
# These classes describe the JSON the client must send. FastAPI checks it for us.

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None   # leave out to start a new conversation


class SessionCreate(BaseModel):
    title: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=20)   # ge = "greater or equal", le = "less or equal"
    doc_id: str | None = None


# ===================================================================== health

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": f"{config.LLM_PROVIDER}:{config.LLM_MODEL}",
        "documents": len(database.list_documents()),
        "indexed_chunks": vector_store.count("documents"),
        "reranker": ai_models.reranker is not None,
    }


# ======================================================================= chat

def get_or_create_session(session_id):
    if session_id is None:
        return database.create_session()
    if database.get_session(session_id) is None:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session_id


@app.post("/api/v1/chat", dependencies=PROTECTED)
def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    """Send a message and get the full reply (with citations and the tools that were used)."""
    session_id = get_or_create_session(request.session_id)
    try:
        print("Inside Chat API!")
        print(f"Question = {request.message}")
        result = chat.chat(session_id, request.message)
    except Exception as error:
        raise HTTPException(502, f"LLM error: {error}")

    # Update the summary and profile AFTER the reply has been sent, so the user doesn't wait.
    background_tasks.add_task(chat.after_turn, session_id, request.message)
    return result


@app.post("/api/v1/chat/stream", dependencies=PROTECTED)
def send_message_stream(request: ChatRequest):
    """Same as /chat, but the reply arrives bit by bit (Server-Sent Events).

    Each event looks like:   event: token
                             data: "Hel"
    """
    session_id = get_or_create_session(request.session_id)

    def events():
        yield format_event("session", {"session_id": session_id})
        for event in chat.chat_stream(session_id, request.message):
            yield format_event(event["event"], event["data"])

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


def format_event(name, data):
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# =================================================================== sessions

@app.post("/api/v1/sessions", status_code=201, dependencies=PROTECTED)
def create_session(body: SessionCreate | None = None):
    title = body.title if body else None
    session_id = database.create_session(title)
    return database.get_session(session_id)


@app.get("/api/v1/sessions", dependencies=PROTECTED)
def list_sessions(limit: int = 50):
    return database.list_sessions(limit)


@app.get("/api/v1/sessions/{session_id}", dependencies=PROTECTED)
def get_session(session_id: str):
    """Shows what the bot remembers: turn count, summary and the user profile."""
    session = database.get_session(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    session["recent_turns"] = min(session["turn"], config.MEMORY_WINDOW_TURNS)
    return session


@app.get("/api/v1/sessions/{session_id}/messages", dependencies=PROTECTED)
def get_messages(session_id: str):
    if database.get_session(session_id) is None:
        raise HTTPException(404, "Session not found")
    return database.get_messages(session_id)


@app.delete("/api/v1/sessions/{session_id}", status_code=204, dependencies=PROTECTED)
def delete_session(session_id: str):
    """Deletes the session, its messages and its long-term memories."""
    if database.get_session(session_id) is None:
        raise HTTPException(404, "Session not found")
    database.delete_session(session_id)
    memory.forget_session(session_id)


# ================================================================== documents

@app.post("/api/v1/documents", status_code=201, dependencies=PROTECTED)
def upload_document(file: UploadFile):
    """Upload a PDF. It gets split into chunks, embedded and saved in ChromaDB."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(415, "Only PDF files are supported")

    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File is bigger than {config.MAX_UPLOAD_MB} MB")
    if not data.startswith(b"%PDF"):   # every real PDF file starts with these 4 bytes
        raise HTTPException(422, "File is not a valid PDF")

    try:
        return documents.add_pdf(data, file.filename)
    except ValueError as error:
        raise HTTPException(422, str(error))


@app.get("/api/v1/documents", dependencies=PROTECTED)
def list_documents():
    return database.list_documents()


@app.delete("/api/v1/documents/{doc_id}", status_code=204, dependencies=PROTECTED)
def delete_document(doc_id: str):
    if not documents.delete_pdf(doc_id):
        raise HTTPException(404, "Document not found")


@app.post("/api/v1/documents/search", dependencies=PROTECTED)
def search_documents(request: SearchRequest):
    """Search only, no LLM. Handy for checking what the chatbot would find."""
    results = documents.search(request.query, request.top_k, request.doc_id)
    return {"query": request.query, "results": results}
