import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base

from app.models.user import User
from app.models.profile import Profile
from app.models.skill_gap import SkillGapReport
from app.models.practice_session import PracticeSession, PracticeAnswer

import app.interview_agent.planner as planner

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


def test_planner_receives_persistent_memory(db, monkeypatch):
    # ---------------------------------------------------------
    # Create user + profile
    # ---------------------------------------------------------

    user = User(
        email="planner@test.com",
        hashed_password="fake_hash",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(
        user_id=user.id,
        full_name="Test Candidate",
        headline="AI Engineer",
        summary="AI developer with Python experience.",
        location="Cairo",
    )

    db.add(profile)
    db.commit()

    # ---------------------------------------------------------
    # Create repeated historical skill gaps
    # ---------------------------------------------------------

    db.add_all(
        [
            SkillGapReport(
                user_id=user.id,
                job_title="AI Engineer",
                missing_skills=json.dumps(["Docker", "AWS"]),
                matched_skills=json.dumps(["Python"]),
            ),
            SkillGapReport(
                user_id=user.id,
                job_title="AI Engineer",
                missing_skills=json.dumps(["Docker"]),
                matched_skills=json.dumps(["Python"]),
            ),
        ]
    )

    # ---------------------------------------------------------
    # Create previous weak interview performance
    # ---------------------------------------------------------

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
            question="Explain Docker containers.",
            user_answer="They run applications.",
            score=4.0,
            feedback=("Explain isolation, images, and containers " "in more detail."),
        )
    )

    db.commit()

    # ---------------------------------------------------------
    # Mock external RAG
    # ---------------------------------------------------------

    monkeypatch.setattr(
        planner,
        "retrieve_relevant_chunks",
        lambda query, top_k=3: [
            "Study Docker fundamentals.",
            "Review container isolation.",
        ],
    )

    # ---------------------------------------------------------
    # Capture what is actually sent to the LLM
    # ---------------------------------------------------------

    captured = {}

    def fake_complete(system_prompt, user_prompt):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt

        return json.dumps(
            {
                "days": [
                    {
                        "day_number": 1,
                        "topic": "Docker",
                        "focus_areas": [
                            "Containers",
                            "Images",
                            "Isolation",
                        ],
                    }
                ]
            }
        )

    monkeypatch.setattr(
        planner,
        "complete",
        fake_complete,
    )

    # ---------------------------------------------------------
    # Build personalized plan
    # ---------------------------------------------------------

    result = planner.build_plan(
        db=db,
        user_id=user.id,
        target_role="AI Engineer",
        days=3,
    )

    prompt = captured["user_prompt"]

    # ---------------------------------------------------------
    # Prove memory reached the AI planner
    # ---------------------------------------------------------

    assert "Test Candidate" in prompt

    assert "Docker (2 occurrence(s))" in prompt

    assert "Average score: 4.0/10" in prompt

    assert "Explain Docker containers." in prompt

    assert ("Explain isolation, images, and containers " "in more detail.") in prompt

    assert "AI Engineer" in prompt

    # Prove RAG context also reached the planner
    assert "Study Docker fundamentals." in prompt

    # Prove planner successfully parsed LLM response
    assert result["days"][0]["topic"] == "Docker"
