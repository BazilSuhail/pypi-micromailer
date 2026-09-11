from __future__ import annotations
import base64
from typing import Any, Dict


def encode_base64(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def decode_base64(data: str) -> bytes:
    return base64.b64decode(data)


def render_template(template: str, context: Dict[str, Any]) -> str:
    return template.format_map(context)


def validate_html(html: str) -> list[str]:
    errors: list[str] = []
    tags: list[str] = []
    i = 0
    while i < len(html):
        if html[i] == "<":
            j = html.find(">", i + 1)
            if j == -1:
                errors.append("Unclosed tag")
                break
            tag_content = html[i + 1:j].strip()
            if not tag_content or tag_content.startswith("!"):
                i = j + 1
                continue
            parts = tag_content.split()
            tag_name = parts[0].lower()
            if tag_name.startswith("/"):
                if not tags:
                    errors.append(f"Unexpected closing tag </{tag_name[1:]}>")
                else:
                    expected = tags.pop()
                    if expected != tag_name[1:]:
                        errors.append(
                            f"Unexpected closing tag </{tag_name[1:]}> (expected </{expected}>)"
                        )
            elif tag_name not in (
                "meta",
                "link",
                "br",
                "hr",
                "img",
                "input",
                "col",
                "area",
                "base",
                "embed",
                "source",
                "track",
                "wbr",
            ):
                tags.append(tag_name)
            i = j + 1
        else:
            i += 1
    for tag in tags:
        errors.append(f"Unclosed tag <{tag}>")
    return errors
