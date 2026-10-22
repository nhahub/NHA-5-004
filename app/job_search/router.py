"""
HTTP layer only: parse query params into JobSearchFilters, call the service,
map errors to HTTP status codes. No business logic here.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.common.exceptions import ExternalAPIError
from app.job_search.filters import JobSearchFilters
from app.job_search.service import search_jobs
from app.schemas.job import JobPosting

router = APIRouter(tags=["job-search"])

# بستقبل الطلب من المستخدم عبر البحث 

@router.get("/search", response_model=list[JobPosting])
#التاكد من صحة اليانات المستخدم باعتها 
def search(filters: JobSearchFilters = Depends()):
    try:
        #لو سليمة بيبعتها ل الدالة دة الموجودة في ال service 
        return search_jobs(filters)
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))