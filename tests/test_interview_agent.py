"""
Unit tests for app/interview_agent/: nudge.py decision logic (pure function, no
mocks needed) plus state.py's submit_answer branching and max-attempts guard
(LLM mocked via mock_llm, DB via in-memory SQLite via db_session).
"""
import json

from app.interview_agent.nudge import decide_next_action
from app.interview_agent import state as agent_state
from app.models.user import User
from app.models.practice_session import PracticeSession


def test_advance_on_high_score():
    assert decide_next_action(score=8.0, recent_scores=[7.0]) == "advance"


def test_repeat_on_low_score():
    assert decide_next_action(score=3.0, recent_scores=[6.0]) == "repeat_topic"


def test_nudge_break_on_low_streak():
    assert decide_next_action(score=3.0, recent_scores=[4.0]) == "nudge_break"


def _make_session(db_session, days=2):
    user = User(email="sarah@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    plan = {"days": [
        {"day_number": 1, "topic": "SQL fundamentals", "focus_areas": ["joins"]},
        {"day_number": 2, "topic": "System design", "focus_areas": ["caching"]},
    ][:days]}
    session = PracticeSession(user_id=user.id, target_role="Backend Engineer", plan_json=json.dumps(plan))
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_submit_answer_advances_on_high_score(db_session, mock_llm):
    session = _make_session(db_session)
    mock_llm.return_value = json.dumps({"score": 8.0, "feedback": "Great answer."})

    result = agent_state.submit_answer(db_session, session, 1, "Q?", "A.")

    assert result["next_action"] == "advance"
    assert session.current_day == 2
    assert session.current_day_attempts == 0


def test_submit_answer_repeats_on_single_low_score(db_session, mock_llm):
    # Only one low score so far -> repeat_topic (nudge.py needs 2 in a row to break).
    session = _make_session(db_session)
    mock_llm.return_value = json.dumps({"score": 3.0, "feedback": "Needs work."})

    result = agent_state.submit_answer(db_session, session, 1, "Q?", "A.")

    assert result["next_action"] == "repeat_topic"
    assert session.current_day == 1
    assert session.current_day_attempts == 1


def test_submit_answer_forces_advance_after_max_attempts(db_session, mock_llm):
    # Consecutive low scores trip nudge.py's break threshold after the first repeat,
    # so this exercises the guard capping repeat_topic/nudge_break combined, not
    # a specific single action repeated MAX_ATTEMPTS_PER_DAY times.
    session = _make_session(db_session)
    mock_llm.return_value = json.dumps({"score": 3.0, "feedback": "Needs work."})

    seen_actions = []
    for _ in range(agent_state.MAX_ATTEMPTS_PER_DAY - 1):
        result = agent_state.submit_answer(db_session, session, 1, "Q?", "A.")
        seen_actions.append(result["next_action"])
        assert result["next_action"] in ("repeat_topic", "nudge_break")

    result = agent_state.submit_answer(db_session, session, 1, "Q?", "A.")

    assert result["next_action"] == "advance"
    assert session.current_day == 2
    assert session.current_day_attempts == 0


def test_submit_answer_completes_session_on_last_day(db_session, mock_llm):
    session = _make_session(db_session, days=1)
    mock_llm.return_value = json.dumps({"score": 9.0, "feedback": "Excellent."})

    result = agent_state.submit_answer(db_session, session, 1, "Q?", "A.")

    assert result["next_action"] == "advance"
    assert session.status == "completed"


def test_get_current_topic_resources_returns_rag_results(db_session, monkeypatch):
    from app.career_rag import retriever

    session = _make_session(db_session)
    monkeypatch.setattr(
        retriever, "retrieve_resources",
        lambda topic, top_k=3: [{"excerpt": "some SQL tips", "source_url": "https://example.com"}],
    )

    result = agent_state.get_current_topic_resources(session)

    assert result["topic"] == "SQL fundamentals"
    assert result["resources"] == [{"excerpt": "some SQL tips", "source_url": "https://example.com"}]


def test_get_current_topic_resources_empty_when_rag_has_nothing(db_session, monkeypatch):
    from app.career_rag import retriever

    session = _make_session(db_session)
    monkeypatch.setattr(retriever, "retrieve_resources", lambda topic, top_k=3: [])

    result = agent_state.get_current_topic_resources(session)

    assert result == {"topic": "SQL fundamentals", "resources": []}


def test_get_current_topic_resources_survives_rag_failure(db_session, monkeypatch):
    from app.career_rag import retriever

    session = _make_session(db_session)

    def _boom(topic, top_k=3):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr(retriever, "retrieve_resources", _boom)

    result = agent_state.get_current_topic_resources(session)

    assert result == {"topic": "SQL fundamentals", "resources": []}
