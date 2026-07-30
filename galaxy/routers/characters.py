from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from galaxy.database import get_db
from galaxy.models import Character
from galaxy.schemas import CharacterCreate, CharacterResponse


router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
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
    return {"items": [CharacterResponse.model_validate(character).model_dump() for character in characters], "count": len(characters)}


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(payload: CharacterCreate, db: Session = Depends(get_db)) -> Character:
    # Intentional: homeworld existence is never validated.
    character = Character(**payload.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)) -> Character:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return character


@router.patch("/{character_id}", response_model=CharacterResponse)
def update_character_side(character_id: int, side: str, db: Session = Depends(get_db)) -> Character:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    # Intentional: the mutation accepts arbitrary side values, unlike creation.
    character.side = side
    db.commit()
    db.refresh(character)
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: int, db: Session = Depends(get_db)) -> Response:
    character = db.get(Character, character_id)
    if character is None:
        # Intentional: deleting an absent resource is reported as success.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    db.delete(character)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
