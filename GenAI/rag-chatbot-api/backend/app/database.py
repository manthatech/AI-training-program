"""
database.py - Saves sessions, chat messages and the list of uploaded documents in SQLite.

SQLite is a small database stored in a single file (data/app.db). Python has it built in.

We have three tables:
  sessions   - one row per conversation (its title, turn number, summary and user profile)
  messages   - every message ever sent, with the turn number it belongs to
  documents  - one row per uploaded PDF

Every function here opens the database, runs one SQL command, and closes it again.
That is a little slower than keeping it open, but it is simple and safe.
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from app import config


def db_path():
    return os.path.join(config.DATA_DIR, "app.db")


def now():
    """The current time as text, e.g. '2026-10-02T13:30:00+00:00'."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_sql(sql, params=()):
    """Run one SQL command and return the result rows as a list of dictionaries."""
    connection = sqlite3.connect(db_path())
    connection.row_factory = sqlite3.Row   # lets us turn each row into a dict
    rows = connection.execute(sql, params).fetchall()
    connection.commit()
    connection.close()
    return [dict(row) for row in rows]


def create_tables():
    """Create the tables the first time the app runs (does nothing if they already exist)."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    run_sql("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            created_at  TEXT,
            updated_at  TEXT,
            turn        INTEGER,   -- how many question/answer turns so far
            summary     TEXT,      -- running summary of old turns (mid-term memory)
            profile     TEXT       -- facts about the user, stored as JSON text
        )""")
    run_sql("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            turn        INTEGER,
            role        TEXT,      -- 'user' or 'assistant'
            content     TEXT,
            sources     TEXT,      -- JSON list of citations
            tool_calls  TEXT,      -- JSON list of tools used
            created_at  TEXT
        )""")
    run_sql("""
        CREATE TABLE IF NOT EXISTS documents (
            id          TEXT PRIMARY KEY,
            filename    TEXT,
            pages       INTEGER,
            chunks      INTEGER,
            created_at  TEXT
        )""")


# ======================================================================= sessions

def create_session(title=None):
    """Create a new, empty conversation and return its id."""
    session_id = uuid.uuid4().hex   # a random unique id like '3f2a9c...'
    run_sql("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, title, now(), now(), 0, "", "{}"))
    return session_id


def get_session(session_id):
    """Return the session as a dict, or None if it doesn't exist."""
    rows = run_sql("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if not rows:
        return None
    session = rows[0]
    session["profile"] = json.loads(session["profile"])   # JSON text -> dict
    return session


def list_sessions(limit=50):
    """Newest sessions first, with how many messages each one has."""
    return run_sql("""
        SELECT id, title, created_at, updated_at,
               (SELECT COUNT(*) FROM messages WHERE session_id = sessions.id) AS message_count
        FROM sessions
        ORDER BY updated_at DESC
        LIMIT ?""", (limit,))


def update_session(session_id, turn=None, title=None, summary=None, profile=None):
    """Change one or more fields of a session. Fields left as None are not changed."""
    if turn is not None:
        run_sql("UPDATE sessions SET turn = ? WHERE id = ?", (turn, session_id))
    if title is not None:
        run_sql("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
    if summary is not None:
        run_sql("UPDATE sessions SET summary = ? WHERE id = ?", (summary, session_id))
    if profile is not None:
        run_sql("UPDATE sessions SET profile = ? WHERE id = ?", (json.dumps(profile), session_id))
    run_sql("UPDATE sessions SET updated_at = ? WHERE id = ?", (now(), session_id))


def delete_session(session_id):
    run_sql("DELETE FROM messages WHERE session_id = ?", (session_id,))
    run_sql("DELETE FROM sessions WHERE id = ?", (session_id,))


# ======================================================================= messages

def add_message(session_id, turn, role, content, sources=None, tool_calls=None):
    run_sql("""INSERT INTO messages (session_id, turn, role, content, sources, tool_calls, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, turn, role, content,
             json.dumps(sources or []), json.dumps(tool_calls or []), now()))


def get_messages(session_id, from_turn=1):
    """All messages of a session, oldest first, starting at turn `from_turn`."""
    rows = run_sql("SELECT * FROM messages WHERE session_id = ? AND turn >= ? ORDER BY id",
                   (session_id, from_turn))
    for row in rows:
        row["sources"] = json.loads(row["sources"])
        row["tool_calls"] = json.loads(row["tool_calls"])
    return rows


def get_turn_messages(session_id, turn):
    """Just the user + assistant messages of one turn."""
    return run_sql("SELECT role, content FROM messages WHERE session_id = ? AND turn = ? ORDER BY id",
                   (session_id, turn))


# ====================================================================== documents

def add_document(doc_id, filename, pages, chunks):
    created_at = now()
    run_sql("INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
            (doc_id, filename, pages, chunks, created_at))
    return {"id": doc_id, "filename": filename, "pages": pages,
            "chunks": chunks, "created_at": created_at}


def list_documents():
    return run_sql("SELECT * FROM documents ORDER BY created_at DESC")


def get_document(doc_id):
    rows = run_sql("SELECT * FROM documents WHERE id = ?", (doc_id,))
    if rows:
        return rows[0]
    return None


def delete_document(doc_id):
    run_sql("DELETE FROM documents WHERE id = ?", (doc_id,))
