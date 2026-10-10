"""
Test setup. We replace the real AI models with FAKE ones, so the tests:
  - need no API key and no internet
  - give the same answer every time
"""
import hashlib
import io
import uuid

import numpy as np
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

from app import ai_models, config
from app.main import app


class FakeChatModel(BaseChatModel):
    """Pretends to be an LLM. It calls tools when it sees certain words."""
    tool_names: list[str] = []

    @property
    def _llm_type(self):
        return "fake"

    def bind_tools(self, tools, **kwargs):
        return FakeChatModel(tool_names=[t["name"] for t in tools])

    def with_structured_output(self, schema, **kwargs):
        def extract(prompt):
            return schema(name="Asha") if "Asha" in str(prompt) else schema()
        return RunnableLambda(extract)

    def _tool_call(self, name, args):
        return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": uuid.uuid4().hex}])

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last = messages[-1]
        text = str(last.content)
        if isinstance(last, ToolMessage):
            reply = AIMessage(content=f"Answer based on tool result: {text[:80]}")
        elif self.tool_names and isinstance(last, HumanMessage) and "refund" in text.lower():
            reply = self._tool_call("search_documents", {"query": "refund policy"})
        elif self.tool_names and isinstance(last, HumanMessage) and "calculate" in text.lower():
            reply = self._tool_call("calculator", {"expression": "2 + 3 * 4"})
        elif self.tool_names and isinstance(last, HumanMessage) and "remember" in text.lower():
            reply = self._tool_call("save_memory", {"fact": text})
        elif "Progressively summarize" in text:
            reply = AIMessage(content="SUMMARY: the user chatted about several things.")
        else:
            reply = AIMessage(content=f"Echo: {text}")
        return ChatResult(generations=[ChatGeneration(message=reply)])


class FakeEmbedder:
    """Turns text into a random-looking (but always the same) vector."""
    def encode(self, texts, normalize_embeddings=True):
        vectors = []
        for text in texts:
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
            vector = np.random.default_rng(seed).normal(size=64)
            vectors.append(vector / np.linalg.norm(vector))
        return np.array(vectors)


def make_pdf(pages):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    for page in pages:
        y = 800
        for line in page.split("\n"):
            pdf.drawString(50, y, line)
            y -= 16
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a fresh, empty data folder and small settings for every test.
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "MEMORY_WINDOW_TURNS", 2)
    monkeypatch.setattr(config, "MEMORY_RECALL_K", 2)
    monkeypatch.setattr(config, "CHUNK_SIZE", 300)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 50)
    monkeypatch.setattr(config, "API_KEY", None)
    # Fake models instead of real ones.
    monkeypatch.setattr(ai_models, "llm", FakeChatModel())
    monkeypatch.setattr(ai_models, "embedder", FakeEmbedder())
    monkeypatch.setattr(ai_models, "reranker", None)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def pdf_bytes():
    return make_pdf([
        "Refund policy\nRefunds are issued within 14 days of purchase.\nItems must be unused.",
        "Shipping\nOrders ship within 2 business days.\nTracking is emailed to you.",
    ])
