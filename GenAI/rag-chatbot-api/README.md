# RAG Chatbot (FastAPI backend + React UI)

```
rag-chatbot-api/
├── backend/    FastAPI app, tests, Dockerfile, .env, data/
└── frontend/   React + Vite chat UI
```

**Run it** (two terminals):

```bash
# 1. backend  -> http://localhost:8000
cd backend
uvicorn app.main:app --reload

# 2. frontend -> http://localhost:3000
cd frontend
npm install
npm run dev
```

The UI has a conversation list, a streaming chat with clickable citations, and a side panel with
**Sources** (the passages behind an answer), **Library** (upload and delete PDFs) and **Memory**
(the session summary and user profile). The dev server forwards `/api` and `/health` to the backend.
If `API_KEY` is set in `backend/.env`, put the same value in `frontend/.env.local` as `VITE_API_KEY`.


A chatbot you can talk to over HTTP. It can:

- **search your PDFs** and answer with citations like `[handbook.pdf p.4]` (RAG)
- **use tools**: a calculator, a clock, a document search, and a "save this fact" tool
- **remember** the conversation, even long ones, and learn facts about the user

Capstone backend for **Phase 4 — Generative AI**:

| Week | Concept | File |
|---|---|---|
| 10 | Prompt engineering: system prompt, grounding rules, citations | `prompts.py` |
| 11 | Tool calling: tool menu, running tools, the tool loop | `tools.py`, `chat.py` |
| 11 | Multi-turn conversations saved in a database | `chat.py`, `database.py` |
| 11 | Memory: recent turns, running summary, vector recall, saved facts | `memory.py` |
| 11 | Structured output: a `UserProfile` pulled out of messages | `memory.py` |
| 12 | RAG: PDF → chunks → embeddings → ChromaDB | `documents.py`, `vector_store.py` |
| 12 | Two-step search: vector search, then rerank | `documents.py` |

## Read the code in this order

Every file is short and has comments explaining what's going on. The files are in `backend/app/`. Start at the top:

| # | File | What it does |
|---|---|---|
| 1 | `config.py` | All settings, read from `.env` |
| 2 | `prompts.py` | All the text we send to the LLM |
| 3 | `ai_models.py` | Loads the LLM, the embedding model and the reranker |
| 4 | `database.py` | Saves sessions, messages and documents in SQLite |
| 5 | `vector_store.py` | Saves and searches text by meaning, in ChromaDB |
| 6 | `documents.py` | Uploading PDFs and searching them (RAG) |
| 7 | `memory.py` | The four kinds of memory |
| 8 | `tools.py` | The tools, and what the LLM is told about them |
| 9 | `chat.py` | **The main part:** what happens when a message arrives |
| 10 | `main.py` | The web server: every URL of the API |

## What happens when you send a message

```
POST /api/v1/chat  {"message": "What's the refund policy?"}
        │
        ▼
1. Build the messages for the LLM  (chat.start_turn)
     system prompt  = rules + list of documents + memories
     + the last 6 turns
     + the new message
        │
        ▼
2. The tool loop  (chat.chat)
     ask the LLM ──► wants a tool? ──yes──► run it, add the result, ask again
                          │
                          no
                          ▼
                    final answer
        │
        ▼
3. Save the turn  (chat.finish_turn)
     messages table  +  long-term memory in ChromaDB
        │
        ▼
4. Reply goes back to the user. THEN, in the background  (chat.after_turn):
     fold the oldest turn into the summary  +  update the user profile
```

### The four kinds of memory (`memory.py`)

| Memory | What it keeps | Where it lives |
|---|---|---|
| Short-term | The last `MEMORY_WINDOW_TURNS` turns, word for word | `messages` table |
| Mid-term | A short summary of everything older | `sessions.summary` |
| Long-term | Every turn, searchable by meaning; plus facts saved with `save_memory` | ChromaDB `conversation_memory` |
| Profile | The user's name, job, goals, preferences... | `sessions.profile` |

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then open .env and add your API key
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** to try every endpoint from your browser.

The embedding model (~90 MB) and the reranker (~90 MB) download the first time you start. Set `RERANK_ENABLED=false` to skip the reranker.

**Other LLM providers:** install the provider's package (e.g. `pip install langchain-groq`) and set `LLM_PROVIDER=groq`, `LLM_MODEL=llama-3.3-70b-versatile`, `GROQ_API_KEY=…` in `.env`. To run fully on your own computer: `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.1` (choose a model that supports tools).

**Docker:** `docker compose up --build`

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Status, model name, number of documents and chunks |
| POST | `/api/v1/chat` | Send a message → reply, citations, tools used |
| POST | `/api/v1/chat/stream` | Same, but the reply arrives bit by bit |
| POST | `/api/v1/sessions` | Start a new conversation |
| GET | `/api/v1/sessions` | List conversations |
| GET | `/api/v1/sessions/{id}` | What the bot remembers: turn count, summary, profile |
| GET | `/api/v1/sessions/{id}/messages` | Every message in the conversation |
| DELETE | `/api/v1/sessions/{id}` | Delete a conversation and its memories |
| POST | `/api/v1/documents` | Upload a PDF (form field `file`) |
| GET | `/api/v1/documents` | List uploaded documents |
| DELETE | `/api/v1/documents/{doc_id}` | Delete a document |
| POST | `/api/v1/documents/search` | Search the PDFs without the LLM (for debugging) |

If `API_KEY` is set in `.env`, every `/api/v1/...` request needs the header `X-API-Key: <key>`.

### Examples

```bash
# 1. Upload a PDF
curl -F "file=@handbook.pdf" http://localhost:8000/api/v1/documents

# 2. Check the search works before involving the LLM
curl -X POST http://localhost:8000/api/v1/documents/search \
     -H "Content-Type: application/json" -d '{"query": "refund policy", "top_k": 3}'

# 3. Chat (leave out session_id to start a new conversation)
curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hi, I am Asha. What does the handbook say about refunds?"}'

# 4. Ask a follow-up in the same conversation
curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id": "<id from step 3>", "message": "And how long do I have?"}'

# 5. See what the bot remembers
curl http://localhost:8000/api/v1/sessions/<id>

# 6. Streaming
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
     -H "Content-Type: application/json" -d '{"message": "Summarize the shipping rules"}'
```

Example `/chat` reply:

```json
{
  "session_id": "3f2a…",
  "turn": 1,
  "reply": "Refunds are issued within 14 days of purchase, provided items are unused [handbook.pdf p.4].",
  "sources": [{"doc_id": "a1b2c3", "filename": "handbook.pdf", "page": 4, "score": 0.71,
               "rerank_score": 8.2, "text": "…", "snippet": "Refunds are issued within 14 days…"}],
  "tool_calls": [{"name": "search_documents", "args": {"query": "refund policy"}, "ok": true}]
}
```

The stream sends these events, in order: `session` → `tool` (0 or more) → `token` (many) → `sources` (if any) → `done`. If something fails you get an `error` event instead.

## Tests

The tests use a fake LLM and fake embeddings, so they need no API key and download nothing.

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Things we kept simple on purpose

This version favours readable code. A production app would also:

- **Lock each conversation** so two messages sent at the same moment to the same session can't overlap.
- **Keep one database connection open** instead of opening one for every query.
- **Use a safer calculator** (e.g. parse the expression with Python's `ast` module) so it can also support powers and functions like `sqrt`.

## Ideas for extending it

- **Hybrid search:** add keyword search (BM25, `rank-bm25`) and combine it with the vector search.
- **Background indexing:** index big PDFs in a background job and add a "status" endpoint.
- **Users:** add login, and give each user their own sessions and documents.
- **Evaluation:** a script that asks a list of questions and scores the answers (Week 10).
- **Monitoring:** log token usage and response time for each turn.
- **Production storage:** use Postgres instead of SQLite, and run Chroma as a server.
