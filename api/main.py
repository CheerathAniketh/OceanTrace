import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OceanTrace API")

# Allow Vite dev server on localhost AND on LAN (e.g. demo laptop by IP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # read-only public GET endpoint, fine for a hackathon demo (local dev + LAN)
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
SYNTHETIC_RESULT_PATH = OUTPUTS_DIR / "pipeline_result.json"
REAL_RESULT_PATH = OUTPUTS_DIR / "pipeline_result_real.json"

# Set OCEANTRACE_MODE=real as an env var before starting uvicorn to serve
# the real Sentinel-1 result instead of the synthetic demo result.
DEFAULT_MODE = os.environ.get("OCEANTRACE_MODE", "synthetic")


@app.get("/api/spill-result")
def get_spill_result(mode: str = None):
    """
    mode: optional query param, "synthetic" (default) or "real".
    Falls back to OCEANTRACE_MODE env var, then to synthetic.
    Example: /api/spill-result?mode=real
    """
    selected_mode = mode or DEFAULT_MODE
    path = REAL_RESULT_PATH if selected_mode == "real" else SYNTHETIC_RESULT_PATH

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{path.name} not found — run `python -m pipeline.run_pipeline"
                    f"{' --real' if selected_mode == 'real' else ''}` first",
        )

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=503,
            detail="Result file is being written right now — try again in a moment",
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "synthetic_available": SYNTHETIC_RESULT_PATH.exists(),
        "real_available": REAL_RESULT_PATH.exists(),
    }