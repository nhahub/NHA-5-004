"""CRUD for application tracking. Plain DB logic, no AI. Reminder logic lives in reminders.py."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate


def create_application(db: Session, user_id: int, payload: ApplicationCreate) -> Application:
    application = Application(user_id=user_id, **payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_application(db: Session, user_id: int, application_id: int) -> Optional[Application]:
    return db.query(Application).filter(
        Application.id == application_id, Application.user_id == user_id
    ).first()


def list_applications(db: Session, user_id: int, status: Optional[str] = None) -> list[Application]:
    query = db.query(Application).filter(Application.user_id == user_id)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.last_updated.desc()).all()


def update_application(
    db: Session, user_id: int, application_id: int, payload: ApplicationUpdate
) -> Optional[Application]:
    application = get_application(db, user_id, application_id)
    if application is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def delete_application(db: Session, user_id: int, application_id: int) -> bool:
    application = get_application(db, user_id, application_id)
    if application is None:
        return False
    db.delete(application)
    db.commit()
    return True