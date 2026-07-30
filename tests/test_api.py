"""HTTP integration tests for the Galactic Conflict API.

The `known_bug` tests intentionally preserve the broken behaviour documented in
INTENTIONAL_BUGS.md. When a bug is fixed, update or remove its corresponding
test and the catalogue entry.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Serve every request against a fresh, shared in-memory SQLite database."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", test_session_factory)

    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client

    main.Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def test_health_endpoint_reports_operational_service(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "operational", "service": "galactic-conflict-api"}


def test_seeded_characters_can_be_filtered(client: TestClient):
    response = client.get("/characters", params={"side": "rebel", "force_sensitive": "true"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["name"] == "Luke Skywalker"


def test_character_creation_and_lookup_work(client: TestClient):
    created = client.post(
        "/characters",
        json={"name": "Chewbacca", "species": "Wookiee", "side": "rebel", "homeworld_id": 1},
    )

    assert created.status_code == 201
    fetched = client.get(f"/characters/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Chewbacca"


def test_known_bug_character_offset_is_ignored(client: TestClient):
    first_page = client.get("/characters", params={"limit": 2, "offset": 0})
    alleged_second_page = client.get("/characters", params={"limit": 2, "offset": 1})

    assert first_page.status_code == 200
    assert alleged_second_page.status_code == 200
    assert alleged_second_page.json()["items"] == first_page.json()["items"]


def test_known_bug_character_accepts_unknown_homeworld(client: TestClient):
    response = client.post(
        "/characters",
        json={"name": "Lost Pilot", "species": "Human", "side": "neutral", "homeworld_id": 999_999},
    )

    assert response.status_code == 201
    assert response.json()["homeworld_id"] == 999_999


def test_known_bug_character_patch_accepts_undocumented_side(client: TestClient):
    response = client.patch("/characters/1", params={"side": "sith"})

    assert response.status_code == 200
    assert response.json()["side"] == "sith"


def test_known_bug_duplicate_planet_is_a_server_error(client: TestClient):
    payload = {"name": "Naboo", "terrain": "swamp", "population": 4_500_000_000}

    assert client.post("/planets", json=payload).status_code == 201
    duplicate = client.post("/planets", json=payload)
    assert duplicate.status_code == 500


def test_known_bug_deleting_missing_character_reports_success(client: TestClient):
    response = client.delete("/characters/999_999")

    assert response.status_code == 204
    assert response.content == b""


def test_known_bug_new_mission_starts_active(client: TestClient):
    response = client.post(
        "/missions",
        json={"title": "Steal the plans", "target": "Scarif", "assigned_to_id": 999_999},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert response.json()["assigned_to_id"] == 999_999


def test_known_bug_mission_can_jump_from_complete_back_to_active(client: TestClient):
    created = client.post("/missions", json={"title": "Disable shield", "target": "Endor"})
    mission_id = created.json()["id"]

    assert client.patch(f"/missions/{mission_id}/status", json={"status": "complete"}).status_code == 200
    reopened = client.patch(f"/missions/{mission_id}/status", json={"status": "active"})
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "active"
