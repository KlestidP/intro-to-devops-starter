from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import build_fruit_response


SEED = [
    {"name": "apple", "price": 1.0, "in_season": True},
    {"name": "banana", "price": 0.5, "in_season": False},
    {"name": "cherry", "price": 3.0, "in_season": True},
]


@pytest.fixture
def seeded_client() -> TestClient:
    app = create_app()
    app.state.store.seed(SEED)
    return TestClient(app)


@pytest.fixture
def empty_client() -> TestClient:
    return TestClient(create_app())


def test_build_fruit_response_returns_expected_shape() -> None:
    created = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    result = build_fruit_response(
        fruit_id=42,
        name="kiwi",
        price=2.5,
        in_season=True,
        created_at=created,
    )
    assert result == {
        "id": 42,
        "name": "kiwi",
        "price": 2.5,
        "in_season": True,
        "created_at": "2025-01-02T03:04:05+00:00",
    }


def test_list_fruits_returns_seeded_rows(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/fruits")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == len(SEED)
    assert sorted(f["name"] for f in body) == sorted(s["name"] for s in SEED)


def test_list_fruits_in_season_true(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/fruits", params={"in_season": "true"})
    assert resp.status_code == 200
    body = resp.json()
    assert {f["name"] for f in body} == {"apple", "cherry"}
    assert all(f["in_season"] is True for f in body)


def test_list_fruits_in_season_false(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/fruits", params={"in_season": "false"})
    assert resp.status_code == 200
    body = resp.json()
    assert {f["name"] for f in body} == {"banana"}
    assert all(f["in_season"] is False for f in body)


def test_cheapest_returns_lowest_priced(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/fruits/cheapest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "banana"
    assert body["price"] == 0.5


def test_cheapest_when_empty_returns_404(empty_client: TestClient) -> None:
    resp = empty_client.get("/fruits/cheapest")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "No fruits available"}


def test_get_unknown_id_returns_404(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/fruits/9999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Fruit not found"}


def test_create_missing_name_returns_422(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/fruits", json={"price": 1.0, "in_season": True})
    assert resp.status_code == 422


def test_create_wrong_type_for_price_returns_422(seeded_client: TestClient) -> None:
    resp = seeded_client.post(
        "/fruits", json={"name": "mango", "price": "not-a-number"}
    )
    assert resp.status_code == 422


def test_create_negative_price_returns_422(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/fruits", json={"name": "mango", "price": -1.0})
    assert resp.status_code == 422


def test_update_unknown_id_returns_404(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/fruits/9999", json={"price": 5.0})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Fruit not found"}


def test_delete_unknown_id_returns_404(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/fruits/9999")
    assert resp.status_code == 404


def test_health_returns_ok(empty_client: TestClient) -> None:
    resp = empty_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
