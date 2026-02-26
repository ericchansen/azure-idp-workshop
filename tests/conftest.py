"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from workshop.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
