from __future__ import annotations
from typing import Optional, List, Union, runtime_checkable, Protocol, runtime_checkable


@runtime_checkable
class MailerBackend(Protocol):
    async def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        sender: Optional[str] = None,
    ) -> bool:
        ...


class SMTPError(Exception):
    __slots__ = ("code",)

    def __init__(self, code: int = -1, message: str = "") -> None:
        self.code = code
        super().__init__(message)


class MailerResult:
    __slots__ = ("to", "subject", "accepted", "error")

    def __init__(
        self,
        to: str,
        subject: str,
        accepted: bool,
        error: str = "",
    ) -> None:
        self.to = to
        self.subject = subject
        self.accepted = accepted
        self.error = error


class MailerBatch:
    __slots__ = ("results", "total", "accepted")

    def __init__(self, results: Optional[List[MailerResult]] = None) -> None:
        self.results = results or []
        self.total = len(self.results)
        self.accepted = sum(1 for r in self.results if r.accepted)
