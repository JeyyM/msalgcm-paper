"""Start the FastAPI dev server without requiring an editable pip install."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
os.environ.setdefault("PYTHONPATH", str(SRC))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import uvicorn  # noqa: E402

# Reload when Python sources change. On Windows, watch the full package (not just api/)
# so new routes under services/ are picked up without a manual restart.
USE_RELOAD = True
RELOAD_DIRS = [str(SRC / "optimize")]

if __name__ == "__main__":
    port = int(os.environ.get("DEV_API_PORT", "8002"))
    uvicorn.run(
        "optimize.api.app:app",
        host="127.0.0.1",
        port=port,
        reload=USE_RELOAD,
        reload_dirs=RELOAD_DIRS if USE_RELOAD else None,
    )
