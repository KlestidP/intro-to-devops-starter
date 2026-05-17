from __future__ import annotations

import os

from .base import FruitStore
from .memory import InMemoryFruitStore
from .mysql import MySQLFruitStore, create_engine_from_env

__all__ = [
    "FruitStore",
    "InMemoryFruitStore",
    "MySQLFruitStore",
    "create_engine_from_env",
    "create_default_store",
]


def create_default_store() -> FruitStore:
    """Pick MySQL when DB_HOST is set; otherwise fall back to in-memory."""
    if os.environ.get("DB_HOST"):
        return MySQLFruitStore(create_engine_from_env())
    return InMemoryFruitStore()
