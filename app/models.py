from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FruitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    in_season: bool = False


class FruitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1)
    price: Optional[float] = Field(default=None, ge=0)
    in_season: Optional[bool] = None


class Fruit(BaseModel):
    id: int
    name: str
    price: float
    in_season: bool
    created_at: datetime


def build_fruit_response(
    *,
    fruit_id: int,
    name: str,
    price: float,
    in_season: bool,
    created_at: datetime,
) -> dict:
    """Free function so the response shape can be unit-tested without the HTTP layer."""
    return {
        "id": fruit_id,
        "name": name,
        "price": price,
        "in_season": in_season,
        "created_at": created_at.isoformat(),
    }
