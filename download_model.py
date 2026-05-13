"""Download Abhinay45/XTTS-Hindi-finetuned weights from Hugging Face at startup.

Runs once on container boot. Saves files into MODEL_DIR (default /app/models/xtts_hindi).
Idempotent: skips download if files already exist.
"""
import os
from pathlib import Path
from huggingface_hub import snapshot_download

HF_REPO = os.environ.get("HF_REPO", "Abhinay45/XTTS-Hindi-finetuned")
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/app/models/xtts_hindi"))

def download():
      MODEL_DIR.mkdir(parents=True, exist_ok=True)
      marker = MODEL_DIR / ".downloaded"
      if marker.exists():
                print(f"[download_model] Already downloaded at {MODEL_DIR}, skipping.")
                return str(MODEL_DIR)
            print(f"[download_model] Pulling {HF_REPO} -> {MODEL_DIR} ...")
    snapshot_download(
              repo_id=HF_REPO,
              local_dir=str(MODEL_DIR),
              local_dir_use_symlinks=False,
              allow_patterns=["*.pth", "*.json", "*.txt", "vocab.json", "config.json"],
    )
    marker.write_text("ok")
    print("[download_model] Done.")
    return str(MODEL_DIR)

if __name__ == "__main__":
      download()
