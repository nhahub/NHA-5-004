"""
Typed representation of persistent user memory.

Memory is NOT a database table. It is a read-optimized view assembled
from the user's persisted profile, skill-gap history, and interview
practice history.

Other AI features should consume UserMemory instead of querying those
tables individually.
"""

from pydantic import BaseModel, Field

from app.schemas.profile import ProfileOut


class SkillGapFrequency(BaseModel):
    """How often a skill appeared as missing across previous job analyses."""

    skill: str
    count: int


class SkillGapMemory(BaseModel):
    """Aggregated information from the user's previous skill-gap reports."""

    total_reports: int = 0

    recurring_missing_skills: list[SkillGapFrequency] = Field(default_factory=list)

    recent_target_roles: list[str] = Field(default_factory=list)


class WeakInterviewAnswer(BaseModel):
    """A low-scoring interview answer worth remembering for future practice."""

    question: str | None = None
    score: float | None = None
    feedback: str | None = None
    target_role: str | None = None


class InterviewMemory(BaseModel):
    """Aggregated interview-practice history."""

    total_sessions: int = 0
    completed_sessions: int = 0
    total_answers: int = 0

    average_score: float | None = None

    recent_target_roles: list[str] = Field(default_factory=list)

    weak_answers: list[WeakInterviewAnswer] = Field(default_factory=list)


class UserMemory(BaseModel):
    """
    Single memory object consumed by the application's AI features.

    Existing fields are preserved for backward compatibility while richer
    structured memory is exposed through skill_gap_history and
    interview_history.
    """

    profile: ProfileOut

    # Existing API — keep this because interview_agent currently uses it.
    known_missing_skills: list[str] = Field(default_factory=list)

    # Existing human-readable summary.
    practice_history_summary: str | None = None

    # Richer structured memory.
    skill_gap_history: SkillGapMemory = Field(default_factory=SkillGapMemory)

    interview_history: InterviewMemory = Field(default_factory=InterviewMemory)
