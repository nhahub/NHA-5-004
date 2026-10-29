# job_search_agent: Personal Job Search & Application Agent

A backend for helping a job seeker move from raw CV materials to a structured
personal profile, targeted job search, tailored applications, interview preparation,
and application tracking. The system is built around a practical architecture:
plain software for infrastructure, LLM modules for reasoning and writing, and a
single interview-prep agent for multi-step planning.

## What this project does

The app supports the full job-search lifecycle:

- CV upload and extraction into a structured profile
- Job discovery using structured search APIs
- Skill-gap analysis against job requirements
- Tailoring of CV bullets and cover letters
- Career-resource retrieval with RAG
- Interview preparation planning via a focused agent
- Application tracking and reminder workflows

## Design principles

The project intentionally keeps each concern in the simplest layer that fits it:

| Approach | Used for | Where |
|---|---|---|
| Normal LLM | Reasoning and writing on content already available | `app/cv_extraction/`, `app/skill_gap/`, `app/tailoring/` |
| RAG | Retrieval over changing external knowledge | `app/career_rag/`, `app/job_rag/` |
| Agent | Multi-step planning and branching runtime logic | `app/interview_agent/` |
| Memory | Persistent facts about the user | `app/memory/` |
| Normal software | Auth, database, job search, resume storage, app tracking | `app/auth/`, `app/job_search/`, `app/application_tracker/`, `app/storage/` |

Only one agent exists in the system: the interview-prep planner. Everything else
uses plain LLM calls or plain application code unless multi-step branching truly
requires an agent.

## Repository structure

```text
job_search_agent/
├── app/
│   ├── main.py                 # FastAPI app assembly and router mounting
│   ├── config.py               # Central app configuration
│   ├── database.py             # Database/session setup
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic request/response contracts
│   ├── common/                 # Shared exceptions, logging, helpers
│   ├── auth/                   # Auth and JWT flow
│   ├── storage/                # Resume file storage
│   ├── memory/                 # Persistent user context
│   ├── llm/                    # Shared LLM client
│   ├── cv_extraction/          # Resume parsing + structured profile extraction
│   ├── job_search/             # Structured job search integration
│   ├── skill_gap/              # CV-to-job gap analysis
│   ├── tailoring/              # Resume tailoring and cover letters
│   ├── career_rag/             # Career-resource retrieval and embedding flow
│   ├── interview_agent/        # Interview-prep planning agent
│   ├── application_tracker/    # Application CRUD and reminders
│   ├── job_rag/                # Optional semantic job-search stretch work
│   └── ...
├── migrations/                 # Alembic migrations
├── scripts/                    # Seed and ingest utilities
├── tests/                      # Feature-level tests
├── frontend/                   # Client placeholder; backend is the source of truth
├── .env.example                # Required environment variables
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker Compose setup
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── LICENSE                     # Project license
├── README.md                   # Project documentation
└── .gitignore
```

## Local setup

1. Create a local environment file:

```bash
cp .env.example .env
```

2. Fill in the values in `.env`, especially:

- `DATABASE_URL`
- `Groq_API_KEY`
- `TAVILY_API_KEY`
- `JOB_API_BASE_URL`
- `JOB_API_KEY`
- `SECRET_KEY`

Example values are defined in `.env.example`.

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app locally:

```bash
# Option A: quick local dev (no migration history)
python -m scripts.seed_db

# Option B: use Alembic migrations
alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn app.main:app --reload
```

The API is available at:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Docker

```bash
docker-compose up --build
```

## Build order and module sequencing

The project is structured in phases:

1. Foundations — `app/models/`, `app/auth/`, `app/storage/`
2. Core pipeline — `app/cv_extraction/` → `app/memory/`
3. Structured search — `app/job_search/`
4. Skill-gap and tailoring — `app/skill_gap/`, `app/tailoring/`
5. Career-resource RAG — `app/career_rag/`
6. Interview-prep agent — `app/interview_agent/`
7. Stretch work — `app/job_rag/`, reminders, market insights

## Module rules

A few project conventions keep the codebase predictable:

- Each feature folder has a `router.py` for HTTP concerns and a `service.py` for orchestration.
- `models/` are for database structure; `schemas/` are for API contracts.
- LLM code imports the shared client from `app/llm/` instead of creating separate provider clients.
- User memory is centralized in `app/memory/` instead of re-implemented per feature.
- CV parsing, file storage, and LLM interpretation remain separate concerns.

## Testing

```bash
pytest tests/ -v
```

## Notes

This repository is a backend-first scaffold intended to be connected to a client UI or CLI. The frontend folder is intentionally minimal and acts as a placeholder for user-facing tooling. The main runtime contract is the FastAPI backend in `app/`.
