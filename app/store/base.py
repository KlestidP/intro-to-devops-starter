from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..models import Fruit


class FruitStore(ABC):
    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def seed(self, fruits: Iterable[dict]) -> None: ...

    @abstractmethod
    def list(self, in_season: Optional[bool] = None) -> list[Fruit]: ...

    @abstractmethod
    def create(self, *, name: str, price: float, in_season: bool) -> Fruit: ...

    @abstractmethod
    def get(self, fruit_id: int) -> Optional[Fruit]: ...

    @abstractmethod
    def update(self, fruit_id: int, **fields) -> Optional[Fruit]: ...

    @abstractmethod
    def delete(self, fruit_id: int) -> bool: ...

    @abstractmethod
    def cheapest(self) -> Optional[Fruit]: ...
