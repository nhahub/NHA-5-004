"""Prompt templates for resume bullet rewriting and cover letters. Owned only by this module."""
from app.llm.base_prompts import GROUNDING_RULE

RESUME_TAILOR_SYSTEM_PROMPT = f"""You rewrite resume bullet points to better match a target job posting.
{GROUNDING_RULE} Do not add skills, tools, or metrics not present in the original bullets.
Keep each rewritten bullet under 30 words, action-verb-first.
"""

COVER_LETTER_SYSTEM_PROMPT = f"""You write concise, specific cover letters (under 350 words).
{GROUNDING_RULE} Reference the candidate's real experience and connect it to the posting's stated needs.
Avoid generic filler phrases.
"""

RESEARCH_COMPANY_SYSTEM_PROMPT = f"""-You write factual company briefs from search results only. 
-Never add facts that are not in the sources. If the sources seem to be 
-about a different company than the one named, reply exactly: UNRELIABLE."""


DRAFT_SYSTEM_PROMPT = ("""
    You write concise, specific cover letters (250-350 words). Rules:
    - Only claim experience present in the candidate material. Never invent.
    - Reference 1-2 concrete facts from the company brief if provided; never add 
    company facts that are not in the brief.
    - Connect specific achievements to specific job requirements.
    - Avoid cliches ('I am excited to apply', 'passionate', 'team player').
    - Do not include citation markers like [2] in the letter.
    Output only the letter."
    """
)


CRITIQUE_SYSTEM_PROMPT="You are a strict hiring manager and fact-checker. Respond with a JSON object only."
