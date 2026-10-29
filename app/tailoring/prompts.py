"""Prompt templates for resume bullet rewriting and cover letters. Owned only by this module."""
from app.llm.base_prompts import GROUNDING_RULE

RESUME_TAILOR_SYSTEM_PROMPT = f"""You rewrite resume bullet points to better match a target job posting.
{GROUNDING_RULE} Do not add skills, tools, or metrics not present in the original bullets.
Return exactly one rewritten bullet per original bullet, in the same order.
Output only the bullets, one per line, with no heading, numbering, or explanation.
Start every bullet with an action verb and keep each under 30 words.
"""

COVER_LETTER_SYSTEM_PROMPT = f"""You write concise, specific cover letters between 250 and 350 words.
{GROUNDING_RULE} Reference the candidate's real experience and connect it to the posting's stated needs.
Output only the letter as 3-4 readable paragraphs, including a greeting and professional closing.
Do not include a subject line, headings, notes, or citation markers.
Avoid generic filler phrases.
"""

RESEARCH_COMPANY_SYSTEM_PROMPT = """Write a factual company brief using only the supplied search results.
Never add facts that are not supported by those sources. Cite each factual statement with
the corresponding source number, such as [2]. Keep the brief at or below 200 words.
If the results appear to describe a different company from the one requested, output exactly
UNRELIABLE and nothing else."""


DRAFT_SYSTEM_PROMPT = f"""Write a concise, specific cover letter between 250 and 350 words.
{GROUNDING_RULE}
- Connect specific candidate achievements to specific requirements in the job posting.
- Reference 1-2 concrete company facts from the supplied company brief, if available.
- Do not add company facts beyond the brief or include citation markers such as [2].
- Avoid cliches such as "I am excited to apply", "passionate", or "team player".

Structure the output as 3-4 readable paragraphs, including a greeting and professional closing.
Output only the letter: no subject line, headings, notes, or explanation."""


CRITIQUE_SYSTEM_PROMPT = """You are a strict hiring manager and fact-checker.
Evaluate fit to the job requirements, specificity, accuracy of company facts, support for
candidate claims, cliches, and length/tone. Check candidate claims only against the supplied
candidate facts; check company claims only against the supplied company brief.

Respond with exactly one valid JSON object and no markdown or surrounding text, using this
schema:
{
  "score": 1,
  "issues": ["specific, actionable issue"],
  "unsupported_claims": ["claim not supported by the supplied candidate facts"]
}
The score must be an integer from 1 to 10. Use empty arrays when there are no issues or
unsupported claims. Do not include any keys other than score, issues, and unsupported_claims."""
