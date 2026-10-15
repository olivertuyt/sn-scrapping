"""LLM structured extraction via Gemini REST or Anthropic-compatible Messages API.

Provider credentials and model settings come from environment (never hardcoded).
Uses only httpx (already a dependency) — no provider SDK needed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from urllib.parse import quote

import httpx

log = logging.getLogger("extract")

# Same corporate TLS-intercepting proxy as the crawler: use the Windows system
# CA store when truststore is available (see src/crawler.py for the evidence).
try:
    import ssl

    import truststore
    _SSL_CONTEXT: ssl.SSLContext | None = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
except ImportError:  # pragma: no cover
    _SSL_CONTEXT = None

_SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "05_extraction_system_prompt.txt")
_MAX_PAGES_PER_CALL = 6  # keep context bounded; top-ranked pages first
_GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        field: {
            "type": "object",
            "properties": {
                "value": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "null"},
                    ]
                },
                "status": {
                    "type": "string",
                    "enum": ["FOUND", "NOT_FOUND", "CONFLICT", "MULTIPLE_CANDIDATES"],
                },
                "source_url": {
                    "anyOf": [{"type": "string"}, {"type": "null"}]
                },
                "evidence": {
                    "anyOf": [{"type": "string"}, {"type": "null"}]
                },
            },
            "required": ["value", "status", "source_url", "evidence"],
        }
        for field in (
            "head_office_address",
            "representative",
            "capital",
            "established_year_month",
        )
    },
    "required": [
        "head_office_address",
        "representative",
        "capital",
        "established_year_month",
    ],
}


def _system_prompt() -> str:
    with open(_SYSTEM_PROMPT_FILE, encoding="utf-8") as f:
        return f.read()


def extract_company(company_name: str, pages: list[tuple[str, str]]) -> dict:
    """Call the LLM with top candidate pages; return raw JSON dict of 4 fields.

    pages: (url, cleaned_text) pairs, best candidates first (already truncated
    by the caller). Raises RuntimeError on unrecoverable API failure.
    """
    # Prefer Gemini when its key is configured; GOOGLE_API_KEY follows Google's
    # documented precedence over GEMINI_API_KEY when both are present.
    gemini_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    pages = pages[:_MAX_PAGES_PER_CALL]
    doc = "\n\n".join(f"=== URL: {url} ===\n{text[:6000]}" for url, text in pages)
    user_msg = f"会社名: {company_name}\n\n以下は公式サイトから取得したページ群です。\n\n{doc}"
    if gemini_key:
        return _extract_gemini(user_msg, gemini_key)

    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    model = os.environ.get("LLM_MODEL") or os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-5-5")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY or LLM_API_KEY to run extraction (see .env.example)")

    body = {
        "model": model,
        "max_tokens": 2000,
        "system": _system_prompt(),
        "messages": [{"role": "user", "content": user_msg}],
    }
    # OpenRouter-style tokens authenticate via Bearer; native Anthropic via x-api-key
    auth: dict[str, str] = {"content-type": "application/json", "anthropic-version": "2023-06-01"}
    if os.environ.get("ANTHROPIC_AUTH_TOKEN") and not os.environ.get("LLM_API_KEY"):
        auth["Authorization"] = f"Bearer {api_key}"
    else:
        auth["x-api-key"] = api_key
    delay = 2.0
    for attempt in range(3):
        try:
            r = httpx.post(f"{base_url}/v1/messages", json=body, headers=auth, timeout=60.0, verify=_SSL_CONTEXT or True)
            if r.status_code in (429, 500, 502, 503, 529):
                raise httpx.TransportError(f"retryable status {r.status_code}")
            if r.status_code != 200:
                raise RuntimeError(f"LLM API error {r.status_code}: {r.text[:300]}")
            # content may start with thinking/tool blocks; join the text ones
            text = _response_text(r.json())
            if not text:
                raise RuntimeError(f"LLM returned no text block: {r.text[:300]}")
            return _parse_json(text)
        except (httpx.TransportError, httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            if attempt >= 2:
                raise RuntimeError(f"LLM extraction failed after retries: {e}") from e
            log.warning("extract retry %s: %s", attempt + 1, e)
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def _extract_gemini(user_msg: str, api_key: str) -> dict:
    """Call Google's REST generateContent API with JSON structured output."""
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
    if not model:
        raise RuntimeError("GEMINI_MODEL must not be empty")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='-._')}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": _system_prompt()}]},
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {
            "maxOutputTokens": 2000,
            "responseFormat": {
                "text": {
                    "mimeType": "APPLICATION_JSON",
                    "schema": _GEMINI_RESPONSE_SCHEMA,
                }
            },
        },
    }
    headers = {"content-type": "application/json", "x-goog-api-key": api_key}
    delay = 2.0
    for attempt in range(3):
        try:
            response = httpx.post(
                url,
                json=body,
                headers=headers,
                timeout=60.0,
                verify=_SSL_CONTEXT or True,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                raise httpx.TransportError(f"retryable Gemini status {response.status_code}")
            if response.status_code != 200:
                raise RuntimeError(
                    f"Gemini API error {response.status_code}: {response.text[:300]}"
                )
            text = _gemini_response_text(response.json())
            if not text:
                raise RuntimeError("Gemini returned no text candidate")
            return _parse_json(text)
        except (httpx.TransportError, httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            if attempt >= 2:
                raise RuntimeError(f"Gemini extraction failed after retries: {e}") from e
            log.warning("Gemini extract retry %s: %s", attempt + 1, e)
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def _gemini_response_text(payload: dict) -> str:
    """Join visible text parts from Gemini's first response candidate."""
    candidates = payload.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
        and isinstance(part.get("text"), str)
        and not part.get("thought")
    )


def _response_text(payload: dict) -> str:
    """Join the text blocks of an Anthropic Messages response (thinking blocks first)."""
    return "".join(b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text")


def _parse_json(text: str) -> dict:
    """Parse the model's JSON, tolerating markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)
