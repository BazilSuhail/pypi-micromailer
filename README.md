# micromailer

Ultra-fast, modular, zero-dependency async email engine for Python, FastAPI, and Django.

- Zero runtime dependencies
- Async SMTP with automatic STARTTLS / implicit TLS
- HTTP API backend for Resend / SES-style providers
- SMTP connection pool for ultra-fast bulk sending
- HTML validation and simple templating utilities
- Type-checked with `py.typed`

## Install

```bash
pip install micromailer
```

## Quick start

```python
import asyncio
from micromailer import AsyncSMTPMailer


async def main() -> None:
    mailer = AsyncSMTPMailer(
        host="smtp.gmail.com",
        port=587,
        username="you@gmail.com",
        password="app-password",
        use_tls=True,
    )

    ok = await mailer.send(
        to="friend@example.com",
        subject="Hello",
        html_body="<h1>Hi</h1>",
        sender="you@gmail.com",
    )

    print("Sent!" if ok else "Failed")

    await mailer.aclose()


asyncio.run(main())
```

## Backend swapping with protocols

```python
from typing import List, Union
from micromailer import AsyncSMTPMailer, AsyncHTTPMailer
from micromailer.core.base import MailerBackend


def send_all(
    backend: MailerBackend,
    to: Union[str, List[str]],
    subject: str,
    html_body: str,
) -> None:
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        backend.send(to, subject, html_body)
    )


send_all(AsyncSMTPMailer("smtp.gmail.com"), "a@b.com", "Hi", "<p>ok</p>")
send_all(AsyncHTTPMailer("api-key", "https://api.resend.com"), "a@b.com", "Hi", "<p>ok</p>")
```

## SMTP connection pool

Reuse TLS connections across hundreds of emails to cut TLS handshake overhead:

```python
from micromailer import SMTPPool


async def bulk() -> None:
    async with SMTPPool(max_size=5, host="smtp.gmail.com", port=587, username="...", password="...") as pool:
        for contact in contacts:
            mailer = await pool.acquire()
            await mailer.send(contact["email"], "Newsletter", "<p>Hello</p>")
            await pool.release(mailer)


asyncio.run(bulk())
```

## Utilities

```python
from micromailer import validate_html, render_template, encode_base64

validate_html("<div><p>unclosed")  # []

template = render_template("Hello {name}", {"name": "Bazil"})  # "Hello Bazil"
b64 = encode_base64("raw bytes")  # "cmF3IGJ5dGVz"
```

## Module layout

- `core.base` — `MailerBackend` protocol, `SMTPError`, `MailerResult`, `MailerBatch`
- `core.smtp` — `AsyncSMTPMailer`
- `core.http` — `AsyncHTTPMailer`
- `core.pool` — `SMTPPool`
- `utils.mime` — `validate_html`, `render_template`, `encode_base64`, `decode_base64`
