# micromailer

[![PyPI version](https://img.shields.io/pypi/v/micromailer.svg)](https://pypi.org/project/micromailer/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/micromailer.svg)](https://pypi.org/project/micromailer/)
[![Python Versions](https://img.shields.io/pypi/pyversions/micromailer.svg)](https://pypi.org/project/micromailer/)

Ultra-fast, modular, zero-dependency async email engine for Python 3.12+.

- Zero runtime dependencies
- Async SMTP via stdlib `smtplib` (works on 3.12, 3.13, 3.14)
- HTTP API backend for Resend / SES-style providers
- `SMTPPool` for connection reuse in bulk sends
- `validate_html` and `render_template` utilities
- PEP 561 typed package (`py.typed`)

## Install

```bash
pip install micromailer
```

## Quick start

```python
import asyncio
from micromailer import AsyncSMTPMailer

async def main() -> None:
    async with AsyncSMTPMailer(
        host="smtp.gmail.com",
        port=587,
        username="you@gmail.com",
        password="app-password",
    ) as mailer:
        await mailer.send(
            to="friend@example.com",
            subject="Hello",
            html_body="<p>Hi</p>",
        )

asyncio.run(main())
```

## Sending patterns

All patterns are async-first. Use `async with` so the connection is always closed.

### Single recipient

```python
await mailer.send(
    to="alex@example.com",
    subject="Your grade",
    html_body="<p>Grade: A</p>",
)
```

### Multiple recipients

```python
await mailer.send(
    to=["alex@example.com", "jordan@example.com"],
    subject="Your grade",
    html_body="<p>Grade: A</p>",
)
```

### Custom sender

```python
await mailer.send(
    to="alex@example.com",
    subject="Hi",
    html_body="<p>Hello</p>",
    sender="registrar@university.edu",
)
```

### Plain-text email

```python
text = "Hello,\n\nYour grade is A.\n"
html = f"<pre>{text}</pre>"
await mailer.send(to="alex@example.com", subject="Grade", html_body=html)
```

### HTML email with inline CSS

```python
html = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h1 style="color: #1a73e8;">Results</h1>
  <p style="color: #444;">Grade: <strong>A</strong></p>
</div>
"""
await mailer.send(to="alex@example.com", subject="Results", html_body=html)
```

### Implicit TLS (port 465)

```python
async with AsyncSMTPMailer(
    host="smtp.gmail.com",
    port=465,
    username="you@gmail.com",
    password="app-password",
    use_tls=True,
) as mailer:
    await mailer.send(to="friend@example.com", subject="Hello", html_body="<p>Hi</p>")
```

### Bulk sends with SMTPPool

```python
from micromailer import SMTPPool

async def bulk(contacts: list[dict]) -> None:
    async with SMTPPool(max_size=5, host="smtp.gmail.com", port=587,
                        username="you@gmail.com", password="app-password") as pool:
        for contact in contacts:
            mailer = await pool.acquire()
            try:
                await mailer.send(
                    to=contact["email"],
                    subject="Newsletter",
                    html_body="<p>Hello</p>",
                )
            finally:
                await pool.release(mailer)
```

### HTTP API backend (Resend / SES)

```python
from micromailer import AsyncHTTPMailer

async def send_via_api() -> None:
    async with AsyncHTTPMailer(api_key="re_xxx", base_url="https://api.resend.com") as mailer:
        await mailer.send(
            to="alex@example.com",
            subject="Hello",
            html_body="<p>Hi from API</p>",
        )
```

### Error handling

```python
from micromailer.core.base import SMTPError

try:
    await mailer.send(to="alex@example.com", subject="Hi", html_body="<p>Hi</p>")
except SMTPError as e:
    print(f"SMTP failed: {e.code} -> {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__} -> {e}")
```

## Utilities

```python
from micromailer import validate_html, render_template, encode_base64

validate_html("<div><p>ok</p></div>")          # []
validate_html("<div><p>oops</div>")             # ["Unclosed tag <div>", ...]

render_template("Hi {name}", {"name": "Alex"})  # "Hi Alex"
encode_base64("raw bytes")                       # "cmF3IGJ5dGVz"
```

## Module layout

- `core.base` — `MailerBackend` protocol, `SMTPError`, `MailerResult`, `MailerBatch`
- `core.smtp` — `AsyncSMTPMailer`
- `core.http` — `AsyncHTTPMailer`
- `core.pool` — `SMTPPool`
- `utils.mime` — `validate_html`, `render_template`, `encode_base64`, `decode_base64`
