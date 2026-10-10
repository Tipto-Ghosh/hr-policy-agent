from __future__ import annotations

import hashlib

from hr_agent.memory.store import get_store, preference_namespace


def _ns(user_id: str):
    return preference_namespace(hashlib.sha256(user_id.encode()).hexdigest())


def test_list_and_delete_memory(client, auth_headers):
    store = get_store()
    ns = _ns("tipto")
    store.put(ns, key="verbosity", value={"value": "concise"})

    r = client.get("/memory", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    keys = {it["key"] for it in body["items"]}
    assert "verbosity" in keys

    r = client.delete("/memory/verbosity", headers=auth_headers)
    assert r.status_code == 200

    r = client.get("/memory", headers=auth_headers)
    keys = {it["key"] for it in r.json()["items"]}
    assert "verbosity" not in keys


def test_memory_is_user_scoped(client):
    alice = client.post("/auth/login", json={"username": "alice", "password": "demo"}).json()["access_token"]
    bob = client.post("/auth/login", json={"username": "bob", "password": "demo"}).json()["access_token"]

    store = get_store()
    store.put(_ns("alice"), key="language", value={"value": "en"})

    r_alice = client.get("/memory", headers={"Authorization": f"Bearer {alice}"})
    r_bob = client.get("/memory", headers={"Authorization": f"Bearer {bob}"})

    alice_keys = {it["key"] for it in r_alice.json()["items"]}
    bob_keys = {it["key"] for it in r_bob.json()["items"]}
    assert "language" in alice_keys
    assert "language" not in bob_keys