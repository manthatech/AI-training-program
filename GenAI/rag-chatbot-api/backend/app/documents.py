"""
documents.py - RAG (Retrieval-Augmented Generation) over PDF files  (Week 12).

Two jobs:

  1. INDEXING a PDF   (when a user uploads one)
        read PDF  ->  split each page into chunks  ->  embed + save chunks in ChromaDB

  2. SEARCHING        (when the chatbot calls the search_documents tool)
        vector search for ~20 candidates  ->  rerank them  ->  keep the best 4
"""
import io
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app import ai_models, config, database, vector_store


# ===================================================================== 1. indexing

def add_pdf(pdf_bytes, filename):
    """Read a PDF, split it into chunks and save them. Returns info about the document.

    Raises ValueError if the PDF can't be read or has no text in it.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as error:
        raise ValueError(f"Could not read PDF: {error}")

    # The splitter cuts text into pieces of about CHUNK_SIZE characters. It prefers to
    # cut at paragraph breaks, then line breaks, then sentences, then spaces.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    doc_id = uuid.uuid4().hex[:12]   # a short random id for this document
    ids = []
    texts = []
    metadatas = []

    page_number = 0
    for page in reader.pages:
        page_number += 1
        page_text = (page.extract_text() or "").strip()
        print(f"Page Number {page_number} Page Text = {page_text}")
        if page_text == "":
            continue   # skip empty pages (e.g. pictures only)

        chunks = splitter.split_text(page_text)
        for chunk_number, chunk in enumerate(chunks):
            print('=====')
            print(f"Chunk = {chunk_number},{chunk}")
            print('=====')
            ids.append(f"{doc_id}:{page_number}:{chunk_number}")
            texts.append(chunk)
            # We remember where each chunk came from, so we can cite it later.
            metadatas.append({"doc_id": doc_id, "filename": filename, "page": page_number})
        print('=============================================')

    if not texts:
        raise ValueError("No text found in this PDF. Scanned PDFs need OCR before upload.")

    vector_store.add("documents", ids, texts, metadatas)
    print(f"Doc ID = {doc_id}")
    print(f"Indexed {filename}: {len(reader.pages)} pages, {len(texts)} chunks")
    return database.add_document(doc_id, filename, len(reader.pages), len(texts))


def delete_pdf(doc_id):
    """Remove a document and all its chunks. Returns False if it didn't exist."""
    if database.get_document(doc_id) is None:
        return False
    vector_store.delete("documents", where={"doc_id": doc_id})
    database.delete_document(doc_id)
    return True


# ==================================================================== 2. searching

def search(query, top_k=None, doc_id=None):
    """Find the chunks that best answer `query`.

    Step 1 (fast, rough):   vector search returns many candidates.
    Step 2 (slow, precise): the reranker reads each (question, chunk) pair and scores it.
    Returns a list of "source" dicts (see make_source below), best first.
    """
    if top_k is None:
        top_k = config.SEARCH_TOP_K

    # Only search inside one document if doc_id was given.
    where = None
    if doc_id:
        where = {"doc_id": doc_id}

    # Without a reranker there's no point fetching extra candidates.
    how_many = config.SEARCH_CANDIDATES if ai_models.reranker else top_k
    hits = vector_store.search("documents", query, how_many, where)

    if ai_models.reranker and hits:
        pairs = [(query, hit["text"]) for hit in hits]
        scores = ai_models.reranker.predict(pairs)
        for hit, score in zip(hits, scores):
            hit["rerank_score"] = round(float(score), 4)
        hits.sort(key=lambda hit: hit["rerank_score"], reverse=True)   # best first

    return [make_source(hit) for hit in hits[:top_k]]


def make_source(hit):
    """Turn a search hit into the citation info we send back to the user."""
    return {
        "doc_id": hit["metadata"]["doc_id"],
        "filename": hit["metadata"]["filename"],
        "page": hit["metadata"]["page"],
        "score": hit["score"],
        "rerank_score": hit.get("rerank_score"),
        "text": hit["text"],
        "snippet": hit["text"][:300],
    }


def format_for_llm(sources):
    """Turn search results into text for the LLM, with a citation label above each passage:

        [handbook.pdf p.4]
        Refunds are issued within 14 days...
    """
    passages = []
    for source in sources:
        passages.append(f"[{source['filename']} p.{source['page']}]\n{source['text']}")
    return "\n\n".join(passages)
