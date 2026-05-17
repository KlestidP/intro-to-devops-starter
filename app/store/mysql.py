from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine

from ..models import Fruit
from .base import FruitStore


metadata = MetaData()

fruits_table = Table(
    "fruits",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("price", Float, nullable=False),
    Column("in_season", Boolean, nullable=False, default=False),
    Column(
        "created_at",
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    ),
)


def _build_db_url() -> str:
    """Build the SQLAlchemy URL from DB_* env vars; all are required at MySQL boot."""
    try:
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        host = os.environ["DB_HOST"]
        name = os.environ["DB_NAME"]
    except KeyError as missing:
        raise RuntimeError(
            f"Missing required DB env var {missing.args[0]} for MySQL backend"
        ) from None
    port = os.environ.get("DB_PORT", "3306")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def create_engine_from_env(**kwargs) -> Engine:
    return create_engine(_build_db_url(), pool_pre_ping=True, **kwargs)


def _row_to_fruit(row) -> Fruit:
    created = row.created_at
    if created is not None and created.tzinfo is None:
        # pymysql returns naive datetimes; we stored UTC.
        created = created.replace(tzinfo=timezone.utc)
    return Fruit(
        id=row.id,
        name=row.name,
        price=row.price,
        in_season=bool(row.in_season),
        created_at=created,
    )


class MySQLFruitStore(FruitStore):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        metadata.create_all(engine)

    def reset(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(fruits_table))

    def seed(self, fruits: Iterable[dict]) -> None:
        self.reset()
        for f in fruits:
            self.create(
                name=f["name"],
                price=f["price"],
                in_season=f.get("in_season", False),
            )

    def list(self, in_season: Optional[bool] = None) -> list[Fruit]:
        stmt = select(fruits_table).order_by(fruits_table.c.id)
        if in_season is not None:
            stmt = stmt.where(fruits_table.c.in_season == in_season)
        with self._engine.connect() as conn:
            return [_row_to_fruit(r) for r in conn.execute(stmt)]

    def create(self, *, name: str, price: float, in_season: bool) -> Fruit:
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            result = conn.execute(
                insert(fruits_table).values(
                    name=name,
                    price=price,
                    in_season=in_season,
                    created_at=now,
                )
            )
            new_id = result.inserted_primary_key[0]
            row = conn.execute(
                select(fruits_table).where(fruits_table.c.id == new_id)
            ).one()
        return _row_to_fruit(row)

    def get(self, fruit_id: int) -> Optional[Fruit]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(fruits_table).where(fruits_table.c.id == fruit_id)
            ).one_or_none()
        return _row_to_fruit(row) if row is not None else None

    def update(self, fruit_id: int, **fields) -> Optional[Fruit]:
        if not fields:
            return self.get(fruit_id)
        with self._engine.begin() as conn:
            result = conn.execute(
                update(fruits_table).where(fruits_table.c.id == fruit_id).values(**fields)
            )
            if result.rowcount == 0:
                return None
            row = conn.execute(
                select(fruits_table).where(fruits_table.c.id == fruit_id)
            ).one()
        return _row_to_fruit(row)

    def delete(self, fruit_id: int) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(
                delete(fruits_table).where(fruits_table.c.id == fruit_id)
            )
        return result.rowcount > 0

    def cheapest(self) -> Optional[Fruit]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(fruits_table).order_by(fruits_table.c.price.asc()).limit(1)
            ).one_or_none()
        return _row_to_fruit(row) if row is not None else None
