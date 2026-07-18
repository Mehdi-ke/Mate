import os
import uuid
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import anthropic
import markdown
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from extensions import db, doc_collection
from models import Conversation, Message, Document

bp = Blueprint(
    "construction_assistant",
    __name__,
    template_folder="templates",
    url_prefix="/tools/construction-assistant",
)

client = anthropic.Anthropic()

MESSAGE_CAP = 10
WARNING_AT = 7
SUMMARY_AT = 9
MAX_DOCUMENTS = 3
UPLOAD_FOLDER = "instance/uploads"

# Chroma distance below which a retrieved chunk counts as genuinely relevant.
# Lower = stricter. Tuned against observed distances (~0.55 for a real hit,
# ~1.3 for an unrelated chunk). Adjust after testing with your own documents.
RELEVANCE_THRESHOLD = 1.5

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
        n_results=3,
        where={"doc_id": {"$in": doc_ids}},
        include=["documents", "distances", "metadatas"],
    )

    chunks = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not chunks or not distances or distances[0] > RELEVANCE_THRESHOLD:
        return ("no_match", None)

    labelled = []
    for chunk, meta in zip(chunks, metadatas):
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
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

    chunks = []
    metadatas = []

    pdf = fitz.open(save_path)
    for page_number, page in enumerate(pdf, start=1):
        page_text = page.get_text()
        if not page_text.strip():
            continue  # skip blank or image-only pages
        for chunk in splitter.split_text(page_text):
            chunks.append(chunk)
            metadatas.append({
                "doc_id": doc_id,
                "filename": file.filename,
                "page": page_number,
            })
    pdf.close()

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

    # Two clean paths:
    #   - relevant evidence found -> RAG path (append excerpts + RAG_SUFFIX)
    #   - no evidence (or no docs) -> general path, prompt left exactly as-is
    doc_status, context = retrieve_relevant_context(conv, user_message)
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

    # Documents were uploaded but none matched this question — tell the user
    # plainly, and mark the general answer that follows as not document-based.
    if doc_status == "no_match":
        notice = ("_I couldn't find anything relevant to this question in your "
                  "uploaded documents, so I can't answer from them — please "
                  "provide more relevant documents if you need a document-based "
                  "answer or ask a relevant question. Here's a general answer instead:_\n\n")
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