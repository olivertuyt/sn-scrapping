"""HTML cleaning: boilerplate removal for LLM extraction (generic, no site selectors)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_STRIP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "iframe", "svg", "form"]

_WS = re.compile(r"[ \t]+")


def clean_html(html: str) -> str:
    """Visible text of the page, one line per block, whitespace-squeezed."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()
    for t in soup.find_all(["br"]):
        t.replace_with("\n")
    text = soup.get_text("\n")
    lines = [_WS.sub(" ", ln).strip() for ln in text.splitlines()]
    # drop empty and nav-menu-like lines (short symbol/number-only)
    return "\n".join(ln for ln in lines if ln)
