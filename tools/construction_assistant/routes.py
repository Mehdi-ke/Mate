import os
import uuid
from flask import Blueprint, render_template, request, session, redirect, url_for
import anthropic
import markdown

from extensions import db, doc_collection
from models import Conversation, Message, Document
from tools.document_processing import (
    RELEVANCE_THRESHOLD,
    extract_pages,
    chunk_pages,
    rerank_chunks,
)

bp = Blueprint(
    "construction_assistant",
    __name__,
    template_folder="templates",
    url_prefix="/tools/construction-assistant",
)

client = anthropic.Anthropic()

WARNING_AT = 7
SUMMARY_AT = 9
MAX_DOCUMENTS = 10
UPLOAD_FOLDER = "instance/uploads"


@bp.app_context_processor
def inject_max_documents():
    return {"max_documents": MAX_DOCUMENTS}


BASE_SYSTEM_PROMPT = "You are a construction technology advisor specialising in the UK construction industry. Provide clear, practical, and accurate guidance on construction technology, digital workflows, BIM, UK contract forms, CDM Regulations, site management, project delivery, and industry best practices. Tailor responses to UK standards and terminology, explain technical concepts in a concise and professional manner, highlight compliance or safety considerations where relevant, and acknowledge uncertainty rather than making unsupported assumptions. Match the length of your response to the depth of the question — be brief for simple questions and thorough for complex ones, but never pad."

WARNING_SUFFIX = " IMPORTANT: This is the fourth of five exchanges in this conversation. After answering the user's question normally, end your reply with a brief, friendly note (one short sentence) that you're approaching a good moment to start a fresh chat soon."

SUMMARY_SUFFIX = " IMPORTANT: This is the final exchange in this conversation. Instead of answering normally, produce a concise summary of the entire conversation as 3-5 bullet points capturing the key questions asked and the key guidance given. Format it so the user can paste it into a new chat as context. Start with a brief sentence explaining this is a wrap-up summary, then the bullets."

# Appended ONLY when relevant document evidence was found (the RAG path).
RAG_SUFFIX = """

The user has uploaded documents to this conversation, and the excerpts below were retrieved as relevant to their latest question. Each excerpt is prefixed with its source document and page number.

Base your answer primarily on these excerpts. When you state something drawn from an excerpt, cite it inline in the form (Source: filename, page X) using the exact filename and page shown. Where the excerpts don't fully cover the question, you may supplement with general knowledge — but make clear which parts come from the documents and which are general knowledge, and don't attach a citation to general knowledge.

Relevant excerpts:
{context}"""


def get_or_create_conversation():
    conv_id = session.get("conversation_id")
    if conv_id:
        conv = Conversation.query.get(conv_id)
        if conv:
            return conv
    conv = Conversation()
    db.session.add(conv)
    db.session.commit()
    session["conversation_id"] = conv.id
    return conv


def render_history(messages):
    rendered = []
    for msg in messages:
        if msg.role == "assistant":
            rendered.append({"role": "assistant", "content": markdown.markdown(msg.content)})
        else:
            rendered.append({"role": "user", "content": msg.content})
    return rendered


def get_documents_for(conv):
    if not conv:
        return []
    return Document.query.filter_by(conversation_id=conv.id).order_by(Document.uploaded_at).all()


@bp.route("/")
def home():
    carry = session.pop("carry_context", None)

    conv_id = session.get("conversation_id")
    if conv_id:
        conv = Conversation.query.get(conv_id)
        if conv and conv.summary is None:
            return render_template(
                "construction_assistant/index.html",
                history=render_history(conv.messages),
                locked=False,
                prefill=None,
                documents=get_documents_for(conv),
            )

    session.pop("conversation_id", None)
    return render_template(
        "construction_assistant/index.html",
        history=[],
        locked=False,
        prefill=carry,
        documents=[],
    )


@bp.route("/new")
def new():
    session.pop("conversation_id", None)
    session.pop("carry_context", None)
    return redirect(url_for("construction_assistant.home"))


REWRITE_PROMPT = """Rewrite the user's latest question into a standalone search query.

Resolve any pronouns or references ("those", "it", "that clause") using the conversation history, so the query makes sense on its own without the history.

Rules:
- Output ONLY the rewritten query. No preamble, no quotes, no explanation.
- Keep it short — a search query, not a sentence.
- If the question is already standalone, return it essentially unchanged.

Conversation so far:
{history}

Latest question: {question}"""


def rewrite_query(conv, question):
    """Turn a follow-up question into a standalone search query.

    Falls back to the original question if there's no history to resolve
    against, or if the rewrite call fails for any reason.
    """
    previous = conv.messages[:-1]
    if not previous:
        return question

    recent = previous[-4:]
    history = "\n".join(f"{m.role}: {m.content[:500]}" for m in recent)

    try:
        reply = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": REWRITE_PROMPT.format(history=history, question=question),
            }],
        )
        rewritten = reply.content[0].text.strip()
        return rewritten if rewritten else question
    except Exception:
        return question


def retrieve_relevant_context(conv, question):
    """Decide how uploaded documents relate to this question.

    Returns one of:
      ("relevant", excerpt_text)  - relevant evidence found -> RAG path
      ("no_match", None)          - docs exist but none relevant -> notice
      ("no_docs", None)           - no documents uploaded at all -> silent
    """
    documents = get_documents_for(conv)
    if not documents:
        return ("no_docs", None)

    doc_ids = [d.doc_id for d in documents]
    results = doc_collection.query(
        query_texts=[question],
        n_results=10,
        where={"doc_id": {"$in": doc_ids}},
        include=["documents", "distances", "metadatas"],
    )

    chunks = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not chunks or not distances:
        return ("no_match", None)

    # Re-rank: filter by threshold, diversify across pages
    filtered_chunks, filtered_metas = rerank_chunks(
        chunks, distances, metadatas,
        max_per_page=3,
        max_total=6,
        threshold=RELEVANCE_THRESHOLD,
    )

    if not filtered_chunks:
        return ("no_match", None)

    labelled = []
    for chunk, meta in zip(filtered_chunks, filtered_metas):
        filename = meta.get("filename", "unknown document")
        page = meta.get("page", "?")
        labelled.append(f"[Source: {filename}, page {page}]\n{chunk}")

    return ("relevant", "\n\n---\n\n".join(labelled))


@bp.route("/upload-doc", methods=["POST"])
def upload_doc():
    conv = get_or_create_conversation()
    documents = get_documents_for(conv)

    upload_error = None
    file = request.files.get("doc_file")

    if len(documents) >= MAX_DOCUMENTS:
        upload_error = f"You've reached the {MAX_DOCUMENTS}-document limit for this conversation."
    elif not file or file.filename == "":
        upload_error = "Please choose a PDF to upload."
    elif not file.filename.lower().endswith(".pdf"):
        upload_error = "Only PDF files are supported right now."

    if upload_error:
        return render_template(
            "construction_assistant/index.html",
            history=render_history(conv.messages),
            locked=False,
            prefill=None,
            documents=documents,
            upload_error=upload_error,
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    doc_id = str(uuid.uuid4())
    pages = extract_pages(save_path)
    chunks, metadatas = chunk_pages(pages, doc_id, file.filename)

    if not chunks:
        return render_template(
            "construction_assistant/index.html",
            history=render_history(conv.messages),
            locked=False,
            prefill=None,
            documents=documents,
            upload_error="Couldn't extract any text from that PDF — it may be a scan or image-only.",
        )

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    doc_collection.add(documents=chunks, ids=ids, metadatas=metadatas)

    new_doc = Document(doc_id=doc_id, filename=file.filename, conversation_id=conv.id)
    db.session.add(new_doc)
    db.session.commit()

    return redirect(url_for("construction_assistant.home"))


@bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["user_message"]

    conv = get_or_create_conversation()

    if conv.summary is not None:
        return redirect(url_for("construction_assistant.home"))

    db.session.add(Message(conversation_id=conv.id, role="user", content=user_message))
    db.session.commit()

    count = len(conv.messages)

    if count == WARNING_AT:
        system_prompt = BASE_SYSTEM_PROMPT + WARNING_SUFFIX
    elif count == SUMMARY_AT:
        system_prompt = BASE_SYSTEM_PROMPT + SUMMARY_SUFFIX
    else:
        system_prompt = BASE_SYSTEM_PROMPT

    search_query = rewrite_query(conv, user_message)
    doc_status, context = retrieve_relevant_context(conv, search_query)
    if doc_status == "relevant":
        system_prompt += RAG_SUFFIX.format(context=context)

    api_messages = [{"role": m.role, "content": m.content} for m in conv.messages]

    reply = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=system_prompt,
        messages=api_messages,
    )
    assistant_response = reply.content[0].text
    if reply.stop_reason == "max_tokens":
        assistant_response += "\n\n_[Response was cut short — ask a follow-up if you'd like more detail.]_"

    if doc_status == "no_match":
        notice = ("_I didn't find a direct match for this question in your uploaded "
                  "documents. The answer below may draw on our earlier conversation "
                  "or general knowledge rather than the documents themselves._\n\n")
        assistant_response = notice + assistant_response

    db.session.add(Message(conversation_id=conv.id, role="assistant", content=assistant_response))

    locked = False
    if count == SUMMARY_AT:
        conv.summary = assistant_response
        session["carry_context"] = assistant_response
        locked = True

    db.session.commit()

    return render_template(
        "construction_assistant/index.html",
        history=render_history(conv.messages),
        locked=locked,
        prefill=None,
        documents=get_documents_for(conv),
    )
