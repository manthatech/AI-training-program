import json

from app import config, memory

API = "/api/v1"


def upload(client, pdf_bytes, name="policy.pdf"):
    return client.post(f"{API}/documents", files={"file": (name, pdf_bytes, "application/pdf")})


def parse_events(text):
    """Turn a Server-Sent Events response into a list of (event_name, data) pairs."""
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


# ------------------------------------------------------------------ health
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# --------------------------------------------------------------- documents
def test_upload_list_search_delete_document(client, pdf_bytes):
    response = upload(client, pdf_bytes)
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["pages"] == 2 and doc["chunks"] >= 2

    assert [d["id"] for d in client.get(f"{API}/documents").json()] == [doc["id"]]

    results = client.post(f"{API}/documents/search", json={"query": "refund", "top_k": 2}).json()["results"]
    assert len(results) == 2
    assert {r["page"] for r in results} <= {1, 2}
    assert all(r["filename"] == "policy.pdf" for r in results)

    assert client.delete(f"{API}/documents/{doc['id']}").status_code == 204
    assert client.get(f"{API}/documents").json() == []
    assert client.get("/health").json()["indexed_chunks"] == 0


def test_rejects_non_pdf(client):
    response = client.post(f"{API}/documents", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_rejects_fake_pdf(client):
    response = client.post(f"{API}/documents", files={"file": ("x.pdf", b"not a pdf", "application/pdf")})
    assert response.status_code == 422


# -------------------------------------------------------------------- chat
def test_chat_creates_session_and_answers(client):
    response = client.post(f"{API}/chat", json={"message": "Hello there"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_id"] and body["turn"] == 1
    assert body["reply"] == "Echo: Hello there"


def test_chat_rag_tool_returns_sources(client, pdf_bytes):
    upload(client, pdf_bytes)
    body = client.post(f"{API}/chat", json={"message": "What is the refund policy?"}).json()
    assert [t["name"] for t in body["tool_calls"]] == ["search_documents"]
    assert body["tool_calls"][0]["ok"] is True
    assert body["sources"] and body["sources"][0]["filename"] == "policy.pdf"
    assert "policy.pdf p." in body["reply"]


def test_chat_calculator_tool(client):
    body = client.post(f"{API}/chat", json={"message": "calculate something"}).json()
    assert body["tool_calls"][0]["name"] == "calculator"
    assert "14" in body["reply"]


def test_unknown_session_404(client):
    response = client.post(f"{API}/chat", json={"message": "hi", "session_id": "nope"})
    assert response.status_code == 404


def test_multi_turn_history_and_profile(client):
    session_id = client.post(f"{API}/chat", json={"message": "Hi, I'm Asha"}).json()["session_id"]
    client.post(f"{API}/chat", json={"message": "second message", "session_id": session_id})

    messages = client.get(f"{API}/sessions/{session_id}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]

    session = client.get(f"{API}/sessions/{session_id}").json()
    assert session["turn"] == 2
    assert session["title"] == "Hi, I'm Asha"
    assert session["profile"]["name"] == "Asha"     # pulled out with structured output


def test_summary_after_window(client):
    session_id = None
    for i in range(4):                               # the window is 2 turns in the tests
        body = client.post(f"{API}/chat", json={"message": f"message {i}", "session_id": session_id}).json()
        session_id = body["session_id"]
    session = client.get(f"{API}/sessions/{session_id}").json()
    assert session["recent_turns"] == 2
    assert session["summary"].startswith("SUMMARY")


def test_short_term_window_has_the_right_turns(client):
    session_id = None
    for i in range(1, 5):
        session_id = client.post(f"{API}/chat", json={"message": f"message {i}", "session_id": session_id}).json()["session_id"]
    recent = memory.recent_messages(session_id, last_turn=4)
    assert [m.content for m in recent if m.type == "human"] == ["message 3", "message 4"]


def test_save_memory_tool_and_recall(client):
    session_id = client.post(f"{API}/chat", json={"message": "Please remember I love hiking"}).json()["session_id"]
    recalled = memory.recall(session_id, "hiking", last_turn=1)
    assert any("Saved fact" in text for text in recalled)


def test_sessions_list_and_delete(client):
    session_id = client.post(f"{API}/sessions", json={"title": "Demo"}).json()["id"]
    assert any(s["id"] == session_id for s in client.get(f"{API}/sessions").json())
    assert client.delete(f"{API}/sessions/{session_id}").status_code == 204
    assert client.get(f"{API}/sessions/{session_id}").status_code == 404


# --------------------------------------------------------------- streaming
def test_stream_events(client, pdf_bytes):
    upload(client, pdf_bytes)
    response = client.post(f"{API}/chat/stream", json={"message": "refund rules?"})
    assert response.status_code == 200
    events = parse_events(response.text)
    names = [name for name, _ in events]
    assert names[0] == "session" and names[-1] == "done"
    assert "tool" in names and "sources" in names and "token" in names
    session_id = events[0][1]["session_id"]
    assert len(client.get(f"{API}/sessions/{session_id}/messages").json()) == 2


# -------------------------------------------------------------------- auth
def test_api_key_required(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret")
    assert client.get(f"{API}/sessions").status_code == 401
    assert client.get(f"{API}/sessions", headers={"X-API-Key": "secret"}).status_code == 200
    assert client.get("/health").status_code == 200
