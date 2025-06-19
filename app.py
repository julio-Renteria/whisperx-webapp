from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
import uuid
from docx import Document
import whisperx
import torch

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
    os.system(f"weasyprint {word_filename} {pdf_filename}")

    os.remove(temp_filename)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "text": output_text,
        "word_file": f"/outputs/{os.path.basename(word_filename)}",
        "pdf_file": f"/outputs/{os.path.basename(pdf_filename)}"
    })

async def run_whisperx(filepath, model_size):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model(model_size, device)
    audio = whisperx.load_audio(filepath)
    result = model.transcribe(audio)
    return result["text"]
