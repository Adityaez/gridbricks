"""Pytest configuration and deterministic test fixtures."""
import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_delivery_interval():
    return {
        "startTime": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "cutoff_time": datetime(2026, 1, 14, 17, 0, tzinfo=timezone.utc),
    }

