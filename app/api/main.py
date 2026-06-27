import asyncio
import os
import tempfile
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from app.agent import root_agent
from app.api.pdf_utils import build_report_pdf
from app.mcp_servers.farmer_report_server import generate_farmer_report

IMAGE_FILE = File(...)
SOIL_TYPE_FORM = Form(None)
LANGUAGE_FORM = Form("en")

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
}

TEXT = {
    "en": {
        "report_title": "SoilSense AI Farmer Report",
        "summary": "Soil Summary",
        "soil_seen": "Soil identified from photo",
        "confidence": "Photo confidence",
        "why": "Why we think so",
        "estimated_nutrients": "Approximate Nutrient Values",
        "health": "Soil Health",
        "crop": "Crop Guidance",
        "fertilizer": "Fertilizer Guidance",
        "next_steps": "Next Steps",
        "closest": "Closest known soil group",
        "health_score": "Estimated health score",
        "crop_label": "Suggested crop",
        "fertilizer_label": "Suggested fertilizer",
        "confidence_label": "confidence",
        "note": "These values are photo-based estimates. For final fertilizer dosage, confirm with a local soil test or agriculture officer.",
        "steps": [
            "Use this report as quick guidance before planning the crop.",
            "If the crop is high-value, confirm nutrient levels with a soil test.",
            "Apply fertilizer in split doses and adjust for local rainfall and irrigation.",
        ],
        "not_available": "Not available",
    },
    "hi": {
        "report_title": "SoilSense AI किसान रिपोर्ट",
        "summary": "मिट्टी सारांश",
        "soil_seen": "फोटो से पहचानी गई मिट्टी",
        "confidence": "फोटो भरोसा",
        "why": "पहचान का कारण",
        "estimated_nutrients": "अनुमानित पोषक मान",
        "health": "मिट्टी स्वास्थ्य",
        "crop": "फसल सलाह",
        "fertilizer": "उर्वरक सलाह",
        "next_steps": "अगले कदम",
        "closest": "सबसे नजदीकी मिट्टी समूह",
        "health_score": "अनुमानित स्वास्थ्य अंक",
        "crop_label": "सुझाई गई फसल",
        "fertilizer_label": "सुझाया गया उर्वरक",
        "confidence_label": "भरोसा",
        "note": "ये मान फोटो के आधार पर अनुमान हैं। अंतिम उर्वरक मात्रा के लिए स्थानीय मिट्टी परीक्षण या कृषि अधिकारी से पुष्टि करें।",
        "steps": [
            "फसल योजना से पहले इस रिपोर्ट को शुरुआती सलाह की तरह उपयोग करें।",
            "यदि फसल अधिक मूल्य की है, तो पोषक स्तर मिट्टी परीक्षण से पक्का करें।",
            "उर्वरक को किस्तों में दें और स्थानीय वर्षा व सिंचाई के अनुसार मात्रा बदलें।",
        ],
        "not_available": "उपलब्ध नहीं",
    },
    "te": {
        "report_title": "SoilSense AI రైతు నివేదిక",
        "summary": "మట్టి సారాంశం",
        "soil_seen": "ఫోటో ద్వారా గుర్తించిన మట్టి",
        "confidence": "ఫోటో విశ్వసనీయత",
        "why": "గుర్తించిన కారణం",
        "estimated_nutrients": "అంచనా పోషక విలువలు",
        "health": "మట్టి ఆరోగ్యం",
        "crop": "పంట సూచన",
        "fertilizer": "ఎరువు సూచన",
        "next_steps": "తదుపరి చర్యలు",
        "closest": "దగ్గరలోని మట్టి సమూహం",
        "health_score": "అంచనా ఆరోగ్య స్కోరు",
        "crop_label": "సూచించిన పంట",
        "fertilizer_label": "సూచించిన ఎరువు",
        "confidence_label": "విశ్వసనీయత",
        "note": "ఈ విలువలు ఫోటో ఆధారంగా అంచనా మాత్రమే. తుది ఎరువు మోతాదు కోసం స్థానిక మట్టి పరీక్ష లేదా వ్యవసాయ అధికారిని సంప్రదించండి.",
        "steps": [
            "పంట ప్రణాళికకు ముందు ఈ నివేదికను మొదటి సూచనగా ఉపయోగించండి.",
            "అధిక విలువ గల పంట అయితే పోషక స్థాయులను మట్టి పరీక్షతో నిర్ధారించండి.",
            "ఎరువును విడతలుగా వేయండి; స్థానిక వర్షం మరియు నీటిపారుదల ప్రకారం మోతాదు మార్చండి.",
        ],
        "not_available": "అందుబాటులో లేదు",
    },
}

NUTRIENT_LABELS = {
    "en": {
        "nitrogen": "Nitrogen",
        "phosphorus": "Phosphorus",
        "potassium": "Potassium",
        "sulphur": "Sulphur",
        "iron": "Iron",
        "zinc": "Zinc",
        "copper": "Copper",
        "boron": "Boron",
        "magnesium": "Magnesium",
        "ph": "pH",
        "organic_carbon": "Organic carbon",
        "electrical_conductivity": "Electrical conductivity",
    },
    "hi": {
        "nitrogen": "नाइट्रोजन",
        "phosphorus": "फॉस्फोरस",
        "potassium": "पोटैशियम",
        "sulphur": "सल्फर",
        "iron": "लोहा",
        "zinc": "जिंक",
        "copper": "कॉपर",
        "boron": "बोरोन",
        "magnesium": "मैग्नीशियम",
        "ph": "पीएच",
        "organic_carbon": "जैविक कार्बन",
        "electrical_conductivity": "विद्युत चालकता",
    },
    "te": {
        "nitrogen": "నైట్రోజన్",
        "phosphorus": "ఫాస్ఫరస్",
        "potassium": "పొటాషియం",
        "sulphur": "సల్ఫర్",
        "iron": "ఇనుము",
        "zinc": "జింక్",
        "copper": "కాపర్",
        "boron": "బోరాన్",
        "magnesium": "మెగ్నీషియం",
        "ph": "పీహెచ్",
        "organic_carbon": "సేంద్రీయ కార్బన్",
        "electrical_conductivity": "విద్యుత్ వాహకత",
    },
}

SOIL_TRANSLATIONS = {
    "hi": {
        "Black Cotton": "काली कपास मिट्टी",
        "Peaty": "पीट वाली मिट्टी",
        "Red Loam": "लाल दोमट मिट्टी",
        "Red Sandy": "लाल रेतीली मिट्टी",
        "Laterite": "लेटराइट मिट्टी",
        "Saline Soil": "लवणीय मिट्टी",
        "Sandy Loam": "रेतीली दोमट मिट्टी",
        "Clay": "चिकनी मिट्टी",
        "Clay Loam": "चिकनी दोमट मिट्टी",
        "Alluvial": "जलोढ़ मिट्टी",
        "Chalky Soil": "चूना युक्त मिट्टी",
        "Rocky or Gravelly Soil": "कंकरीली मिट्टी",
        "Silty Soil": "गाद वाली मिट्टी",
        "Loamy Soil": "दोमट मिट्टी",
    },
    "te": {
        "Black Cotton": "నల్ల పత్తి మట్టి",
        "Peaty": "పీట్ మట్టి",
        "Red Loam": "ఎర్ర లోమ్ మట్టి",
        "Red Sandy": "ఎర్ర ఇసుక మట్టి",
        "Laterite": "లేటరైట్ మట్టి",
        "Saline Soil": "ఉప్పు మట్టి",
        "Sandy Loam": "ఇసుక లోమ్ మట్టి",
        "Clay": "బంకమట్టి",
        "Clay Loam": "బంక లోమ్ మట్టి",
        "Alluvial": "ఒండ్రు మట్టి",
        "Chalky Soil": "సున్నపు మట్టి",
        "Rocky or Gravelly Soil": "రాళ్ల మట్టి",
        "Silty Soil": "సిల్ట్ మట్టి",
        "Loamy Soil": "లోమ్ మట్టి",
    },
}

REPORT_LABEL_TRANSLATIONS = {
    "en": {},
    "hi": {},
    "te": {},
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    language: str = "en"
    user_id: str | None = None


class PdfReportRequest(BaseModel):
    report: str = Field(..., min_length=1)
    filename: str = "soil-farmer-report.pdf"


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/chat-page", include_in_schema=False)
def chat_page():
    return RedirectResponse(url="/static/chat.html")


@app.post("/report")
async def report(
    image: UploadFile = IMAGE_FILE,
    soil_type: str | None = SOIL_TYPE_FORM,
    language: str = LANGUAGE_FORM,
):
    suffix = Path(image.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        content = await image.read()
        tmp.write(content)
    try:
        result = await generate_farmer_report(image_path=tmp_path, soil_type=soil_type)
    finally:
        os.remove(tmp_path)

    result["language"] = _normalize_language(language)
    if "report" in result:
        result["report"] = _translate_report(result["report"], language)
        result["download_filename"] = _report_filename(result.get("soil_type"))
    return result


@app.post("/chat")
async def chat(request: ChatRequest):
    language = _normalize_language(request.language)
    message = _message_with_language_instruction(request.message, language)
    response_text = await asyncio.to_thread(
        _run_agent_message,
        message,
        request.user_id or f"web-{uuid.uuid4().hex}",
    )
    return {"response": response_text, "language": language}


@app.post("/report/pdf")
async def report_pdf(request: PdfReportRequest):
    filename = _pdf_filename(request.filename)
    pdf_bytes = build_report_pdf(request.report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _normalize_language(language: str | None) -> str:
    language_key = (language or "en").lower()
    return language_key if language_key in LANGUAGE_NAMES else "en"


def _message_with_language_instruction(message: str, language: str) -> str:
    language_name = LANGUAGE_NAMES[_normalize_language(language)]
    return (
        f"Please answer in {language_name}. Keep the answer farmer-friendly.\n\n"
        f"User query: {message}"
    )


def _run_agent_message(message: str, user_id: str) -> str:
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id=user_id, app_name="app")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)],
    )
    events = list(
        runner.run(
            new_message=content,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    text_parts: list[str] = []
    for event in events:
        if event.content and event.content.parts:
            text_parts.extend(part.text for part in event.content.parts if part.text)

    if text_parts:
        return "\n".join(text_parts).strip()

    return (
        "The agent could not produce a text response. Please retry the same "
        "soil question in a moment."
    )


def _translate_report(report: str, language: str | None) -> str:
    translated = report
    for source, target in REPORT_LABEL_TRANSLATIONS.get(_normalize_language(language), {}).items():
        translated = translated.replace(source, target)
    return translated


def _report_filename(soil_type: str | None) -> str:
    safe_soil = (soil_type or "soil").lower().replace(" ", "-")
    return f"{safe_soil}-farmer-report.pdf"


def _pdf_filename(filename: str) -> str:
    safe = "".join(
        character for character in filename if character.isalnum() or character in "-_."
    ).strip(".")
    if not safe:
        safe = "soil-farmer-report.pdf"
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf"
    return safe


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
