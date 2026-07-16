import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import anthropic

from extensions import db, doc_collection
from models import Document

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
    documents = Document.query.order_by(Document.uploaded_at.desc()).all()
    return render_template("doc_qa/index.html", documents=documents)


@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf_file")
    if not file or file.filename == "":
        return redirect(url_for("doc_qa.index"))

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    reader = PdfReader(save_path)
    full_text = "\n".join(page.extract_text() for page in reader.pages)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_text(full_text)

    doc_id = str(uuid.uuid4())
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id} for _ in chunks]
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
    documents_list = Document.query.order_by(Document.uploaded_at.desc()).all()

    if not document:
        return render_template("doc_qa/index.html", documents=documents_list,
                                ask_error="Document not found.")

    results = doc_collection.query(
        query_texts=[question],
        n_results=3,
        where={"doc_id": doc_id},
    )
    retrieved_chunks = results["documents"][0]

    if not retrieved_chunks:
        return render_template("doc_qa/index.html", documents=documents_list,
                                ask_error="No content found for this document.")

    context = "\n\n---\n\n".join(retrieved_chunks)
    prompt = f"""Answer the question using ONLY the excerpts below. If the
excerpts don't contain the answer, say so - do not use outside knowledge.

Excerpts:
{context}

Question: {question}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = message.content[0].text

    return render_template("doc_qa/index.html", documents=documents_list,
                            asked_document=document, question=question,
                            answer=answer, retrieved_chunks=retrieved_chunks)