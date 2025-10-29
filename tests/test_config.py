from __future__ import annotations

import pytest

from bot.config import load_settings, validate_settings


def test_load_settings_defaults(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.setenv("PROMO_CODE", "TEST-CODE")
    s = load_settings()
    assert s.promo_code == "TEST-CODE"
    assert isinstance(s.active_post_ids, list)
    assert s.log_level


def test_validate_settings(monkeypatch):
    # Missing SUBSCRIPTION_TARGET -> error
    monkeypatch.delenv("SUBSCRIPTION_TARGET", raising=False)
    monkeypatch.delenv("PRIVATE_GROUP_INVITE_LINK", raising=False)
    monkeypatch.delenv("PRIVATE_GROUP_ID", raising=False)
    s = load_settings()
    with pytest.raises(RuntimeError):
        validate_settings(s)

    # Valid when target and one of A/B given
    monkeypatch.setenv("SUBSCRIPTION_TARGET", "@channel")
    monkeypatch.setenv("PRIVATE_GROUP_INVITE_LINK", "https://t.me/+abc")
    s2 = load_settings()
    validate_settings(s2)
