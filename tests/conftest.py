"""Fixtures shared by every test file. pytest finds this file automatically."""
import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """A fresh app with its own empty database file, for each test."""
    return create_app({
        "TESTING": True,
        "DB_PATH": str(tmp_path / "test.db"),  # tmp_path is deleted by pytest afterwards
    })


@pytest.fixture
def client(app):
    """Calls the app in memory: no server, no network."""
    return app.test_client()
