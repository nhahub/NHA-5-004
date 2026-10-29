"""
Builds the initial personalized interview-preparation plan.

The planner combines:
- persistent user memory
- historical skill gaps
- previous interview performance
- relevant career RAG resources

This allows the generated plan to adapt to the individual user instead
of producing generic interview preparation advice.
"""

import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.memory.context_builder import get_user_memory_context
from app.career_rag.retriever import retrieve_relevant_chunks
from app.interview_agent.prompts import PLAN_GENERATION_PROMPT


def build_plan(
    db: Session,
    user_id: int,
    target_role: str,
    days: int,
) -> dict:
    """
    Generate a personalized interview-preparation plan.

    Persistent memory gives the planner historical context, while RAG
    provides relevant external study material.
    """

    memory_context = get_user_memory_context(
        db=db,
        user_id=user_id,
    )

    resource_hints = retrieve_relevant_chunks(
        f"interview prep for {target_role}",
        top_k=3,
    )

    resources_text = (
        "\n---\n".join(resource_hints)
        if resource_hints
        else "No relevant resources found."
    )

    user_prompt = f"""
TARGET ROLE: {target_role}
AVAILABLE DAYS: {days}

{memory_context}

## Relevant Study Resources
{resources_text}

Generate a personalized interview-preparation plan for this candidate.
"""

    raw = complete(
        PLAN_GENERATION_PROMPT,
        user_prompt,
    )

    return json.loads(raw)
