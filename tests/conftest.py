"""Fixtures for eSolat Takwim tests."""
import json
from pathlib import Path
from unittest.mock import patch

import aiohttp
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def no_aiodns():
    with patch("aiohttp.connector.DefaultResolver", aiohttp.ThreadedResolver):
        yield


@pytest.fixture
def frozen(freezer):
    """10:00 MYT, Saturday 31 Oct 2026."""
    freezer.move_to("2026-10-31 10:00:00+08:00")
    return freezer
