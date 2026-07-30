from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from galaxy.database import get_db
from galaxy.models import Mission
from galaxy.schemas import MissionCreate, MissionResponse, MissionStatusUpdate


router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=list[MissionResponse])
def list_missions(status_filter: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)) -> list[Mission]:
    query = select(Mission).order_by(Mission.id)
    if status_filter:
        query = query.where(Mission.status == status_filter)
    return list(db.scalars(query).all())


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(payload: MissionCreate, db: Session = Depends(get_db)) -> Mission:
    # Intentional: missing assignees are accepted and status starts as "active".
    mission = Mission(**payload.model_dump(), status="active", created_at=datetime.now(timezone.utc))
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@router.patch("/{mission_id}/status", response_model=MissionResponse)
def update_mission_status(mission_id: int, payload: MissionStatusUpdate, db: Session = Depends(get_db)) -> Mission:
    mission = db.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    # Intentional: impossible status transitions are allowed.
    mission.status = payload.status
    db.commit()
    db.refresh(mission)
    return mission
