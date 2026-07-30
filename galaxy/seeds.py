"""Deterministic data loaded only into a brand-new database."""

from datetime import datetime, timezone

from sqlalchemy import select

from galaxy import database
from galaxy.models import Character, Mission, Planet, SeedState, Starship


def seed_database() -> None:
    """Load demo records exactly once for each newly initialized database."""
    with database.SessionLocal() as db:
        if db.get(SeedState, "initial-seed") is not None:
            return
        # Databases created by API versions before SeedState already contain
        # data. Mark them initialized instead of attempting a duplicate seed.
        if db.scalar(select(Planet.id).limit(1)) is not None:
            db.add(SeedState(key="initial-seed"))
            db.commit()
            return

        planets = [
            Planet(name="Tatooine", terrain="desert", population=200_000),
            Planet(name="Alderaan", terrain="grasslands", population=2_000_000_000),
            Planet(name="Coruscant", terrain="city", population=1_000_000_000_000),
            Planet(name="Naboo", terrain="swamp", population=4_500_000_000),
            Planet(name="Hoth", terrain="tundra", population=0),
        ]
        db.add_all(planets)
        db.flush()
        tatooine, alderaan, coruscant, naboo, hoth = planets
        characters = [
            Character(name="Luke Skywalker", species="Human", side="rebel", force_sensitive=True, homeworld_id=tatooine.id),
            Character(name="Leia Organa", species="Human", side="rebel", force_sensitive=False, homeworld_id=alderaan.id),
            Character(name="Darth Vader", species="Human", side="empire", force_sensitive=True, homeworld_id=tatooine.id),
            Character(name="Han Solo", species="Human", side="rebel", force_sensitive=False, homeworld_id=coruscant.id),
            Character(name="Yoda", species="Unknown", side="neutral", force_sensitive=True, homeworld_id=naboo.id),
            Character(name="Boba Fett", species="Human", side="neutral", force_sensitive=False, homeworld_id=hoth.id),
        ]
        db.add_all(characters)
        db.flush()
        db.add_all([
            Mission(title="Evacuate Echo Base", target="Hoth", status="planned", assigned_to_id=characters[1].id, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)),
            Mission(title="Locate the droids", target="Tatooine", status="active", assigned_to_id=characters[2].id, created_at=datetime(2026, 1, 2, tzinfo=timezone.utc)),
            Starship(name="Millennium Falcon", model="YT-1300 light freighter", manufacturer="Corellian Engineering Corporation", crew=4, fuel_level=82, hyperdrive_rating=0.5),
            Starship(name="X-wing", model="T-65B X-wing starfighter", manufacturer="Incom Corporation", crew=1, fuel_level=100, hyperdrive_rating=1.0),
            Starship(name="Executor", model="Executor-class Star Dreadnought", manufacturer="Kuat Drive Yards", crew=279_144, fuel_level=58, hyperdrive_rating=2.0),
        ])
        db.add(SeedState(key="initial-seed"))
        db.commit()
