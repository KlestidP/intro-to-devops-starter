from __future__ import annotations

import os

import uvicorn

from app.main import app  # re-exported so `uvicorn main:app` also resolves


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
