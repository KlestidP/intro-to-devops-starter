"""Spawns uvicorn locally unless BASE_URL is set (then hits that server)."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from typing import Iterator

import httpx
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_health(base_url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/health", timeout=1.0)
            if r.status_code == 200:
                return
        except Exception as exc:
            last_err = exc
        time.sleep(0.2)
    raise RuntimeError(f"Server did not become healthy in time: {last_err}")


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    env_url = os.environ.get("BASE_URL")
    if env_url:
        yield env_url.rstrip("/")
        return

    port = _free_port()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        url = f"http://127.0.0.1:{port}"
        _wait_for_health(url)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def client(base_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=5.0) as c:
        yield c


def test_health_returns_ok(client: httpx.Client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_crud_lifecycle(client: httpx.Client) -> None:
    create = client.post(
        "/fruits",
        json={"name": "lifecycle-grape", "price": 1.25, "in_season": True},
    )
    assert create.status_code == 201
    created = create.json()
    fruit_id = created["id"]
    assert created["name"] == "lifecycle-grape"
    assert created["price"] == 1.25
    assert created["in_season"] is True

    read = client.get(f"/fruits/{fruit_id}")
    assert read.status_code == 200
    assert read.json()["id"] == fruit_id

    update = client.put(f"/fruits/{fruit_id}", json={"price": 1.99})
    assert update.status_code == 200
    updated = update.json()
    assert updated["price"] == 1.99
    assert updated["name"] == "lifecycle-grape"

    delete = client.delete(f"/fruits/{fruit_id}")
    assert delete.status_code == 204

    gone = client.get(f"/fruits/{fruit_id}")
    assert gone.status_code == 404


def test_cheapest_matches_min_price_in_list(client: httpx.Client) -> None:
    a = client.post("/fruits", json={"name": "cheapest-a", "price": 0.99}).json()
    b = client.post("/fruits", json={"name": "cheapest-b", "price": 4.50}).json()
    try:
        listing = client.get("/fruits").json()
        assert listing
        min_price = min(f["price"] for f in listing)

        cheapest = client.get("/fruits/cheapest").json()
        assert cheapest["price"] == min_price
    finally:
        client.delete(f"/fruits/{a['id']}")
        client.delete(f"/fruits/{b['id']}")


def test_created_fruit_appears_in_list(client: httpx.Client) -> None:
    created = client.post(
        "/fruits", json={"name": "appear-mango", "price": 2.0}
    ).json()
    try:
        listing = client.get("/fruits").json()
        assert any(f["id"] == created["id"] for f in listing)
    finally:
        client.delete(f"/fruits/{created['id']}")


def test_post_empty_body_returns_422(client: httpx.Client) -> None:
    resp = client.post("/fruits", json={})
    assert resp.status_code == 422


def test_post_wrong_content_type_returns_error(client: httpx.Client) -> None:
    resp = client.post(
        "/fruits",
        content=b"name=banana&price=1",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code in (415, 422)
