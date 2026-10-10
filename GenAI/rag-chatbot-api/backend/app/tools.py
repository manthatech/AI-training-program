"""
tools.py - Tools the chatbot can use  (Week 11: tool calling, Week 12: RAG as a tool).

How tool calling works:
  1. We send the LLM a "menu" of tools: each tool's name, what it does, and its inputs.
     (TOOL_MENU below is exactly what the LLM sees.)
  2. The LLM can't run code. Instead it replies: "please call calculator with expression='2+2'".
  3. OUR code runs the tool (run_tool below) and sends the result back to the LLM.
  4. The LLM uses the result to write its answer (or asks for another tool).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from app import documents, memory


def describe_tool(name, description, input_name, input_description):
    """Build the description of a tool that takes one text input, in the format LLMs expect."""
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                input_name: {"type": "string", "description": input_description},
            },
            "required": [input_name],
        },
    }


# The menu of tools we show to the LLM.
TOOL_MENU = [
    describe_tool(
        "search_documents",
        "Search the uploaded PDF knowledge base and return the most relevant passages "
        "with citation labels like [file.pdf p.3].",
        "query", "A specific, standalone search query",
    ),
    describe_tool(
        "save_memory",
        "Save a durable fact about the user or their goals for later in this conversation.",
        "fact", 'The fact to remember, e.g. "User is preparing for NLP interviews in March"',
    ),
    describe_tool(
        "calculator",
        "Evaluate an arithmetic expression. Supports + - * / % and brackets.",
        "expression", 'The expression, e.g. "23 * (4 + 5)"',
    ),
    describe_tool(
        "get_current_time",
        "Get the current date and time in a timezone.",
        "timezone", 'An IANA timezone such as "UTC", "Asia/Kolkata" or "Europe/London"',
    ),
]


# ===================================================================== the tools

def calculator(expression):
    # eval() runs Python code, which is dangerous with text from outside.
    # So we first check that the text only contains numbers and maths symbols.
    allowed = "0123456789+-*/%(). "
    for character in expression:
        if character not in allowed:
            raise ValueError(f"Character '{character}' is not allowed")
    if "**" in expression:
        raise ValueError("Powers (**) are not supported")   # 9**9**9 would freeze the server
    if len(expression) > 200:
        raise ValueError("Expression too long")

    result = eval(expression, {"__builtins__": {}})   # no built-in functions available
    return str(result)


def get_current_time(timezone):
    now = datetime.now(ZoneInfo(timezone))
    return now.strftime("%A %Y-%m-%d %H:%M:%S %Z")


def run_tool(name, args, session_id, sources):
    """Run the tool the LLM asked for and return its result as text.

    `sources` is a list we add document citations to, so we can show them to the user.
    """
    if name == "search_documents":
        results = documents.search(args["query"])
        if not results:
            return "No relevant passages found in the knowledge base."
        for result in results:
            if result not in sources:
                sources.append(result)
        return documents.format_for_llm(results)

    if name == "save_memory":
        memory.save_fact(session_id, args["fact"])
        return "Saved."

    if name == "calculator":
        return calculator(args["expression"])

    if name == "get_current_time":
        return get_current_time(args.get("timezone", "UTC"))

    raise ValueError(f"Unknown tool '{name}'")
