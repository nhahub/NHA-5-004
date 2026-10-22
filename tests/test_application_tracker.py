import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models  # ensures all SQLAlchemy models are registered

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()



client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous
    
def make_headers(email="tracker@example.com"):
    response = client.post(
        "/auth/signup",
        json={"email": email, "password": "test1234"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_job(headers, title="Python Dev", company="Acme", **extra):
    return client.post(
        "/applications/",
        json={"job_title": title, "company": company, **extra},
        headers=headers,
    )


def test_create_application_defaults_to_saved():
    headers = make_headers()

    response = create_job(headers)

    assert response.status_code == 201
    body = response.json()
    assert body["job_title"] == "Python Dev"
    assert body["status"] == "saved"


def test_list_only_returns_own_applications():
    alice = make_headers("alice@example.com")
    bob = make_headers("bob@example.com")

    create_job(alice, "Alice Job")
    create_job(bob, "Bob Job")

    response = client.get("/applications/", headers=alice)

    assert response.status_code == 200
    titles = [a["job_title"] for a in response.json()]
    assert titles == ["Alice Job"]


def test_list_filter_by_status():
    headers = make_headers()
    create_job(headers, "Saved Job")
    applied = create_job(headers, "Applied Job").json()
    client.patch(
        f"/applications/{applied['id']}",
        json={"status": "applied"},
        headers=headers,
    )

    response = client.get("/applications/?status_filter=applied", headers=headers)

    assert response.status_code == 200
    assert [a["job_title"] for a in response.json()] == ["Applied Job"]


def test_update_status():
    headers = make_headers()
    app_id = create_job(headers).json()["id"]

    response = client.patch(
        f"/applications/{app_id}",
        json={"status": "interviewing"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "interviewing"


def test_update_invalid_status_returns_422():
    headers = make_headers()
    app_id = create_job(headers).json()["id"]

    response = client.patch(
        f"/applications/{app_id}",
        json={"status": "xyz"},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_missing_application_returns_404():
    headers = make_headers()

    response = client.patch(
        "/applications/999",
        json={"status": "applied"},
        headers=headers,
    )

    assert response.status_code == 404


def test_cannot_update_another_users_application():
    alice = make_headers("alice@example.com")
    bob = make_headers("bob@example.com")
    app_id = create_job(alice).json()["id"]

    response = client.patch(
        f"/applications/{app_id}",
        json={"status": "applied"},
        headers=bob,
    )

    assert response.status_code == 404


def test_delete_application():
    headers = make_headers()
    app_id = create_job(headers).json()["id"]

    response = client.delete(f"/applications/{app_id}", headers=headers)

    assert response.status_code == 204
    assert client.get("/applications/", headers=headers).json() == []


def test_delete_missing_application_returns_404():
    headers = make_headers()

    response = client.delete("/applications/999", headers=headers)

    assert response.status_code == 404


def test_stale_returns_empty_for_fresh_applications():
    headers = make_headers()
    create_job(headers)

    response = client.get("/applications/stale", headers=headers)

    assert response.status_code == 200
    assert response.json() == []