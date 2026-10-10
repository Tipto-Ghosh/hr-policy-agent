from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hr_agent.api.app import create_app


@pytest.fixture(scope="session")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    r = client.post("/auth/login", json={"username": "tipto", "password": "demo"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}