"""
memory.py - How the chatbot remembers things  (Week 11).

An LLM forgets everything between calls, so on every turn WE must send it what it
should remember. We use four kinds of memory:

  1. SHORT-TERM  - the last few turns, word for word           (from the messages table)
  2. MID-TERM    - a short summary of the turns before that     (sessions.summary)
  3. LONG-TERM   - every turn saved in ChromaDB; we "recall"    (vector_store)
                   the old turns that are similar to the new question,
                   plus any facts the bot chose to save with the save_memory tool
  4. PROFILE     - structured facts about the user              (sessions.profile)
                   (name, job, goals...) pulled out by the LLM

A "turn" = one user message + one assistant reply.
"""
import json
import uuid
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from app import ai_models, config, database, vector_store
from app.prompts import (PROFILE_PROMPT, PROFILE_SECTION, RECALL_SECTION, SUMMARY_PROMPT,
                         SUMMARY_SECTION)


# ============================================================ 1. short-term memory

def recent_messages(session_id, last_turn):
    """The last MEMORY_WINDOW_TURNS turns, as LangChain message objects.

    `last_turn` is the number of the last finished turn. Example with a window of 6:
    if last_turn is 10, we return turns 5, 6, 7, 8, 9 and 10.
    """
    first_turn = last_turn - config.MEMORY_WINDOW_TURNS + 1
    messages = []
    for row in database.get_messages(session_id, from_turn=first_turn):
        if row["role"] == "user":
            messages.append(HumanMessage(row["content"]))
        else:
            messages.append(AIMessage(row["content"]))
    return messages


# ============================================================== 2. mid-term memory

def update_summary(session_id):
    """When a turn falls out of the short-term window, fold it into the summary."""
    session = database.get_session(session_id)
    if session is None:
        return

    # Example with a window of 6: after turn 10, turns 5-10 are still "recent",
    # so turn 4 has just dropped out and needs to go into the summary.
    old_turn = session["turn"] - config.MEMORY_WINDOW_TURNS
    if old_turn < 1:
        return   # nothing has dropped out of the window yet

    lines = []
    for row in database.get_turn_messages(session_id, old_turn):
        speaker = "User" if row["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {row['content']}")
    new_lines = "\n".join(lines)

    prompt = SUMMARY_PROMPT.format(summary=session["summary"] or "(none)", new_lines=new_lines)
    try:
        reply = ai_models.llm.invoke(prompt)
        new_summary = ai_models.get_text(reply).strip()
    except Exception as error:
        # If the LLM fails, just add the raw lines so we don't lose them.
        print("Summary failed:", error)
        new_summary = (session["summary"] + "\n" + new_lines).strip()

    database.update_session(session_id, summary=new_summary)


# ============================================================= 3. long-term memory

def save_turn(session_id, turn, user_message, reply):
    """Save a whole turn in the vector store so it can be recalled much later."""
    vector_store.add(
        "conversation_memory",
        ids=[f"{session_id}:turn:{turn}"],
        texts=[f"User: {user_message}\nAssistant: {reply}"],
        metadatas=[{"session_id": session_id, "turn": turn}],
    )


def save_fact(session_id, fact):
    """Used by the save_memory tool. Facts get turn = -1 so they can always be recalled."""
    vector_store.add(
        "conversation_memory",
        ids=[f"{session_id}:fact:{uuid.uuid4().hex}"],
        texts=[f"Saved fact: {fact}"],
        metadatas=[{"session_id": session_id, "turn": -1}],
    )


def recall(session_id, query, last_turn):
    """Find old turns (and saved facts) from this session that relate to `query`.

    We skip turns that are still in the short-term window - the LLM already sees those.
    """
    first_recent_turn = last_turn - config.MEMORY_WINDOW_TURNS + 1
    where = {"$and": [{"session_id": session_id},
                      {"turn": {"$lt": first_recent_turn}}]}   # $lt means "less than"
    hits = vector_store.search("conversation_memory", query, config.MEMORY_RECALL_K, where)
    return [hit["text"] for hit in hits]


def forget_session(session_id):
    vector_store.delete("conversation_memory", where={"session_id": session_id})


# ================================================================== 4. user profile

class UserProfile(BaseModel):
    """The shape of the facts we want the LLM to pull out of a message.

    Because this is a Pydantic model, the LLM is forced to answer in exactly this
    format ("structured output"). The descriptions tell the LLM what each field means.
    """
    name: Optional[str] = Field(None, description="The user's name, if they stated it")
    location: Optional[str] = Field(None, description="Where the user lives or works")
    occupation: Optional[str] = Field(None, description="The user's job or role")
    interests: list[str] = Field(default_factory=list, description="Hobbies, topics or technologies they like")
    goals: list[str] = Field(default_factory=list, description="What the user is trying to achieve")
    preferences: list[str] = Field(default_factory=list, description="How they like answers (length, tone, language...)")


def update_profile(session_id, user_message):
    """Ask the LLM for any new facts in the message and add them to the saved profile."""
    if not config.EXTRACT_PROFILE:
        return
    session = database.get_session(session_id)
    if session is None:
        return

    try:
        extractor = ai_models.llm.with_structured_output(UserProfile)
        new_facts = extractor.invoke(PROFILE_PROMPT.format(message=user_message))
    except Exception as error:
        # Small/local models sometimes fail at this. That's fine - just skip it.
        print("Profile extraction failed:", error)
        return

    profile = session["profile"]   # a plain dict, e.g. {"name": "Asha", "goals": ["..."]}

    # Single values: replace the old value if a new one was found.
    for field in ["name", "location", "occupation"]:
        value = getattr(new_facts, field)
        if value:
            profile[field] = value

    # Lists: add new items we don't have yet.
    for field in ["interests", "goals", "preferences"]:
        items = profile.get(field, [])
        for item in getattr(new_facts, field):
            if item and item not in items:
                items.append(item)
        if items:
            profile[field] = items

    database.update_session(session_id, profile=profile)


# ======================================================= putting the memory together

def memory_for_prompt(session, query):
    """Build the memory sections that get added to the system prompt."""
    sections = []

    if session["profile"]:
        profile_text = json.dumps(session["profile"], indent=1)
        sections.append(PROFILE_SECTION.format(profile=profile_text))

    if session["summary"]:
        sections.append(SUMMARY_SECTION.format(summary=session["summary"]))

    recalled = recall(session["id"], query, session["turn"])
    if recalled:
        sections.append(RECALL_SECTION.format(recalled="\n---\n".join(recalled)))

    return sections
