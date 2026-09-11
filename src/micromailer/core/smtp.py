from __future__ import annotations
import asyncio
import ssl
import base64
from email.message import EmailMessage
from typing import Optional, List, Union

from .base import MailerBackend, SMTPError


class AsyncSMTPMailer:
    __slots__ = (
        "host",
        "port",
        "username",
        "password",
        "use_tls",
        "timeout",
        "_reader",
        "_writer",
        "_connected",
    )

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def _read_resp(self) -> int:
        if self._reader is None:
            raise SMTPError(-1, "Not connected")
        raw = await self._reader.readline()
        resp = raw.decode(errors="replace").strip()
        code = int(resp[:3]) if len(resp) >= 3 else -1
        if code >= 400:
            raise SMTPError(code, resp)
        return code

    async def _cmd(self, command: str) -> int:
        if self._writer is None:
            raise SMTPError(-1, "Not connected")
        self._writer.write(f"{command}\r\n".encode())
        await self._writer.drain()
        if command == "QUIT":
            try:
                raw = await asyncio.wait_for(self._reader.readline(), timeout=2.0)
                code = int(raw[:3]) if len(raw) >= 3 else -1
            except asyncio.TimeoutError:
                code = -1
            return code
        return await self._read_resp()

    async def _connect(self) -> None:
        if self._connected:
            return

        ssl_ctx = ssl.create_default_context()
        loop = asyncio.get_running_loop()

        if self.use_tls and self.port == 465:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, ssl=ssl_ctx),
                timeout=self.timeout,
            )
        else:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )

        await self._read_resp()
        await self._cmd(f"EHLO {self.host}")

        if self.use_tls and self.port not in (465,):
            resp = await self._cmd("STARTTLS")
            if resp == 220:
                new_reader = asyncio.StreamReader()
                reader_proto = self._reader._protocol
                reader_proto._stream_reader = new_reader
                new_transport = await loop.start_tls(
                    self._writer.transport,
                    reader_proto,
                    sslcontext=ssl_ctx,
                    server_hostname=self.host,
                )
                self._reader = new_reader
                self._writer = asyncio.StreamWriter(
                    new_transport, reader_proto, new_reader, loop
                )
                await self._cmd(f"EHLO {self.host}")

        if self.username and self.password:
            auth = base64.b64encode(
                f"\0{self.username}\0{self.password}".encode()
            ).decode()
            await self._cmd(f"AUTH PLAIN {auth}")

        self._connected = True

    async def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        sender: Optional[str] = None,
    ) -> bool:
        recipients = [to] if isinstance(to, str) else list(to)
        sender_email = sender or self.username

        if not sender_email:
            raise SMTPError(-1, "No sender specified")

        await self._connect()

        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.add_alternative(html_body, subtype="html")

        await self._cmd(f"MAIL FROM:<{sender_email}>")
        for rcpt in recipients:
            await self._cmd(f"RCPT TO:<{rcpt}>")

        await self._cmd("DATA")
        self._writer.write(msg.as_bytes() + b"\r\n.\r\n")
        await self._writer.drain()
        await self._read_resp()

        await self._cmd("RSET")
        return True

    async def close(self) -> None:
        if self._writer is not None:
            try:
                await self._cmd("QUIT")
            except SMTPError:
                pass
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except asyncio.TimeoutError:
                pass
            self._writer = None
            self._reader = None
        self._connected = False

    async def reset(self) -> None:
        if self._writer and self._connected:
            try:
                await self._cmd("RSET")
            except SMTPError:
                pass

    async def aclose(self) -> None:
        await self.close()

    async def __aenter__(self) -> AsyncSMTPMailer:
        await self._connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
