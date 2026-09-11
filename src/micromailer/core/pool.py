from __future__ import annotations
from typing import Optional

from .smtp import AsyncSMTPMailer


class SMTPPool:
    __slots__ = (
        "host",
        "port",
        "username",
        "password",
        "use_tls",
        "timeout",
        "_pool",
        "_max_size",
    )

    def __init__(self, max_size: int = 5, **kwargs) -> None:
        self.host = kwargs.get("host", "")
        self.port = kwargs.get("port", 587)
        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password", "")
        self.use_tls = kwargs.get("use_tls", True)
        self.timeout = kwargs.get("timeout", 30.0)
        self._pool: list[AsyncSMTPMailer] = []
        self._max_size = max_size

    async def acquire(self) -> AsyncSMTPMailer:
        if self._pool:
            return self._pool.pop()
        return AsyncSMTPMailer(
            self.host,
            self.port,
            self.username,
            self.password,
            self.use_tls,
            self.timeout,
        )

    async def release(self, mailer: AsyncSMTPMailer) -> None:
        if len(self._pool) < self._max_size:
            self._pool.append(mailer)
        await mailer.aclose()

    async def close(self) -> None:
        for m in self._pool:
            await m.aclose()
        self._pool.clear()

    async def __aenter__(self) -> SMTPPool:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def __aiter__(self):
        yield self
        await self.close()
