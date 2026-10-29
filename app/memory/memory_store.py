"""
Memory read layer.

This module is the single place that assembles persistent user context
for AI features such as skill-gap analysis, tailoring, and interview prep.
"""

import json
from collections import Counter

from sqlalchemy.orm import Session, selectinload

from app.models.profile import Profile
from app.models.skill_gap import SkillGapReport
from app.models.practice_session import PracticeSession

from app.memory.memory_schemas import (
    InterviewMemory,
    SkillGapFrequency,
    SkillGapMemory,
    UserMemory,
    WeakInterviewAnswer,
)

from app.schemas.profile import ProfileOut

WEAK_SCORE_THRESHOLD = 6.0
MAX_WEAK_ANSWERS = 5
MAX_RECENT_ROLES = 5


def _safe_json_list(value: str | None) -> list[str]:
    """
    Safely decode a JSON-encoded list.

    Invalid or unexpected stored data should not break the whole
    user-memory pipeline.
    """
    if not value:
        return []

    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(decoded, list):
        return []

    return [item.strip() for item in decoded if isinstance(item, str) and item.strip()]


def _unique_recent(values: list[str | None], limit: int) -> list[str]:
    """Return unique non-empty values while preserving their order."""
    result = []
    seen = set()

    for value in values:
        if not value:
            continue

        cleaned = value.strip()

        if not cleaned:
            continue

        key = cleaned.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

        if len(result) >= limit:
            break

    return result


def _build_skill_gap_memory(
    reports: list[SkillGapReport],
) -> tuple[list[str], SkillGapMemory]:
    """
    Aggregate previous skill-gap reports.

    Skills are counted case-insensitively so values such as
    'Docker' and 'docker' are treated as the same skill.
    """
    counts = Counter()
    display_names = {}

    for report in reports:
        for skill in _safe_json_list(report.missing_skills):
            key = skill.casefold()

            counts[key] += 1

            # Reports are newest first, so keep the newest spelling.
            if key not in display_names:
                display_names[key] = skill

    recurring_skills = [
        SkillGapFrequency(
            skill=display_names[key],
            count=count,
        )
        for key, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], display_names[item[0]].lower()),
        )
    ]

    # Preserve the old simple API for existing modules.
    known_missing_skills = sorted(
        (item.skill for item in recurring_skills),
        key=str.lower,
    )

    recent_roles = _unique_recent(
        [report.job_title for report in reports],
        MAX_RECENT_ROLES,
    )

    memory = SkillGapMemory(
        total_reports=len(reports),
        recurring_missing_skills=recurring_skills,
        recent_target_roles=recent_roles,
    )

    return known_missing_skills, memory


def _build_interview_memory(
    sessions: list[PracticeSession],
) -> InterviewMemory:
    """Aggregate interview-practice history into AI-friendly memory."""
    scores = []
    weak_answers = []

    for session in sessions:
        for answer in session.answers:
            if answer.score is not None:
                scores.append(answer.score)

                if answer.score <= WEAK_SCORE_THRESHOLD:
                    weak_answers.append(
                        WeakInterviewAnswer(
                            question=answer.question,
                            score=answer.score,
                            feedback=answer.feedback,
                            target_role=session.target_role,
                        )
                    )

    weak_answers.sort(
        key=lambda answer: (answer.score if answer.score is not None else float("inf"))
    )

    average_score = None

    if scores:
        average_score = round(sum(scores) / len(scores), 2)

    recent_roles = _unique_recent(
        [session.target_role for session in sessions],
        MAX_RECENT_ROLES,
    )

    completed_sessions = sum(
        1 for session in sessions if (session.status or "").lower() == "completed"
    )

    return InterviewMemory(
        total_sessions=len(sessions),
        completed_sessions=completed_sessions,
        total_answers=sum(len(session.answers) for session in sessions),
        average_score=average_score,
        recent_target_roles=recent_roles,
        weak_answers=weak_answers[:MAX_WEAK_ANSWERS],
    )


def _build_practice_summary(
    interview_memory: InterviewMemory,
) -> str | None:
    """Create a short human-readable summary for backward compatibility."""
    if interview_memory.total_sessions == 0:
        return None

    summary = (
        f"{interview_memory.total_sessions} interview-prep session(s), "
        f"{interview_memory.total_answers} answered question(s)"
    )

    if interview_memory.average_score is not None:
        summary += f", average score " f"{interview_memory.average_score}/10"

    return summary


def get_user_memory(
    db: Session,
    user_id: int,
) -> UserMemory:
    """
    Build the user's complete persistent memory.

    Other AI modules should call this function instead of querying
    profile, skill-gap, and interview-history tables separately.
    """

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    reports = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.user_id == user_id)
        .order_by(SkillGapReport.created_at.desc())
        .all()
    )

    sessions = (
        db.query(PracticeSession)
        .options(selectinload(PracticeSession.answers))
        .filter(PracticeSession.user_id == user_id)
        .order_by(PracticeSession.created_at.desc())
        .all()
    )

    known_missing_skills, skill_gap_memory = _build_skill_gap_memory(reports)

    interview_memory = _build_interview_memory(sessions)

    return UserMemory(
        profile=(ProfileOut.model_validate(profile) if profile else ProfileOut()),
        known_missing_skills=known_missing_skills,
        practice_history_summary=_build_practice_summary(interview_memory),
        skill_gap_history=skill_gap_memory,
        interview_history=interview_memory,
    )
