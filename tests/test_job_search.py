from app.job_search.filters import dedupe, _looks_remote
from app.schemas.job import JobPosting  # عدّل المسار


def make_job(title="Dev", company="Acme", description="", **kw):
    return JobPosting(
        external_id=kw.get("external_id", "1"),
        title=title,
        company=company,
        location="UK",
        remote=False,
        url="https://example.com",
        description=description,
        posted_date="2026-10-08T00:00:00Z",
    )


def test_dedupe_same_job_different_company_spelling():
    desc = "Machine Learning Engineer remote role at an AI startup"
    jobs = [
        make_job("ML Engineer", "Ocho People", desc, external_id="1"),
        make_job("ML Engineer", "Ocho", desc, external_id="2"),
    ]
    assert len(dedupe(jobs)) == 1


def test_dedupe_keeps_different_jobs():
    jobs = [
        make_job("Backend Dev", "A", "python backend"),
        make_job("Data Scientist", "A", "python data"),
    ]
    assert len(dedupe(jobs)) == 2


def test_remote_detected():
    assert _looks_remote(make_job(description="Fully remote UK role")) is True


def test_hybrid_is_not_remote():
    job = make_job(description="Belfast Hybrid, 3 days per week in the office, remote tools")
    assert _looks_remote(job) is False
