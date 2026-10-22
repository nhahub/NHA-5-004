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


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield


def test_signup_login_and_protected_route():
    signup_response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "test1234",
        },
    )

    assert signup_response.status_code == 200
    assert "access_token" in signup_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "test1234",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    protected_response = client.get(
        "/applications/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert protected_response.status_code == 200


def test_duplicate_signup():
    payload = {
        "email": "test@example.com",
        "password": "test1234",
    }

    first_response = client.post(
        "/auth/signup",
        json=payload,
    )

    assert first_response.status_code == 200

    duplicate_response = client.post(
        "/auth/signup",
        json=payload,
    )

    assert duplicate_response.status_code == 400


def test_wrong_password():
    client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "test1234",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_invalid_token():
    response = client.get(
        "/applications/",
        headers={"Authorization": "Bearer abc123"},
    )

    assert response.status_code == 401
