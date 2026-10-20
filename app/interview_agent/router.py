"""HTTP endpoints for the interview-prep agent ONLY. All decision logic lives in state.py."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.schemas.interview import StartPlanRequest, AnswerSubmission, ScoredFeedback
from app.models.practice_session import PracticeSession
from app.interview_agent import state as agent_state

router = APIRouter()


@router.post("/start")
def start(payload: StartPlanRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = agent_state.start_session(db, user.id, payload.target_role, payload.days)
    return {"session_id": session.id, "plan": session.plan_json}


@router.get("/{session_id}/next-question")
def next_question(session_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id, PracticeSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"question": agent_state.get_next_question(db, session)}


@router.get("/{session_id}/resources")
def resources(session_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id, PracticeSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return agent_state.get_current_topic_resources(session)


@router.post("/answer", response_model=ScoredFeedback)
def answer(payload: AnswerSubmission, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == payload.session_id, PracticeSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = agent_state.submit_answer(db, session, payload.day_number, payload.question, payload.user_answer)
    return ScoredFeedback(**result)
