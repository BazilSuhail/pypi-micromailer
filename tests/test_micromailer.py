from __future__ import annotations

import asyncio
from email.message import EmailMessage

import pytest

from micromailer import (
    AsyncHTTPMailer,
    AsyncSMTPMailer,
    SMTPPool,
    render_template,
    validate_html,
)
from micromailer.core.base import MailerBatch, MailerResult, SMTPError
from micromailer.core.smtp import AsyncSMTPMailer


def test_imports() -> None:
    assert AsyncSMTPMailer is not None
    assert AsyncHTTPMailer is not None
    assert SMTPPool is not None


def test_mailer_result_slots() -> None:
    r = MailerResult(to="a@b.com", subject="s", accepted=True)
    assert r.to == "a@b.com"
    assert r.accepted is True
    assert r.error == ""


def test_mailer_batch_count() -> None:
    batch = MailerBatch(
        [
            MailerResult("a@b.com", "s", True),
            MailerResult("a@b.com", "s", False, error="fail"),
        ]
    )
    assert batch.total == 2
    assert batch.accepted == 1


def test_smtp_error() -> None:
    e = SMTPError(code=550, message="fail")
    assert e.code == 550
    assert "fail" in str(e)


def test_smtp_mailer_init() -> None:
    m = AsyncSMTPMailer(
        host="smtp.gmail.com",
        port=587,
        username="u",
        password="p",
        use_tls=True,
        timeout=10.0,
    )
    assert m.host == "smtp.gmail.com"
    assert m.port == 587
    assert m.username == "u"
    assert m.password == "p"
    assert m.use_tls is True
    assert m.timeout == 10.0
    assert m._connected is False


def test_render_template() -> None:
    assert render_template("Hi {name}", {"name": "Bazil"}) == "Hi Bazil"


def test_validate_html_balanced() -> None:
    assert validate_html("<div><p>ok</p></div>") == []


def test_validate_html_unbalanced() -> None:
    errors = validate_html("<div><p>oops</div>")
    assert any("Unclosed" in e or "Unexpected" in e for e in errors)


@pytest.mark.asyncio
async def test_http_mailer_init() -> None:
    m = AsyncHTTPMailer(api_key="key", base_url="https://api.resend.com")
    assert m.api_key == "key"
    assert m.base_url == "https://api.resend.com"


@pytest.mark.asyncio
async def test_pool_acquire_release() -> None:
    async with SMTPPool(max_size=2, host="localhost", port=25) as pool:
        m = await pool.acquire()
        assert isinstance(m, AsyncSMTPMailer)
        await pool.release(m)
        m2 = await pool.acquire()
        assert m is m2  # reused
