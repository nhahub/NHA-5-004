"""
Orchestration only: fetch postings from the API client, then apply post-filters.
No HTTP calls here, no request parsing here.
"""
from app.job_search.filters import JobSearchFilters, apply_post_filters
from app.job_search.job_api_client import fetch_postings
from app.schemas.job import JobPosting


def search_jobs(filters: JobSearchFilters) -> list[JobPosting]:
    postings = fetch_postings(filters)
    return apply_post_filters(postings, filters)