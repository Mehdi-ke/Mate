from flask import Blueprint, render_template, request, session
import anthropic
import markdown

bp = Blueprint(
    "construction_assistant",
    __name__,
    template_folder="templates",
    url_prefix="/tools/construction-assistant",
)

client = anthropic.Anthropic()

SYSTEM_PROMPT = "You are a construction technology advisor specialising in the UK construction industry. Provide clear, practical, and accurate guidance on construction technology, digital workflows, BIM, UK contract forms, CDM Regulations, site management, project delivery, and industry best practices. Tailor responses to UK standards and terminology, explain technical concepts in a concise and professional manner, highlight compliance or safety considerations where relevant, and acknowledge uncertainty rather than making unsupported assumptions."


@bp.route("/")
def home():
    session.pop("history", None)
    return render_template("construction_assistant/index.html", history=[])


@bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["user_message"]

    if "history" not in session:
        session["history"] = []

    session["history"].append({
        "role": "user",
        "content": user_message
    })

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=session["history"]
    )

    assistant_response = message.content[0].text

    session["history"].append({
        "role": "assistant",
        "content": assistant_response
    })

    session.modified = True

    history_rendered = []
    for msg in session["history"]:
        if msg["role"] == "assistant":
            history_rendered.append({
                "role": "assistant",
                "content": markdown.markdown(msg["content"])
            })
        else:
            history_rendered.append({
                "role": "user",
                "content": msg["content"]
            })

    return render_template("construction_assistant/index.html", history=history_rendered)
