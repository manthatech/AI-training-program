"""
ai_models.py - Loads the three AI models the app uses.

  1. llm       - the chat model that writes answers (OpenAI, Anthropic, Groq, Ollama...)
  2. embedder  - turns text into a list of numbers (a "vector") so we can compare meaning
  3. reranker  - scores how well a passage answers a question (optional, improves search)

The models are loaded once, when the server starts (see load_models() in main.py).
Until then the variables below are None.
"""
from langchain.chat_models import init_chat_model

from app import config

llm = None
embedder = None
reranker = None


def load_models():
    """Load all models. Called once when the server starts."""
    global llm, embedder, reranker

    print(f"Loading LLM {config.LLM_PROVIDER}:{config.LLM_MODEL}")
    llm = init_chat_model(config.LLM_MODEL,
                          model_provider=config.LLM_PROVIDER,
                          temperature=config.LLM_TEMPERATURE)

    # We import sentence_transformers here (not at the top) because it is a big,
    # slow import. This way the tests, which use fake models, never need it.
    from sentence_transformers import CrossEncoder, SentenceTransformer

    print(f"Loading embedding model {config.EMBEDDING_MODEL}")
    embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    copy_weights_to_ram(embedder)

    if config.RERANK_ENABLED:
        print(f"Loading reranker {config.RERANK_MODEL}")
        reranker = CrossEncoder(config.RERANK_MODEL)
        copy_weights_to_ram(reranker)


def copy_weights_to_ram(model):
    """Give every weight its own freshly allocated memory.

    transformers memory-maps the weight file, so some weights can start at a
    misaligned address. On macOS 12 the math library then returns NaN scores
    (or crashes with "Bus error"). A copy is always properly aligned.
    """
    for param in model.parameters():
        param.data = param.data.clone()


def embed(texts):
    """Turn a list of texts into a list of vectors (one list of numbers per text)."""
    vectors = embedder.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def get_text(message):
    """Return the plain text of an LLM reply.

    Most models return a string, but some (e.g. Anthropic) return a list of
    "blocks" like [{"type": "text", "text": "Hello"}]. This handles both.
    """
    if isinstance(message.content, str):
        return message.content

    text = ""
    for block in message.content:
        if isinstance(block, dict) and block.get("type") == "text":
            text += block.get("text", "")
    return text
