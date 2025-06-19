from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
import uuid
from docx import Document
import subprocess

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcribe")
async def transcribe_audio(request: Request, file: UploadFile, model_size: str = Form(...)):
    temp_filename = f"temp_{uuid.uuid4()}.mp3"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    output_text = await run_whisperx(temp_filename, model_size)

    word_filename = os.path.join(OUTPUT_DIR, f"{uuid.uuid4()}.docx")
    doc = Document()
    doc.add_paragraph(output_text)
    doc.save(word_filename)

    pdf_filename = word_filename.replace(".docx", ".pdf")
    subprocess.run(["weasyprint", word_filename, pdf_filename])

    os.remove(temp_filename)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "text": output_text,
        "word_file": f"/outputs/{os.path.basename(word_filename)}",
        "pdf_file": f"/outputs/{os.path.basename(pdf_filename)}"
    })

async def run_whisperx(filepath, model_size):
    command = [
        "whisperx", filepath,
        "--model", model_size,
        "--output_format", "txt",
        "--output_dir", OUTPUT_DIR
    ]
    subprocess.run(command, check=True)

    output_txt = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".txt")][-1]
    with open(os.path.join(OUTPUT_DIR, output_txt), "r", encoding="utf-8") as f:
        text = f.read()

    return text
