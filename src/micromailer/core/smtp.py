from __future__ import annotations
import asyncio
import smtplib
from email.message import EmailMessage
from typing import Optional, List, Union

from .base import SMTPError


class AsyncSMTPMailer:
    __slots__ = (
        "host",
        "port",
        "username",
        "password",
        "use_tls",
        "timeout",
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

    def _send_sync(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        sender_email: str,
    ) -> bool:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg.add_alternative(html_body, subtype="html")

        if self.use_tls and self.port == 465:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        try:
            server.ehlo()
            if self.use_tls and self.port not in (465,):
                server.starttls()
                server.ehlo()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(sender_email, to, msg.as_string())
        except smtplib.SMTPException:
            return False
        finally:
            try:
                server.quit()
            except smtplib.SMTPException:
                pass
        return True

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

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._send_sync, recipients, subject, html_body, sender_email
        )

    async def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass

    async def __aenter__(self) -> AsyncSMTPMailer:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass
