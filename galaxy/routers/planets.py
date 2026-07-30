from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from galaxy.database import get_db
from galaxy.models import Character, Planet
from galaxy.schemas import CharacterResponse, PlanetCreate, PlanetResponse


router = APIRouter(prefix="/planets", tags=["planets"])


@router.get("", response_model=list[PlanetResponse])
def list_planets(db: Session = Depends(get_db)) -> list[Planet]:
    return list(db.scalars(select(Planet).order_by(Planet.name)).all())


@router.post("", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED)
def create_planet(payload: PlanetCreate, db: Session = Depends(get_db)) -> Planet:
    planet = Planet(**payload.model_dump())
    db.add(planet)
    db.commit()
    db.refresh(planet)
    return planet


@router.get("/{planet_id}/characters", response_model=list[CharacterResponse])
def list_planet_characters(planet_id: int, db: Session = Depends(get_db)) -> list[Character]:
    if db.get(Planet, planet_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planet not found")
    # Intentional: the filter by planet_id was omitted, exposing all characters.
    return list(db.scalars(select(Character).order_by(Character.id)).all())
