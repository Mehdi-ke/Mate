import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for
import anthropic

from extensions import db, doc_collection
from models import Document
from tools.document_processing import (
    RELEVANCE_THRESHOLD,
    extract_pages,
    chunk_pages,
    rerank_chunks,
)

bp = Blueprint(
    "doc_qa",
    __name__,
    template_folder="templates",
    url_prefix="/tools/doc-qa",
)

client = anthropic.Anthropic()

UPLOAD_FOLDER = "instance/uploads"


@bp.route("/")
def index():
    documents = Document.query.filter_by(conversation_id=None).order_by(Document.uploaded_at.desc()).all()
    return render_template("doc_qa/index.html", documents=documents)


@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf_file")
    if not file or file.filename == "":
        return redirect(url_for("doc_qa.index"))

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    doc_id = str(uuid.uuid4())
    pages = extract_pages(save_path)
    chunks, metadatas = chunk_pages(pages, doc_id, file.filename)

    if not chunks:
        documents = Document.query.filter_by(conversation_id=None).order_by(Document.uploaded_at.desc()).all()
        return render_template(
            "doc_qa/index.html",
            documents=documents,
            ask_error="Couldn't extract any text from that PDF — it may be a scan or image-only.",
        )

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    doc_collection.add(documents=chunks, ids=ids, metadatas=metadatas)

    new_doc = Document(doc_id=doc_id, filename=file.filename)
    db.session.add(new_doc)
    db.session.commit()

    return redirect(url_for("doc_qa.index"))


@bp.route("/ask", methods=["POST"])
def ask():
    doc_id = request.form["doc_id"]
    question = request.form["question"]

    document = Document.query.filter_by(doc_id=doc_id).first()
    documents_list = Document.query.filter_by(conversation_id=None).order_by(Document.uploaded_at.desc()).all()

    if not document:
        return render_template(
            "doc_qa/index.html",
            documents=documents_list,
            ask_error="Document not found.",
        )

    results = doc_collection.query(
        query_texts=[question],
        n_results=10,
        where={"doc_id": doc_id},
        include=["documents", "distances", "metadatas"],
    )

    chunks = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not chunks or not distances:
        return render_template(
            "doc_qa/index.html",
            documents=documents_list,
            ask_error="No content found for this document.",
        )

    # Re-rank: filter by threshold, diversify across pages
    filtered_chunks, filtered_metas = rerank_chunks(
        chunks, distances, metadatas,
        max_per_page=3,
        max_total=6,
        threshold=RELEVANCE_THRESHOLD,
    )

    if not filtered_chunks:
        return render_template(
            "doc_qa/index.html",
            documents=documents_list,
            asked_document=document,
            question=question,
            answer="No relevant passages found in this document for that question. "
                   "Try rephrasing or asking about a different topic.",
        )

    # Build context with source labels for citations
    labelled = []
    for chunk, meta in zip(filtered_chunks, filtered_metas):
        page = meta.get("page", "?")
        labelled.append(f"[Page {page}]\n{chunk}")
    context = "\n\n---\n\n".join(labelled)

    prompt = f"""Answer the question using ONLY the excerpts below. If the
excerpts don't contain the answer, say so - do not use outside knowledge.

When you state something drawn from an excerpt, cite it inline in the form
(Page X). Where the excerpts don't fully cover the question, say so explicitly.

Excerpts:
{context}

Question: {question}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = message.content[0].text

    # Build source list for the UI
    sources = []
    seen_pages = set()
    for meta in filtered_metas:
        page = meta.get("page")
        if page and page not in seen_pages:
            sources.append({"page": page, "filename": meta.get("filename", "")})
            seen_pages.add(page)

    return render_template(
        "doc_qa/index.html",
        documents=documents_list,
        asked_document=document,
        question=question,
        answer=answer,
        sources=sorted(sources, key=lambda s: s["page"]),
    )
