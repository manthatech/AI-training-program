"""
chat.py - What happens when the user sends a message.

    1. start_turn()  - build the list of messages for the LLM:
                         system prompt (rules + document list + memories)
                         + the last few turns
                         + the new user message
    2. the tool loop - ask the LLM. If it wants tools, run them and ask again.
                       Repeat until it gives a normal answer.
    3. finish_turn() - save the question and answer (database + long-term memory).
    4. after_turn()  - slower memory updates (summary, user profile). These run
                       AFTER the user already has their answer.

There are two versions of step 2:
    chat()        - returns the whole answer at once
    chat_stream() - sends the answer word by word, as it is being written
"""
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app import ai_models, config, database, documents, memory
from app.prompts import SYSTEM_PROMPT
from app.tools import TOOL_MENU, run_tool

TOO_MANY_TOOLS = "Sorry, I couldn't finish that within the tool-call limit."


# ================================================================ step 1: start

def build_system_prompt(session, user_message):
    docs = documents_list_text()
    prompt = SYSTEM_PROMPT.format(app_name=config.APP_NAME, knowledge_base=docs)
    memory_sections = memory.memory_for_prompt(session, user_message)
    return "\n\n".join([prompt] + memory_sections)


def documents_list_text():
    """Tell the LLM which documents exist, so it knows when searching is worth it."""
    docs = database.list_documents()
    if not docs:
        return "Empty — no documents uploaded yet. Don't call search_documents."
    names = [doc["filename"] for doc in docs[:20]]
    return f"{len(docs)} document(s): " + ", ".join(names)


def start_turn(session_id, user_message):
    """Return the list of messages to send to the LLM."""
    session = database.get_session(session_id)
    messages = [SystemMessage(build_system_prompt(session, user_message))]
    messages += memory.recent_messages(session_id, session["turn"])
    messages.append(HumanMessage(user_message))
    return messages


# ============================================================ step 2: tool loop

def handle_tool_calls(ai_message, messages, session_id, sources, tools_used):
    """Run every tool the LLM asked for and add each result to `messages`."""
    for tool_call in ai_message.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        print(f"Calling Tool {name} --- {args}")
        try:
            result = run_tool(name, args, session_id, sources)
            print(f"Tool Result = {result}")
            ok = True
        except Exception as error:
            # Don't crash - tell the LLM what went wrong so it can try something else.
            result = f"ERROR: {error}"
            ok = False

        print(f"Tool {name}({args}) ok={ok}")
        tools_used.append({"name": name, "args": args, "ok": ok})
        # The tool_call_id tells the LLM which of its requests this result answers.
        messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))


def chat(session_id, user_message):
    """Answer a message. Returns a dict with the reply, the sources and the tools used."""
    messages = start_turn(session_id, user_message)
    llm = ai_models.llm.bind_tools(TOOL_MENU)   # give the LLM our tool menu
    sources = []
    tools_used = []
    reply = TOO_MANY_TOOLS

    for round_number in range(config.MAX_TOOL_ROUNDS):
        ai_message = llm.invoke(messages)
        print(f"AI Message = {ai_message}")
        messages.append(ai_message)

        if not ai_message.tool_calls:          # no tools wanted -> this is the final answer
            reply = ai_models.get_text(ai_message)
            break

        handle_tool_calls(ai_message, messages, session_id, sources, tools_used)

    turn = finish_turn(session_id, user_message, reply, sources, tools_used)
    return {"session_id": session_id, "turn": turn, "reply": reply,
            "sources": sources, "tool_calls": tools_used}


def chat_stream(session_id, user_message):
    """Same as chat(), but YIELDS small events as they happen:

        {"event": "token",   "data": "Hel"}             a bit of the answer text
        {"event": "tool",    "data": {"name": ...}}     the LLM is using a tool
        {"event": "sources", "data": [...]}             citations
        {"event": "done",    "data": {...}}             finished
        {"event": "error",   "data": {"detail": ...}}   something went wrong
    """
    messages = start_turn(session_id, user_message)
    llm = ai_models.llm.bind_tools(TOOL_MENU)
    sources = []
    tools_used = []
    reply = TOO_MANY_TOOLS

    try:
        for round_number in range(config.MAX_TOOL_ROUNDS):
            # llm.stream() gives the answer in small pieces ("chunks").
            # Adding chunks together (+) rebuilds the full message, including any tool calls.
            full_message = None
            text = ""
            for chunk in llm.stream(messages):
                if full_message is None:
                    full_message = chunk
                else:
                    full_message = full_message + chunk
                piece = ai_models.get_text(chunk)
                if piece:
                    text += piece
                    yield {"event": "token", "data": piece}

            messages.append(full_message)

            if not full_message.tool_calls:
                reply = text
                break

            for tool_call in full_message.tool_calls:
                yield {"event": "tool", "data": {"name": tool_call["name"], "args": tool_call["args"]}}
            handle_tool_calls(full_message, messages, session_id, sources, tools_used)

        if reply == TOO_MANY_TOOLS:   # the loop ran out of rounds
            yield {"event": "token", "data": reply}

    except Exception as error:
        yield {"event": "error", "data": {"detail": f"LLM error: {error}"}}
        return

    turn = finish_turn(session_id, user_message, reply, sources, tools_used)
    if sources:
        yield {"event": "sources", "data": sources}
    yield {"event": "done", "data": {"session_id": session_id, "turn": turn, "tool_calls": tools_used}}

    after_turn(session_id, user_message)


# ========================================================= steps 3 & 4: save

def finish_turn(session_id, user_message, reply, sources, tools_used):
    """Save the turn. Returns the new turn number."""
    session = database.get_session(session_id)
    turn = session["turn"] + 1

    database.add_message(session_id, turn, "user", user_message)
    database.add_message(session_id, turn, "assistant", reply, sources, tools_used)
    memory.save_turn(session_id, turn, user_message, reply)

    # Use the first message as the session's title.
    title = None
    if not session["title"]:
        title = user_message[:60]
    database.update_session(session_id, turn=turn, title=title)
    return turn


def after_turn(session_id, user_message):
    """Slower memory updates (each one is an extra LLM call)."""
    try:
        memory.update_summary(session_id)
        memory.update_profile(session_id, user_message)
    except Exception as error:
        print("Memory update failed:", error)
