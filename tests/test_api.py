"""HTTP integration tests for the Galactic Conflict API.

The defect tests express the intended public contract. They are expected to
fail until the corresponding bug is fixed, making them useful QA regressions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from galaxy import database


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Serve every request against a fresh, shared in-memory SQLite database."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", test_session_factory)

    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client

    database.Base.metadata.drop_all(test_engine)
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


def test_seeded_starships_can_be_listed(client: TestClient):
    response = client.get("/starships")

    assert response.status_code == 200
    assert {ship["name"] for ship in response.json()} >= {"Millennium Falcon", "X-wing"}


def test_starting_an_initialized_database_does_not_duplicate_seeds(client: TestClient):
    initial_starships = client.get("/starships").json()

    main.startup()

    assert client.get("/starships").json() == initial_starships


def test_starship_fuel_rejects_out_of_range_level(client: TestClient):
    response = client.patch("/starships/1/fuel", params={"level": 101})

    assert response.status_code == 422


def test_character_offset_returns_the_requested_page(client: TestClient):
    all_characters = client.get("/characters", params={"limit": 100}).json()["items"]
    second_page = client.get("/characters", params={"limit": 2, "offset": 1})

    assert second_page.status_code == 200
    assert [character["id"] for character in second_page.json()["items"]] == [
        character["id"] for character in all_characters[1:3]
    ]


def test_character_count_reports_all_matching_records(client: TestClient):
    all_characters = client.get("/characters", params={"limit": 100}).json()["items"]
    response = client.get("/characters", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json()["count"] == len(all_characters)


def test_character_rejects_unknown_homeworld(client: TestClient):
    response = client.post(
        "/characters",
        json={"name": "Lost Pilot", "species": "Human", "side": "neutral", "homeworld_id": 999_999},
    )

    assert response.status_code == 404


def test_character_patch_rejects_undocumented_side(client: TestClient):
    response = client.patch("/characters/1", params={"side": "sith"})

    assert response.status_code == 422


def test_duplicate_planet_returns_conflict(client: TestClient):
    payload = {"name": "Kamino", "terrain": "ocean", "population": 1_000_000}

    assert client.post("/planets", json=payload).status_code == 201
    duplicate = client.post("/planets", json=payload)
    assert duplicate.status_code == 409


def test_deleting_missing_character_returns_not_found(client: TestClient):
    response = client.delete("/characters/999_999")

    assert response.status_code == 404


def test_new_mission_starts_planned(client: TestClient):
    response = client.post(
        "/missions",
        json={"title": "Steal the plans", "target": "Scarif", "assigned_to_id": 1},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "planned"


def test_mission_rejects_unknown_assignee(client: TestClient):
    response = client.post(
        "/missions",
        json={"title": "Steal the plans", "target": "Scarif", "assigned_to_id": 999_999},
    )

    assert response.status_code == 404


def test_completed_mission_cannot_be_reopened(client: TestClient):
    created = client.post("/missions", json={"title": "Disable shield", "target": "Endor"})
    mission_id = created.json()["id"]

    assert client.patch(f"/missions/{mission_id}/status", json={"status": "complete"}).status_code == 200
    reopened = client.patch(f"/missions/{mission_id}/status", json={"status": "active"})
    assert reopened.status_code == 409


def test_unknown_mission_status_filter_is_rejected(client: TestClient):
    response = client.get("/missions", params={"status": "archived"})

    assert response.status_code == 422


def test_deleting_mission_removes_the_record(client: TestClient):
    created = client.post("/missions", json={"title": "Guard the reactor", "target": "Endor"})
    mission_id = created.json()["id"]

    assert client.delete(f"/missions/{mission_id}").status_code == 204
    assert client.get(f"/missions/{mission_id}").status_code == 404


def test_planet_residents_only_include_that_planets_characters(client: TestClient):
    response = client.get("/planets/1/characters")

    assert response.status_code == 200
    assert {character["name"] for character in response.json()} == {"Luke Skywalker", "Darth Vader"}


def test_duplicate_starship_returns_conflict(client: TestClient):
    payload = {
        "name": "Slave I",
        "model": "Firespray-31 patrol and attack craft",
        "manufacturer": "Kuat Systems Engineering",
        "crew": 1,
        "fuel_level": 75,
        "hyperdrive_rating": 3.0,
    }

    assert client.post("/starships", json=payload).status_code == 201
    assert client.post("/starships", json=payload).status_code == 409
