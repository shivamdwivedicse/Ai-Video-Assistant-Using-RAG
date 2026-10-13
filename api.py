import os
import uuid
import threading
import traceback

from dotenv import load_dotenv

load_dotenv()  # must run before core imports (transcriber reads env at import)

import imageio_ffmpeg
_d = "/tmp/ffbin"
os.makedirs(_d, exist_ok=True)
_l = os.path.join(_d, "ffmpeg")
if not os.path.exists(_l):
       os.symlink(imageio_ffmpeg.get_ffmpeg_exe(), _l)
       os.environ["PATH"] = _d + os.pathsep + os.environ["PATH"]

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question

app = FastAPI(title="VidRAG AI")

UPLOAD_DIR = "downloads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

JOBS: dict = {}    # job_id -> status/result (JSON safe)
CHAINS: dict = {}  # job_id -> rag_chain (not JSON safe)

STEPS = ["Audio", "Transcribe", "Understand", "Extract", "Index"]


import re


def get_captions(url: str):
    """Fast path: fetch YouTube captions directly (no download, no Whisper)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    if not m:
        return None
    api = YouTubeTranscriptApi()
    vid = m.group(1)
    try:
        fetched = api.fetch(vid, languages=["en", "en-US", "en-GB", "hi"])
    except Exception:
        try:
            fetched = next(iter(api.list(vid))).fetch()  # any available caption
        except Exception:
            return None
    text = " ".join(sn.text for sn in fetched).strip()
    return text or None


def _set(job_id, **kw):
    JOBS[job_id].update(kw)


def run_job(job_id: str, source: str, language: str):
    try:
        transcript = None
        if source.startswith("http"):
            _set(job_id, step=0, progress=8, message="Fetching YouTube captions...")
            transcript = get_captions(source)

        if transcript is None:  # no captions / not YouTube -> original pipeline
            _set(job_id, step=0, progress=8, message="Extracting audio...")
            chunks = process_input(source)
            _set(job_id, step=1, progress=25, message="Transcribing speech...")
            transcript = transcribe_all(chunks, language=language)

        _set(job_id, step=2, progress=50, message="Understanding the video...")
        title = generate_title(transcript)
        summary = summarize(transcript)

        _set(job_id, step=3, progress=68, message="Extracting insights...")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        _set(job_id, step=4, progress=88, message="Building knowledge base...")
        CHAINS[job_id] = build_rag_chain(transcript)

        _set(
            job_id,
            status="done",
            progress=100,
            message="Done",
            result={
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
            },
        )
    except Exception as e:
        traceback.print_exc()
        _set(job_id, status="error", error=str(e), message="Failed")


@app.post("/api/analyze")
async def analyze(
    language: str = Form("english"),
    url: str = Form(""),
    file: UploadFile | None = File(None),
):
    if file is not None and file.filename:
        safe = f"{uuid.uuid4().hex[:8]}_{os.path.basename(file.filename)}"
        path = os.path.join(UPLOAD_DIR, safe)
        with open(path, "wb") as f:
            f.write(await file.read())
        source = path
    elif url.strip():
        source = url.strip()
    else:
        raise HTTPException(400, "Provide a YouTube URL or upload a file.")

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "status": "running",
        "step": 0,
        "progress": 2,
        "message": "Starting...",
        "steps": STEPS,
        "is_url": source.startswith("http"),
    }
    print(f"JOB CREATED | ID={job_id} | PID={os.getpid()}")
    threading.Thread(
        target=run_job, args=(job_id, source, language), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)

    print(
        f"JOB CHECK | ID={job_id} | "
        f"FOUND={job is not None} | "
        f"PID={os.getpid()} | "
        f"TOTAL_JOBS={len(JOBS)}"
    )

    if not job:
        raise HTTPException(404, "Job not found")

    return job


class ChatIn(BaseModel):
    job_id: str
    question: str


@app.post("/api/chat")
def chat(body: ChatIn):
    chain = CHAINS.get(body.job_id)
    if not chain:
        raise HTTPException(404, "Analysis not ready or expired")
    try:
        return {"answer": ask_question(chain, body.question)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/")
def index():
    return FileResponse("web/index.html")


app.mount("/", StaticFiles(directory="web"), name="web")