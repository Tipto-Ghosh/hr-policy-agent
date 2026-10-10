from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from hr_agent.api.config import get_api_settings


def test_login_success(client):
    r = client.post("/auth/login", json={"username": "tipto", "password": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user_id"] == "tipto"


def test_login_bad_password(client):
    r = client.post("/auth/login", json={"username": "tipto", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "demo"})
    assert r.status_code == 401


def test_protected_route_without_token(client):
    r = client.get("/memory")
    assert r.status_code == 401


def test_protected_route_with_expired_token(client):
    settings = get_api_settings()
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = jwt.encode(
        {
            "sub": "tipto",
            "iat": int((past - timedelta(minutes=10)).timestamp()),
            "exp": int(past.timestamp()),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    r = client.get("/memory", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_protected_route_with_valid_token(client, auth_headers):
    r = client.get("/memory", headers=auth_headers)
    assert r.status_code == 200