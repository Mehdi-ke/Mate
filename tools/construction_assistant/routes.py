from flask import Blueprint, render_template, request, session, redirect, url_for
import anthropic
import markdown

from extensions import db
from models import Conversation, Message

bp = Blueprint(
    "construction_assistant",
    __name__,
    template_folder="templates",
    url_prefix="/tools/construction-assistant",
)

client = anthropic.Anthropic()

MESSAGE_CAP = 10
WARNING_AT = 7   # count after saving user msg = 7 → this reply is the warning
SUMMARY_AT = 9   # count after saving user msg = 9 → this reply is the summary

BASE_SYSTEM_PROMPT = "You are a construction technology advisor specialising in the UK construction industry. Provide clear, practical, and accurate guidance on construction technology, digital workflows, BIM, UK contract forms, CDM Regulations, site management, project delivery, and industry best practices. Tailor responses to UK standards and terminology, explain technical concepts in a concise and professional manner, highlight compliance or safety considerations where relevant, and acknowledge uncertainty rather than making unsupported assumptions. Match the length of your response to the depth of the question — be brief for simple questions and thorough for complex ones, but never pad."

WARNING_SUFFIX = " IMPORTANT: This is the fourth of five exchanges in this conversation. After answering the user's question normally, end your reply with a brief, friendly note (one short sentence) that you're approaching a good moment to start a fresh chat soon."

SUMMARY_SUFFIX = " IMPORTANT: This is the final exchange in this conversation. Instead of answering normally, produce a concise summary of the entire conversation as 3-5 bullet points capturing the key questions asked and the key guidance given. Format it so the user can paste it into a new chat as context. Start with a brief sentence explaining this is a wrap-up summary, then the bullets."


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
            )

    session.pop("conversation_id", None)
    return render_template(
        "construction_assistant/index.html",
        history=[],
        locked=False,
        prefill=carry,
    )


@bp.route("/new")
def new():
    session.pop("conversation_id", None)
    session.pop("carry_context", None)
    return redirect(url_for("construction_assistant.home"))


@bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["user_message"]

    conv = get_or_create_conversation()

    # Safety net: refuse if this conversation is already capped
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
    )