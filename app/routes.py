from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response, status

from .models import FruitCreate, FruitUpdate, build_fruit_response
from .store import FruitStore


def _serialize(fruit) -> dict:
    return build_fruit_response(
        fruit_id=fruit.id,
        name=fruit.name,
        price=fruit.price,
        in_season=fruit.in_season,
        created_at=fruit.created_at,
    )


def create_router(store: FruitStore) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/fruits")
    def list_fruits(in_season: Optional[bool] = Query(default=None)) -> list[dict]:
        return [_serialize(f) for f in store.list(in_season=in_season)]

    # Must be declared before /fruits/{fruit_id} or the path param swallows it.
    @router.get("/fruits/cheapest")
    def cheapest() -> dict:
        fruit = store.cheapest()
        if fruit is None:
            raise HTTPException(status_code=404, detail="No fruits available")
        return _serialize(fruit)

    @router.get("/fruits/{fruit_id}")
    def get_fruit(fruit_id: int) -> dict:
        fruit = store.get(fruit_id)
        if fruit is None:
            raise HTTPException(status_code=404, detail="Fruit not found")
        return _serialize(fruit)

    @router.post("/fruits", status_code=status.HTTP_201_CREATED)
    def create_fruit(payload: FruitCreate) -> dict:
        fruit = store.create(
            name=payload.name,
            price=payload.price,
            in_season=payload.in_season,
        )
        return _serialize(fruit)

    @router.put("/fruits/{fruit_id}")
    def update_fruit(fruit_id: int, payload: FruitUpdate) -> dict:
        fields = payload.model_dump(exclude_unset=True)
        fruit = store.update(fruit_id, **fields)
        if fruit is None:
            raise HTTPException(status_code=404, detail="Fruit not found")
        return _serialize(fruit)

    @router.delete("/fruits/{fruit_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_fruit(fruit_id: int) -> Response:
        if not store.delete(fruit_id):
            raise HTTPException(status_code=404, detail="Fruit not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
