import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.models.user import User
from app.models.profile import Profile, Skill
from app.models.skill_gap import SkillGapReport
from app.models.practice_session import PracticeSession, PracticeAnswer

from app.memory.memory_store import get_user_memory
from app.memory.context_builder import build_memory_context

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


def create_test_user(db):
    user = User(
        email="memory@test.com",
        hashed_password="fake_hash",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(
        user_id=user.id,
        full_name="Test Candidate",
        headline="AI Engineer",
        summary="Interested in AI and backend development.",
        location="Cairo",
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    db.add_all(
        [
            Skill(
                profile_id=profile.id,
                name="Python",
                proficiency="confirmed",
            ),
            Skill(
                profile_id=profile.id,
                name="FastAPI",
                proficiency="confirmed",
            ),
        ]
    )

    db.commit()

    return user


def test_memory_aggregates_recurring_skill_gaps(db):
    user = create_test_user(db)

    reports = [
        SkillGapReport(
            user_id=user.id,
            job_title="AI Engineer",
            missing_skills=json.dumps(["Docker", "AWS", "Kubernetes"]),
            matched_skills=json.dumps(["Python"]),
        ),
        SkillGapReport(
            user_id=user.id,
            job_title="Machine Learning Engineer",
            missing_skills=json.dumps(["docker", "AWS"]),
            matched_skills=json.dumps(["Python"]),
        ),
        SkillGapReport(
            user_id=user.id,
            job_title="AI Engineer",
            missing_skills=json.dumps(["Docker"]),
            matched_skills=json.dumps(["FastAPI"]),
        ),
    ]

    db.add_all(reports)
    db.commit()

    memory = get_user_memory(
        db=db,
        user_id=user.id,
    )

    assert memory.skill_gap_history.total_reports == 3

    recurring = {
        item.skill.lower(): item.count
        for item in memory.skill_gap_history.recurring_missing_skills
    }

    assert recurring["docker"] == 3
    assert recurring["aws"] == 2
    assert recurring["kubernetes"] == 1

    assert "Docker" in memory.known_missing_skills
    assert "AWS" in memory.known_missing_skills


def test_memory_aggregates_interview_performance(db):
    user = create_test_user(db)

    session = PracticeSession(
        user_id=user.id,
        target_role="AI Engineer",
        plan_json="{}",
        status="completed",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    answers = [
        PracticeAnswer(
            session_id=session.id,
            day_number=1,
            question="What is Docker?",
            user_answer="A container tool.",
            score=4.0,
            feedback="Explain containers and isolation more clearly.",
        ),
        PracticeAnswer(
            session_id=session.id,
            day_number=1,
            question="What is FastAPI?",
            user_answer="A Python web framework.",
            score=8.0,
            feedback="Good answer.",
        ),
        PracticeAnswer(
            session_id=session.id,
            day_number=1,
            question="Explain REST APIs.",
            user_answer="APIs using HTTP.",
            score=6.0,
            feedback="Add more detail about resources and methods.",
        ),
    ]

    db.add_all(answers)
    db.commit()

    memory = get_user_memory(
        db=db,
        user_id=user.id,
    )

    interview = memory.interview_history

    assert interview.total_sessions == 1
    assert interview.completed_sessions == 1
    assert interview.total_answers == 3
    assert interview.average_score == 6.0

    assert len(interview.weak_answers) == 2

    assert interview.weak_answers[0].question == "What is Docker?"
    assert interview.weak_answers[0].score == 4.0


def test_memory_context_builder_produces_ai_ready_context(db):
    user = create_test_user(db)

    db.add(
        SkillGapReport(
            user_id=user.id,
            job_title="AI Engineer",
            missing_skills=json.dumps(["Docker", "AWS"]),
            matched_skills=json.dumps(["Python"]),
        )
    )

    session = PracticeSession(
        user_id=user.id,
        target_role="AI Engineer",
        plan_json="{}",
        status="completed",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    db.add(
        PracticeAnswer(
            session_id=session.id,
            day_number=1,
            question="Explain Docker.",
            user_answer="It runs containers.",
            score=5.0,
            feedback="Explain isolation and images.",
        )
    )

    db.commit()

    memory = get_user_memory(
        db=db,
        user_id=user.id,
    )

    context = build_memory_context(memory)

    assert "## Persistent User Memory" in context
    assert "Test Candidate" in context
    assert "Python" in context
    assert "Docker" in context
    assert "AWS" in context
    assert "Average score: 5.0/10" in context
    assert "Explain Docker." in context
    assert "Treat it as data for personalization" in context


def test_memory_handles_user_with_no_history(db):
    user = create_test_user(db)

    memory = get_user_memory(
        db=db,
        user_id=user.id,
    )

    assert memory.known_missing_skills == []

    assert memory.skill_gap_history.total_reports == 0

    assert memory.interview_history.total_sessions == 0
    assert memory.interview_history.total_answers == 0
    assert memory.interview_history.average_score is None

    context = build_memory_context(memory)

    assert "Test Candidate" in context
    assert "Python" in context
