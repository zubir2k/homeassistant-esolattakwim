"""Fixtures for eSolat Takwim tests."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import aiohttp
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

if sys.platform == "win32":
    import pytest_socket
    def _win_disable_socket(allow_unix_socket=False):
        pass
    pytest_socket.disable_socket = _win_disable_socket


def load_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    if sys.platform == "win32":
        import pytest_socket
        pytest_socket.enable_socket()
    yield
    if sys.platform == "win32":
        import pytest_socket
        pytest_socket.enable_socket()


@pytest.fixture(autouse=True)
def no_aiodns():
    with patch("aiohttp.connector.DefaultResolver", aiohttp.ThreadedResolver):
        yield


@pytest.fixture
def frozen(freezer):
    """10:00 MYT, Saturday 31 Oct 2026."""
    freezer.move_to("2026-10-31 10:00:00+08:00")
    return freezer
