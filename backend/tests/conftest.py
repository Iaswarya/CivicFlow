"""
Test fixtures. Uses an in-memory SQLite DB (via a StaticPool so all connections in a
test share the same in-memory database) so the test suite runs anywhere with no
external Postgres dependency -- production still uses PostgreSQL per DATABASE_URL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OCR_ENGINE"] = "demo"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.models import models  # noqa: F401
from app.main import app

TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def inspector_token(client):
    client.post("/api/auth/register", json={
        "full_name": "Test Inspector", "email": "inspector@test.com",
        "password": "TestPass123", "role": "INSPECTOR",
    })
    resp = client.post("/api/auth/login", json={"email": "inspector@test.com", "password": "TestPass123"})
    return resp.json()["access_token"]
