"""FastAPI server for Hindi XTTSv2 (Coqui).

Endpoints:
  GET  /health         - liveness check
  POST /synthesize     - JSON body: {text, language='hi', speaker_wav (optional path)}
                         returns: audio/wav stream
  POST /clone          - multipart: text (form), speaker_wav (file)
                         returns: audio/wav stream

The model is loaded once on first request.
"""
import io
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from download_model import download as download_model

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("xtts-hindi")

MODEL_DIR = download_model()
DEFAULT_SPEAKER = os.environ.get("DEFAULT_SPEAKER_WAV", "")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
log.info(f"Using device: {DEVICE}")

tts = None


def get_tts():
    global tts
    if tts is None:
        from TTS.api import TTS
        log.info("Loading XTTSv2 (Hindi) model...")
        tts = TTS(
            model_path=MODEL_DIR,
            config_path=str(Path(MODEL_DIR) / "config.json"),
        ).to(DEVICE)
        log.info("Model loaded.")
    return tts


app = FastAPI(title="Hindi XTTSv2 API", version="1.0.0")


class SynthRequest(BaseModel):
    text: str
    language: str = "hi"
    speaker_wav: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE, "model_dir": MODEL_DIR}


@app.post("/synthesize")
def synthesize(req: SynthRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    speaker = req.speaker_wav or DEFAULT_SPEAKER
    if not speaker or not os.path.exists(speaker):
        raise HTTPException(
            status_code=400,
            detail="speaker_wav is required (set DEFAULT_SPEAKER_WAV env or pass in body)",
        )
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out_path = f.name
    get_tts().tts_to_file(
        text=req.text,
        file_path=out_path,
        speaker_wav=speaker,
        language=req.language,
    )
    data = Path(out_path).read_bytes()
    os.unlink(out_path)
    return StreamingResponse(io.BytesIO(data), media_type="audio/wav")


@app.post("/clone")
async def clone(
    text: str = Form(...),
    language: str = Form("hi"),
    speaker_wav: UploadFile = File(...),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref:
        ref.write(await speaker_wav.read())
        ref_path = ref.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out_path = f.name
    get_tts().tts_to_file(
        text=text,
        file_path=out_path,
        speaker_wav=ref_path,
        language=language,
    )
    data = Path(out_path).read_bytes()
    os.unlink(out_path)
    os.unlink(ref_path)
    return StreamingResponse(io.BytesIO(data), media_type="audio/wav")
