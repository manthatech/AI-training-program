"""
vector_store.py - Stores text as vectors in ChromaDB so we can search by MEANING.

How a vector search works:
  1. When we save a piece of text, we also save its vector (from ai_models.embed).
  2. When we search, we turn the question into a vector too.
  3. ChromaDB returns the saved texts whose vectors are closest to the question's vector.

We keep two separate "collections" (think: two tables):
  "documents"           - chunks of the uploaded PDFs           (used by documents.py)
  "conversation_memory" - old chat turns and saved facts        (used by memory.py)
"""
import os

import chromadb

from app import ai_models, config

collections = {}   # filled in by connect(): {"documents": ..., "conversation_memory": ...}


def connect():
    """Open (or create) the ChromaDB database on disk. Called once at startup."""
    client = chromadb.PersistentClient(path=os.path.join(config.DATA_DIR, "chroma"))
    for name in ["documents", "conversation_memory"]:
        # "cosine" = compare vectors by the angle between them (the usual choice for text)
        collections[name] = client.get_or_create_collection(
            name, configuration={"hnsw": {"space": "cosine"}})


def add(collection_name, ids, texts, metadatas):
    """Save texts. `ids` must be unique; `metadatas` are extra labels we can filter on later."""
    collection = collections[collection_name]
    batch_size = 200   # embed and save in small batches so big PDFs don't use too much memory
    for start in range(0, len(texts), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
            embeddings=ai_models.embed(texts[start:end]),
        )


def search(collection_name, query, how_many, where=None):
    """Find the texts most similar to `query`.

    `where` is an optional filter, e.g. {"session_id": "abc"} -> only that session's texts.
    Returns a list of dicts: {"text": ..., "metadata": {...}, "score": 0.0 to 1.0}
    """
    collection = collections[collection_name]
    total = collection.count()
    if how_many <= 0 or total == 0:
        return []

    result = collection.query(
        query_embeddings=ai_models.embed([query]),
        n_results=min(how_many, total),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # ChromaDB returns one list per query. We sent one query, so we take item [0].
    texts = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    hits = []
    for i in range(len(texts)):
        hits.append({
            "text": texts[i],
            "metadata": metadatas[i],
            "score": round(1 - distances[i], 4),   # distance 0 = identical, so score 1 = identical
        })
    return hits


def delete(collection_name, where):
    """Delete every text that matches the filter, e.g. {"doc_id": "a1b2c3"}."""
    collections[collection_name].delete(where=where)


def count(collection_name):
    return collections[collection_name].count()
