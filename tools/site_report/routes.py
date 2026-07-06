from flask import Blueprint, render_template, request
import anthropic
from datetime import date
import base64

bp = Blueprint(
    "site_report",
    __name__,
    template_folder="templates",
    url_prefix="/tools/site-report",
)

client = anthropic.Anthropic()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_media_type(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif"
    }
    return media_types.get(ext, "image/jpeg")
def is_construction_relevant(text):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system="You are a validator. Reply only with YES or NO.",
        messages=[
            {
                "role": "user",
                "content": f"Is this description relevant to construction site work, building activities, or site management? Reply YES or NO only.\n\n{text}"
            }
        ]
    )
    result = message.content[0].text.strip().upper()
    return result.startswith("YES")

def generate_site_report(worker_input, site_name, image_data=None, media_type=None):
    today = date.today().strftime("%d/%m/%Y")

    system_prompt = f"""You are a construction site report assistant for UK construction projects.
Convert the worker's description into a formal site report.

STRICT RULES — follow these without exception:
1. Capitalise proper nouns — site names, place names, project names must be properly capitalised (e.g. "Manchester" not "manchester").
2. The worker's description is the PRIMARY source of truth. Never add information not stated by the worker.
3. Never write quality statements like "Work completed to standard" or "Concrete finish satisfactory" unless the worker explicitly says so.
4. Never guess or assume missing information. Write "Not reported" if uncertain.
5. Distinguish clearly between materials USED/DELIVERED and materials REQUIRED/ORDERED.
6. Keep ISSUES RAISED for actual problems only — delays, defects, shortages, access issues, incidents.
7. Keep REQUESTS / ACTIONS REQUIRED separate — worker requests, material orders, planned procurement.
8. Never infer information from the image that the worker has not mentioned.

FORMAT — include every section below, in this exact order:

DATE: {today}

SITE: {site_name.strip().title() if site_name else "[Extract from input — properly capitalised. If not mentioned write Not specified]"}

PROJECT:
[Extract project name or description from input — properly capitalised. If not mentioned write "Not specified".]

WEATHER:
[Extract from worker's description only. If not mentioned write "Not recorded". Do not infer from image.]

WORKFORCE:
[Trades or number of workers mentioned by the worker. If not mentioned write "Not reported".]

ACTIVITIES COMPLETED:
- [List only work the worker confirms was completed. Do not assume completion unless stated.]

MATERIALS DELIVERED / USED:
- [Materials the worker confirms were delivered or used today. If none mentioned write "None reported".]

MATERIALS REQUIRED / ORDERED:
- [Materials the worker says are needed or ordered for upcoming work. If none mentioned write "None reported".]

PLANT & EQUIPMENT USED:
- [Machinery or equipment mentioned by the worker. If not mentioned write "Not reported". Do not add equipment seen only in image.]

QUALITY OBSERVATIONS:
- [Only record quality statements explicitly made by the worker. If none made write "None reported".]

SAFETY OBSERVATIONS:
- [PPE observations, hazards identified, incidents and near misses, safety actions taken. If none mentioned write "None reported".]

ISSUES RAISED:
- [Actual problems that affect programme, access, quality or cost — delays, defects, shortages, access issues. Do NOT repeat safety incidents here unless they also caused a programme or access problem.]

REQUESTS / ACTIONS REQUIRED:
- [Worker requests, procurement needs, actions needed from others. If none write "None reported".]

NEXT DAY PLAN:
- [Planned work for tomorrow as stated by the worker. If not mentioned write "Not reported".]

FURTHER DETAILS:
[Only include information genuinely not captured in any other section. Do not repeat items already listed above. If nothing further write "None".]

REPORT COMPILED BY:
AI Site Assistant

Return only the completed report. No introduction. No closing remarks. No extra text."""

    if image_data:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": f"""Convert this to a site report: {worker_input}

At the end of the report, after REPORT COMPILED BY, add this section:

SITE PHOTO OBSERVATIONS:
[Write 2-4 factual sentences based strictly on what is clearly visible in the image AND supported by the worker's description.
Rules:
- Only describe what can be clearly seen — do not speculate.
- Do not infer weather from the image.
- Do not identify people.
- Do not describe architectural details such as facades, balconies, finishes or building aesthetics — these are never relevant to a site diary report.
- Only describe: materials visible, plant and equipment, ground conditions, work areas, site organisation, safety observations directly relevant to the worker's account.
- Focus only on: construction progress relevant to the worker's account, materials or equipment visible that support the worker's description, site conditions, safety observations, visible issues.
- If the image supports the worker's account, say so specifically.
- If something is not clearly visible write "Not clearly visible" rather than guessing.
- The worker's description takes priority. The image is supplementary evidence only.]"""
                    }
                ]
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": f"Convert this to a site report: {worker_input}"
            }
        ]

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )

    return message.content[0].text

@bp.route("/")
def home():
    return render_template("site_report/index.html")

@bp.route("/generate", methods=["POST"])
def generate():
    worker_input = request.form["worker_input"]
    site_name = request.form["site_name"]
    include_transcript = request.form.get("include_transcript") == "yes"

    upload_message = None
    image_data = None
    media_type = None
    validation_error = None

    if not worker_input.strip():
        validation_error = "Please describe your day on site before generating a report."
        return render_template("site_report/index.html",
                             validation_error=validation_error,
                             site_name=site_name)

    if not is_construction_relevant(worker_input):
        validation_error = "Your description does not appear to be related to construction site work. Please describe your day on site — activities completed, any issues, and tomorrow's plan — and try again."
        return render_template("site_report/index.html",
                             validation_error=validation_error,
                             worker_input=worker_input,
                             site_name=site_name)

    if "site_photo" in request.files:
        file = request.files["site_photo"]
        if file.filename != "":
            if not allowed_file(file.filename):
                upload_message = "File type not allowed. Please upload a PNG, JPG or GIF."
            else:
                file_bytes = file.read()
                if len(file_bytes) > MAX_FILE_SIZE:
                    upload_message = "File too large. Maximum size is 5MB."
                else:
                    image_data = base64.standard_b64encode(file_bytes).decode("utf-8")
                    media_type = get_media_type(file.filename)
                    upload_message = f"Photo uploaded and analysed: {file.filename}"

    report = generate_site_report(worker_input, site_name, image_data, media_type)

    return render_template("site_report/index.html",
                         report=report,
                         worker_input=worker_input,
                         site_name=site_name,
                         upload_message=upload_message,
                         image_data=image_data,
                         media_type=media_type,
                         include_transcript=include_transcript)
