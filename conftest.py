"""
Test setup.

Environment variables are set BEFORE the app is imported, so:
- tests always run in demo mode (no real Gemini calls, no API cost),
- tests use a separate database file (your real fitbuddy.db is untouched),
- the admin dashboard is open during tests.
"""
import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent.parent / "test_fitbuddy.db"

os.environ["GEMINI_API_KEY"] = ""
os.environ["ADMIN_KEY"] = ""
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

if TEST_DB.exists():
    TEST_DB.unlink()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # Using TestClient as a context manager runs the app's lifespan,
    # which calls init_db() and creates the tables.
    with TestClient(app) as test_client:
        yield test_client
