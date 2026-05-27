"""Property and contract tests for password hashing and token handling."""

import time

import jwt
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core import security
from app.core.config import get_settings

_printable = st.characters(min_codepoint=33, max_codepoint=126)


@settings(max_examples=30, deadline=None)
@given(password=st.text(alphabet=_printable, min_size=1, max_size=64))
def test_hash_roundtrips_and_rejects_wrong(password: str) -> None:
    hashed = security.hash_password(password)
    assert hashed != password
    assert security.verify_password(password, hashed) is True
    assert security.verify_password(password + "x", hashed) is False


def test_token_carries_subject_and_tenant() -> None:
    token = security.create_access_token("7", tenant_id=3)
    payload = security.decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["tenant_id"] == 3


def test_expired_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "access_token_ttl_minutes", -1)
    token = security.create_access_token("1", tenant_id=1)
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_access_token(token)


def test_tampered_token_is_rejected() -> None:
    token = security.create_access_token("1", tenant_id=1)
    with pytest.raises(jwt.PyJWTError):
        jwt.decode(token + "tamper", get_settings().jwt_secret, algorithms=["HS256"])


def test_token_not_yet_expired_decodes() -> None:
    token = security.create_access_token("1", tenant_id=1)
    time.sleep(0)
    assert security.decode_access_token(token)["sub"] == "1"
