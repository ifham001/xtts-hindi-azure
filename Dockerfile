# Hindi XTTSv2 (Coqui) FastAPI server
# CPU build by default; for GPU change base image to nvidia/cuda + install torch+cu118
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    MODEL_DIR=/app/models/xtts_hindi \
    PORT=8000

WORKDIR /app

# System deps for audio + torch
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git ffmpeg libsndfile1 espeak-ng curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-create the model dir; actual weights are pulled at runtime by download_model.py
RUN mkdir -p /app/models/xtts_hindi

COPY download_model.py server.py ./

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
