"""HTTP request and response shapes exposed in OpenAPI."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlanetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    terrain: str = Field(min_length=2, max_length=100)
    population: int = Field(ge=0)


class PlanetResponse(PlanetCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    species: str = Field(min_length=2, max_length=80)
    side: Literal["rebel", "empire", "neutral"]
    force_sensitive: bool = False
    homeworld_id: int | None = None


class CharacterResponse(BaseModel):
    id: int
    name: str
    species: str
    # Deliberately broader than CharacterCreate to expose the patch validation bug.
    side: str
    force_sensitive: bool
    homeworld_id: int | None
    model_config = ConfigDict(from_attributes=True)


class MissionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    target: str = Field(min_length=2, max_length=150)
    assigned_to_id: int | None = None


class MissionStatusUpdate(BaseModel):
    status: Literal["planned", "active", "complete", "failed"]


class MissionResponse(MissionCreate):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StarshipCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    model: str = Field(min_length=2, max_length=120)
    manufacturer: str = Field(min_length=2, max_length=120)
    crew: int = Field(ge=0)
    fuel_level: int = Field(default=100, ge=0, le=100)
    hyperdrive_rating: float = Field(gt=0)


class StarshipResponse(BaseModel):
    id: int
    name: str
    model: str
    manufacturer: str
    crew: int
    # Deliberately unconstrained to expose the fuel-update validation bug.
    fuel_level: int
    hyperdrive_rating: float
    model_config = ConfigDict(from_attributes=True)
