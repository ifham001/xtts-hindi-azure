# xtts-hindi-azure

A Hindi text-to-speech HTTP API built on top of **Coqui XTTSv2** fine-tuned on Hindi (`Abhinay45/XTTS-Hindi-finetuned`), wrapped in **FastAPI**, containerised for **Azure Container Apps**.

> ⚠️ **License notice**: The base XTTSv2 model uses the [Coqui Public Model License](https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt) which permits **non-commercial use only**. The fine-tune inherits this restriction. Do not use this image in a commercial product.

## Features

- Hindi (`hi`) text-to-speech
- Voice cloning from any 6–10 second reference clip
- 24 kHz output
- Streams `audio/wav` over HTTP
- Container-ready, scales to zero on Azure Container Apps

## Endpoints

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/health` | — | JSON status |
| POST | `/synthesize` | JSON `{text, language?, speaker_wav?}` | `audio/wav` |
| POST | `/clone` | multipart: `text`, `speaker_wav` (file) | `audio/wav` |

### Example: clone a voice in Hindi

```bash
curl -X POST https://YOUR-APP.azurecontainerapps.io/clone \
  -F "text=नमस्ते! मेरा नाम स्वरा है।" \
  -F "language=hi" \
  -F "speaker_wav=@reference.wav" \
  --output out.wav
```

## Run locally

```bash
pip install -r requirements.txt
python download_model.py        # one-time, ~2GB download from HF
uvicorn server:app --reload --port 8000
```

## Run with Docker

```bash
docker build -t xtts-hindi .
docker run --rm -p 8000:8000 xtts-hindi
# First boot downloads weights to /app/models/xtts_hindi (~2GB)
```

Mount a volume to cache the weights between runs:

```bash
docker run --rm -p 8000:8000 -v $(pwd)/models:/app/models xtts-hindi
```

## Deploy to Azure Container Apps (CPU)

```bash
az login
az extension add -n containerapp --upgrade

az group create -n rg-xtts-hindi -l centralindia

az containerapp up \
  --name xtts-hindi \
  --resource-group rg-xtts-hindi \
  --location centralindia \
  --environment xtts-env \
  --source https://github.com/ifham001/xtts-hindi-azure.git \
  --target-port 8000 \
  --ingress external
```

## Deploy with GPU (recommended for real-time)

Azure Container Apps supports serverless GPU (T4 / A100). After creating an env with workload profile:

```bash
az containerapp env workload-profile add \
  -g rg-xtts-hindi -n xtts-env \
  --workload-profile-name gpu-t4 \
  --workload-profile-type Consumption-GPU-NC8as-T4
```

Then update the app to use the `gpu-t4` profile and rebuild Dockerfile from `nvidia/cuda:11.8-runtime` with `torch+cu118`.

## Environment variables

| Var | Default | Purpose |
|-----|---------|---------|
| `HF_REPO` | `Abhinay45/XTTS-Hindi-finetuned` | source model on Hugging Face |
| `MODEL_DIR` | `/app/models/xtts_hindi` | local path for weights |
| `DEFAULT_SPEAKER_WAV` | `""` | optional default reference clip |
| `PORT` | `8000` | HTTP port |

## Credits

- Base model: [coqui/XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- Hindi fine-tune: [Abhinay45/XTTS-Hindi-finetuned](https://huggingface.co/Abhinay45/XTTS-Hindi-finetuned)
- Toolkit: [Coqui TTS](https://github.com/coqui-ai/TTS) (archived)

## License

Code in this repository is MIT.  
Model weights and outputs follow the **Coqui Public Model License** (non-commercial).
