from unittest.mock import MagicMock, patch

from src.services.core.http_client import mask_headers, TokenCache, LoggedSession


# --- L10: máscara do Authorization no log ---

def test_mask_headers_masks_authorization():
    masked = mask_headers({"Authorization": "Bearer segredo", "X-Trace": "abc"})
    assert masked["Authorization"] == "***"
    assert masked["X-Trace"] == "abc"


def test_mask_headers_is_non_mutating_and_handles_none():
    original = {"Authorization": "Bearer segredo"}
    masked = mask_headers(original)
    assert original["Authorization"] == "Bearer segredo"  # não muta o original
    assert mask_headers(None) is None


# --- L2: cache de token com TTL ---

class FakeClock:
    def __init__(self, start=0.0):
        self._now = start

    def now(self):
        return self._now

    def advance(self, seconds):
        self._now += seconds


def test_token_cache_returns_same_token_within_ttl():
    clock = FakeClock()
    cache = TokenCache(ttl_seconds=300, time_fn=clock.now)
    calls = []

    def fetch():
        calls.append(1)
        return f"tok-{len(calls)}"

    first = cache.get_or_refresh(fetch)
    second = cache.get_or_refresh(fetch)

    assert first == "tok-1"
    assert second == "tok-1"  # veio do cache
    assert len(calls) == 1  # fetch chamado uma única vez


def test_token_cache_refreshes_after_ttl_expires():
    clock = FakeClock()
    cache = TokenCache(ttl_seconds=300, time_fn=clock.now)
    calls = []

    def fetch():
        calls.append(1)
        return f"tok-{len(calls)}"

    cache.get_or_refresh(fetch)
    clock.advance(301)
    refreshed = cache.get_or_refresh(fetch)

    assert refreshed == "tok-2"
    assert len(calls) == 2


# --- L1: TLS ligado ---

def test_logged_session_verifies_tls_by_default(monkeypatch):
    monkeypatch.delenv("PATH_ROOT_CA", raising=False)
    session = LoggedSession()
    assert session.verify is True


def test_logged_session_uses_ca_bundle_when_configured(monkeypatch):
    monkeypatch.setenv("PATH_ROOT_CA", "/app/root.crt")
    session = LoggedSession()
    assert session.verify == "/app/root.crt"


def test_logged_session_logs_masked_authorization(caplog):
    session = LoggedSession()
    fake_response = MagicMock(status_code=200)
    with patch("requests.Session.request", return_value=fake_response):
        with caplog.at_level("INFO", logger="GatewayHttpClient"):
            session.request("GET", "https://x", headers={"Authorization": "Bearer segredo"})

    assert '"Authorization": "***"' in caplog.text
    assert "Bearer segredo" not in caplog.text  # L10: token nunca aparece no log
