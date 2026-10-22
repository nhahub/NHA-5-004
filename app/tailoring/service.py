"""
Orchestrates Phase 4b: pulls profile from Memory, calls resume_tailor.py and
cover_letter.py, saves results onto the relevant Application row.
"""
from sqlalchemy.orm import Session

from app.memory.memory_store import get_user_memory
from app.models.application import Application
from app.tailoring.resume_tailor import tailor_bullets
from app.tailoring.cover_letter import generate_cover_letter_with_critique


def tailor_application(db: Session, user_id: int, application_id: int, job_description: str) -> Application:
    memory = get_user_memory(db, user_id)
    application = db.query(Application).filter(
        Application.id == application_id, Application.user_id == user_id
    ).first()

    all_bullets = [
        line.strip()
        for exp in memory.profile.experiences
        for line in (exp.description or "").splitlines() if line.strip()
    ]
    tailored = tailor_bullets(all_bullets, job_description)

    cover_letter, company_brief = generate_cover_letter_with_critique(
        memory.profile.summary or "",
        application.job_title,
        application.company,
        job_description,
        tailored,  # ground the letter in the tailored bullets
    )
    application.cover_letter_text = cover_letter
    # tailored bullets would typically render into a new resume file via docx skill / template
    db.commit()
    db.refresh(application)
    return application
