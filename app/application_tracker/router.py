"""HTTP endpoints for the application tracker ONLY."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    Status,
)
from app.application_tracker.service import (
    create_application,
    delete_application,
    list_applications,
    update_application,
)
from app.application_tracker.reminders import find_stale_applications

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create(payload: ApplicationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return create_application(db, user.id, payload)


@router.get("/", response_model=list[ApplicationOut])
def list_all(
    status_filter: Optional[Status] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_applications(db, user.id, status_filter)


@router.get("/stale", response_model=list[ApplicationOut])
def stale(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return find_stale_applications(list_applications(db, user.id))


@router.patch("/{application_id}", response_model=ApplicationOut)
def update(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    application = update_application(db, user.id, application_id, payload)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not delete_application(db, user.id, application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)