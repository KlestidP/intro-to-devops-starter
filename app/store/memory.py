from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Iterable, Optional

from ..models import Fruit
from .base import FruitStore


class InMemoryFruitStore(FruitStore):
    """In-memory store kept for unit tests and local dev without a database."""

    def __init__(self) -> None:
        self._items: dict[int, Fruit] = {}
        self._next_id: int = 1
        self._lock: Lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._items.clear()
            self._next_id = 1

    def seed(self, fruits: Iterable[dict]) -> None:
        self.reset()
        for f in fruits:
            self.create(
                name=f["name"],
                price=f["price"],
                in_season=f.get("in_season", False),
            )

    def list(self, in_season: Optional[bool] = None) -> list[Fruit]:
        with self._lock:
            items = list(self._items.values())
        if in_season is not None:
            items = [f for f in items if f.in_season == in_season]
        items.sort(key=lambda f: f.id)
        return items

    def create(self, *, name: str, price: float, in_season: bool) -> Fruit:
        with self._lock:
            fruit = Fruit(
                id=self._next_id,
                name=name,
                price=price,
                in_season=in_season,
                created_at=datetime.now(timezone.utc),
            )
            self._items[self._next_id] = fruit
            self._next_id += 1
        return fruit

    def get(self, fruit_id: int) -> Optional[Fruit]:
        with self._lock:
            return self._items.get(fruit_id)

    def update(self, fruit_id: int, **fields) -> Optional[Fruit]:
        with self._lock:
            existing = self._items.get(fruit_id)
            if existing is None:
                return None
            updated = existing.model_copy(update=fields)
            self._items[fruit_id] = updated
            return updated

    def delete(self, fruit_id: int) -> bool:
        with self._lock:
            if fruit_id in self._items:
                del self._items[fruit_id]
                return True
        return False

    def cheapest(self) -> Optional[Fruit]:
        with self._lock:
            items = list(self._items.values())
        if not items:
            return None
        return min(items, key=lambda f: f.price)
