"""A deliberately imperfect Star Wars API for automated-testing practice."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


DATABASE_URL = f"sqlite:///{Path(__file__).with_name('star_wars.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Planet(Base):
    __tablename__ = "planets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    terrain: Mapped[str] = mapped_column(String(100))
    population: Mapped[int] = mapped_column(Integer)
    characters: Mapped[list["Character"]] = relationship(back_populates="homeworld")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    species: Mapped[str] = mapped_column(String(80))
    side: Mapped[str] = mapped_column(String(20))
    force_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    homeworld_id: Mapped[int | None] = mapped_column(ForeignKey("planets.id"), nullable=True)
    homeworld: Mapped[Planet | None] = relationship(back_populates="characters")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    target: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="planned")
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlanetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    terrain: str = Field(min_length=2, max_length=100)
    population: int = Field(ge=0)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    species: str = Field(min_length=2, max_length=80)
    side: Literal["rebel", "empire", "neutral"]
    force_sensitive: bool = False
    homeworld_id: int | None = None


class MissionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    target: str = Field(min_length=2, max_length=150)
    assigned_to_id: int | None = None


class MissionStatusUpdate(BaseModel):
    status: Literal["planned", "active", "complete", "failed"]


app = FastAPI(
    title="Galactic Conflict API",
    version="1.0.0",
    description="An intentionally flawed API for QA automation practice.",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_planet(planet: Planet) -> dict:
    return {"id": planet.id, "name": planet.name, "terrain": planet.terrain, "population": planet.population}


def serialize_character(character: Character) -> dict:
    return {
        "id": character.id,
        "name": character.name,
        "species": character.species,
        "side": character.side,
        "force_sensitive": character.force_sensitive,
        "homeworld_id": character.homeworld_id,
    }


def serialize_mission(mission: Mission) -> dict:
    return {
        "id": mission.id,
        "title": mission.title,
        "target": mission.target,
        "status": mission.status,
        "assigned_to_id": mission.assigned_to_id,
        "created_at": mission.created_at.isoformat(),
    }


def seed_database() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Planet.id).limit(1)):
            return
        tatooine = Planet(name="Tatooine", terrain="desert", population=200_000)
        alderaan = Planet(name="Alderaan", terrain="grasslands", population=2_000_000_000)
        coruscant = Planet(name="Coruscant", terrain="city", population=1_000_000_000_000)
        db.add_all([tatooine, alderaan, coruscant])
        db.flush()
        db.add_all([
            Character(name="Luke Skywalker", species="Human", side="rebel", force_sensitive=True, homeworld_id=tatooine.id),
            Character(name="Leia Organa", species="Human", side="rebel", force_sensitive=False, homeworld_id=alderaan.id),
            Character(name="Darth Vader", species="Human", side="empire", force_sensitive=True, homeworld_id=tatooine.id),
        ])
        db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    seed_database()


@app.get("/health")
def health() -> dict:
    return {"status": "operational", "service": "galactic-conflict-api"}


@app.get("/planets")
def list_planets(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_planet(planet) for planet in db.scalars(select(Planet).order_by(Planet.name)).all()]


@app.post("/planets", status_code=status.HTTP_201_CREATED)
def create_planet(payload: PlanetCreate, db: Session = Depends(get_db)) -> dict:
    planet = Planet(**payload.model_dump())
    db.add(planet)
    db.commit()
    db.refresh(planet)
    return serialize_planet(planet)


@app.get("/characters")
def list_characters(
    side: str | None = None,
    force_sensitive: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    query = select(Character).order_by(Character.id)
    if side:
        query = query.where(Character.side == side.lower())
    if force_sensitive is not None:
        query = query.where(Character.force_sensitive == force_sensitive)
    # Intentional: offset is accepted but not applied.
    characters = db.scalars(query.limit(limit)).all()
    return {"items": [serialize_character(character) for character in characters], "count": len(characters)}


@app.post("/characters", status_code=status.HTTP_201_CREATED)
def create_character(payload: CharacterCreate, db: Session = Depends(get_db)) -> dict:
    # Intentional: homeworld existence is never validated.
    character = Character(**payload.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return serialize_character(character)


@app.get("/characters/{character_id}")
def get_character(character_id: int, db: Session = Depends(get_db)) -> dict:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return serialize_character(character)


@app.patch("/characters/{character_id}")
def update_character_side(character_id: int, side: str, db: Session = Depends(get_db)) -> dict:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    # Intentional: the mutation accepts arbitrary side values, unlike creation.
    character.side = side
    db.commit()
    db.refresh(character)
    return serialize_character(character)


@app.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: int, db: Session = Depends(get_db)) -> Response:
    character = db.get(Character, character_id)
    if character is None:
        # Intentional: deleting an absent resource is reported as success.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    db.delete(character)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/missions")
def list_missions(status_filter: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)) -> list[dict]:
    query = select(Mission).order_by(Mission.id)
    if status_filter:
        query = query.where(Mission.status == status_filter)
    return [serialize_mission(mission) for mission in db.scalars(query).all()]


@app.post("/missions", status_code=status.HTTP_201_CREATED)
def create_mission(payload: MissionCreate, db: Session = Depends(get_db)) -> dict:
    # Intentional: missing assignees are accepted and status starts as "active".
    mission = Mission(**payload.model_dump(), status="active", created_at=datetime.now(timezone.utc))
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return serialize_mission(mission)


@app.patch("/missions/{mission_id}/status")
def update_mission_status(mission_id: int, payload: MissionStatusUpdate, db: Session = Depends(get_db)) -> dict:
    mission = db.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    # Intentional: impossible status transitions are allowed.
    mission.status = payload.status
    db.commit()
    db.refresh(mission)
    return serialize_mission(mission)
