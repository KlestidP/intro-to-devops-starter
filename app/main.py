from __future__ import annotations

from typing import Optional

from fastapi import FastAPI

from .routes import create_router
from .store import FruitStore


def create_app(store: Optional[FruitStore] = None) -> FastAPI:
    """Each call returns a new app with its own store so unit tests stay isolated."""
    app = FastAPI(title="FruitAPI", version="0.1.0")
    app.state.store = store if store is not None else FruitStore()
    app.include_router(create_router(app.state.store))
    return app


app = create_app()
