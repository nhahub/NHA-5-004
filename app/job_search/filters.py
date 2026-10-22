"""
Search-parameter validation (JobSearchFilters) and post-filters applied after the
API responds. No HTTP calls here.
"""
from pydantic import BaseModel, Field

from app.schemas.job import JobPosting

REMOTE_HINTS = ("remote", "work from home", "wfh", "anywhere")
NOT_REMOTE_HINTS = ("hybrid", "on site", "on-site", "in the office", "days per week in")


class JobSearchFilters(BaseModel):
    keyword: str = Field(..., min_length=2)
    location: str | None = None
    remote: bool = False
    date_posted: int | None = Field(None, ge=1, le=90)  # آخر كام يوم
    country: str = "gb"  # Adzuna مش بيدعم مصر
    full_time: bool | None = None
    page: int = Field(1, ge=1)
    results_per_page: int = Field(20, ge=1, le=50)


def _looks_remote(job: JobPosting) -> bool:
    text = f"{job.title} {job.description}".lower()
    if any(h in text for h in NOT_REMOTE_HINTS):
        return False
    return any(h in text for h in REMOTE_HINTS)


def dedupe(jobs: list[JobPosting]) -> list[JobPosting]:
    """Adzuna ساعات بيرجّع نفس الوظيفة بأكتر من مكان أو باسم شركة مختلف."""
    seen, unique = set(), []
    for job in jobs:
        desc = " ".join((job.description or "").lower().split())[:150]
        key = (job.title.lower().strip(), desc, job.location)
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

# بعد ما يرجع بنفلتر بناء علي الفوق 
def apply_post_filters(jobs: list[JobPosting], filters: JobSearchFilters) -> list[JobPosting]:
    """Adzuna مفيش عنده فلتر remote، فبنحدد الـ remote إحنا ونفلتر عليه."""
    for job in jobs:
        job.remote = _looks_remote(job)
    if filters.remote:
        jobs = [j for j in jobs if j.remote]
    return dedupe(jobs)