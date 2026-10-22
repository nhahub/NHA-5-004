"""
ONLY module that talks to the external job-board API (Adzuna): HTTP calls, auth,
response parsing into JobPosting. No filtering/business logic here.
"""
import requests

from app.config import settings
from app.common.exceptions import ExternalAPIError
from app.job_search.filters import JobSearchFilters
from app.schemas.job import JobPosting

# المستخدم بيبعت البيانات بتاعتو 
def _build_params(f: JobSearchFilters) -> dict:
    params = {
        "app_id": settings.job_api_app_id,
        "app_key": settings.job_api_key,
        "what": f"{f.keyword} remote" if f.remote else f.keyword,
        "results_per_page": f.results_per_page,
        "sort_by": "date",
        "where": f.location,
        "max_days_old": f.date_posted,
        "full_time": 1 if f.full_time else None,
    }
    return {k: v for k, v in params.items() if v is not None}

# قالب للبيانات البترجع علشين نوحد الاسامي 
def _to_posting(raw: dict) -> JobPosting:
    return JobPosting(
        external_id=str(raw["id"]),
        title=raw.get("title") or "Untitled",
        company=(raw.get("company") or {}).get("display_name") or "Unknown",
        location=(raw.get("location") or {}).get("display_name"),
        url=raw.get("redirect_url") or "",
        description=raw.get("description") or "",
        posted_date=raw.get("created"),
    )

# نبعمل الرابط الفعلي البنبعتو ل موقع
def fetch_postings(f: JobSearchFilters) -> list[JobPosting]:
    url = f"{settings.job_api_base_url}/{f.country}/search/{f.page}"
    try:
        resp = requests.get(url, params=_build_params(f), timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ExternalAPIError(f"Job API request failed: {e}")

    return [_to_posting(item) for item in resp.json().get("results", [])]