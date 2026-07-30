from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from galaxy.database import get_db
from galaxy.models import Starship
from galaxy.schemas import StarshipCreate, StarshipResponse


router = APIRouter(prefix="/starships", tags=["starships"])


@router.get("", response_model=list[StarshipResponse])
def list_starships(min_crew: int | None = Query(default=None, ge=0), db: Session = Depends(get_db)) -> list[Starship]:
    query = select(Starship).order_by(Starship.id)
    if min_crew is not None:
        query = query.where(Starship.crew >= min_crew)
    return list(db.scalars(query).all())


@router.post("", response_model=StarshipResponse, status_code=status.HTTP_201_CREATED)
def create_starship(payload: StarshipCreate, db: Session = Depends(get_db)) -> Starship:
    starship = Starship(**payload.model_dump())
    db.add(starship)
    db.commit()
    db.refresh(starship)
    return starship


@router.get("/{starship_id}", response_model=StarshipResponse)
def get_starship(starship_id: int, db: Session = Depends(get_db)) -> Starship:
    starship = db.get(Starship, starship_id)
    if starship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Starship not found")
    return starship


@router.patch("/{starship_id}/fuel", response_model=StarshipResponse)
def refuel_starship(starship_id: int, level: int, db: Session = Depends(get_db)) -> Starship:
    starship = db.get(Starship, starship_id)
    if starship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Starship not found")
    # Intentional: direct query input has no 0--100 range validation.
    starship.fuel_level = level
    db.commit()
    db.refresh(starship)
    return starship
