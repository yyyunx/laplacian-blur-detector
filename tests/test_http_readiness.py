"""Regression for the observed container startup connection-reset race."""

from io import BytesIO
from pathlib import Path
import runpy
from urllib.error import URLError

import pytest


@pytest.fixture
def probe():
    return runpy.run_path(str(Path(__file__).with_name("smoke_http.py")))["wait_for_health"]


def response(body=b'{"status":"ok"}'):
    stream = BytesIO(body)
    stream.status = 200
    return stream


def test_startup_connection_reset_is_retried_until_exact_health_contract(monkeypatch, probe):
    calls = []

    def fetch(url, timeout):
        calls.append((url, timeout))
        if len(calls) == 1:
            raise ConnectionResetError("Container proxy connected before server was ready")
        return response()

    monkeypatch.setitem(probe.__globals__, "urlopen", fetch)
    probe("http://127.0.0.1:8000", interval=0)
    assert len(calls) == 2 and all(url.endswith("/healthz") for url, _ in calls)


def test_permanent_network_failure_has_a_bounded_deadline(monkeypatch, probe):
    def unavailable(*args, **kwargs):
        raise URLError("Service unavailable")

    monkeypatch.setitem(probe.__globals__, "urlopen", unavailable)
    with pytest.raises(TimeoutError, match="deadline"):
        probe("http://127.0.0.1:8000", timeout=0.01, interval=0.002)


def test_bad_health_payload_is_not_hidden_by_retry(monkeypatch, probe):
    monkeypatch.setitem(probe.__globals__, "urlopen", lambda *args, **kwargs: response(b'{"status":"broken"}'))
    with pytest.raises(AssertionError):
        probe("http://127.0.0.1:8000")
