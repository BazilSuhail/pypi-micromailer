from __future__ import annotations
import asyncio
import json
import ssl
from typing import Optional, List, Union, Dict, Any

from .base import MailerBackend, SMTPError


class AsyncHTTPMailer:
    __slots__ = ("api_key", "base_url", "ssl_ctx")

    def __init__(self, api_key: str, base_url: str = "") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.ssl_ctx = ssl.create_default_context()

    async def _request(
        self, method: str, path: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        from urllib.parse import urlparse

        if not self.base_url:
            raise SMTPError(-1, "No base URL configured")

        parsed = urlparse(self.base_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        kw: Dict[str, Any] = {}
        if parsed.scheme == "https":
            kw["ssl"] = self.ssl_ctx

        reader, writer = await asyncio.open_connection(host, port, **kw)

        body = json.dumps(payload).encode()
        headers = {
            "Host": host,
            "User-Agent": "micromailer/0.1.0",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Length": str(len(body)),
        }

        req = f"{method} {path or '/'} HTTP/1.1\r\n"
        req += "\r\n".join(f"{k}: {v}" for k, v in headers.items())
        req += "\r\n\r\n"
        writer.write(req.encode() + body)
        await writer.drain()

        resp = b""
        while True:
            try:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=30)
            except asyncio.TimeoutError:
                break
            if not chunk:
                break
            resp += chunk
            if b"\r\n\r\n" in resp:
                header, body_part = resp.split(b"\r\n\r\n", 1)
                if b"Transfer-Encoding: chunked" in header:
                    continue
                cl = None
                for line in header.split(b"\r\n"):
                    if line.lower().startswith(b"content-length:"):
                        cl = int(line.split(b":", 1)[1].strip())
                        break
                if cl is None or len(body_part) >= cl:
                    break

        writer.close()
        await writer.wait_closed()

        status_line = resp.split(b"\r\n")[0]
        status = int(status_line.split(b" ")[1]) if len(status_line.split(b" ")) > 1 else -1

        parts = resp.split(b"\r\n\r\n", 1)
        body_str = parts[1].decode(errors="replace") if len(parts) > 1 else ""

        if status >= 400:
            raise SMTPError(status, body_str)

        return json.loads(body_str) if body_str else {}

    async def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        sender: Optional[str] = None,
    ) -> bool:
        recipients = [to] if isinstance(to, str) else list(to)
        payload = {
            "from": sender or "micromailer@example.com",
            "to": recipients,
            "subject": subject,
            "html": html_body,
        }
        result = await self._request("POST", "/emails", payload)
        return result.get("id") is not None
