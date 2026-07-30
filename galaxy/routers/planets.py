from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from galaxy.database import get_db
from galaxy.models import Planet
from galaxy.schemas import PlanetCreate, PlanetResponse


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
