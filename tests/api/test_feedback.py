from __future__ import annotations


def test_submit_and_read_feedback(client, auth_headers):
    payload = {"request_id": "test-req-1", "thumb": "up", "reason": "clear answer"}
    r = client.post("/feedback", json=payload, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["thumb"] == "up"
    assert body["request_id"] == "test-req-1"
    assert body["reason"] == "clear answer"
    assert body["id"] > 0


def test_feedback_requires_auth(client):
    payload = {"request_id": "test-req-2", "thumb": "down", "reason": ""}
    r = client.post("/feedback", json=payload)
    assert r.status_code == 401


def test_feedback_rejects_bad_thumb(client, auth_headers):
    payload = {"request_id": "test-req-3", "thumb": "sideways", "reason": ""}
    r = client.post("/feedback", json=payload, headers=auth_headers)
    assert r.status_code == 422