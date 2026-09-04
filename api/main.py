import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OceanTrace API")

# Allow Vite's dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PIPELINE_RESULT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "pipeline_result.json"


@app.get("/api/spill-result")
def get_spill_result():
    if not PIPELINE_RESULT_PATH.exists():
        raise HTTPException(status_code=404, detail="pipeline_result.json not found — run the pipeline first")

    with open(PIPELINE_RESULT_PATH) as f:
        return json.load(f)


@app.get("/api/health")
def health():
    return {"status": "ok"}