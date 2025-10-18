import os
import tempfile
import json
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from uvicorn import run as run_app
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

from scraper import scrape_internships

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_GEMINI_API")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Internship Matcher")

# Allow frontend to call this API during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Extract text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# Extract text from DOCX
def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


# Extract text based on file extension
def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith((".docx", ".doc")):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Please upload PDF or DOCX.")


# Response model
class ProfileGeminiResponse(BaseModel):
    fields: list[str]
    skills: list[str]
    level: str
    location: str = ""


class ProfileResponse(BaseModel):
    field: str
    skills: list[str]
    level: str
    location: str = ""


@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")


@app.post("/upload-cv", response_model=ProfileGeminiResponse)
async def upload_cv(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX files are allowed."
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extract text
        cv_text = extract_text(tmp_path)
        if not cv_text.strip():
            raise HTTPException(status_code=400, detail="CV is empty or unreadable.")

        # Truncate to avoid token limits
        cv_excerpt = cv_text[:5000]

        # Prompt for Gemini
        prompt = f"""
            Analyze the following CV excerpt and return a JSON object with exactly these keys:
            - "fields": a list of 2–4 professional fields the candidate is qualified for (e.g., ["Data Engineering", "Machine Learning", "Cloud Infrastructure"])
            - "skills": a list of technical skills (e.g., ["Python", "Docker", "AWS"])
            - "level": the candidate's level (e.g., "Master's Student", "Junior Developer")

            Only return valid JSON. Do not include any other text.

            CV Excerpt:
            {cv_excerpt}
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        # Parse JSON response
        try:
            profile = json.loads(response.text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response.")

        # Validate structure
        required_keys = {"fields", "skills", "level"}
        if not required_keys.issubset(profile.keys()):
            raise HTTPException(
                status_code=500, detail="AI response missing required fields."
            )

        if not isinstance(profile["fields"], list) or len(profile["fields"]) == 0:
            raise HTTPException(
                status_code=500, detail="AI returned invalid 'fields' format."
            )

        return ProfileGeminiResponse(
            fields=profile["fields"], skills=profile["skills"], level=profile["level"]
        )
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@app.post("/scrape-internships")
def scrape_endpoint(profile: ProfileResponse):
    jobs = scrape_internships(profile.field, profile.location)
    return {"count": len(jobs), "jobs": jobs}


if __name__ == "__main__":
    run_app(app, host="localhost", port=8000)
