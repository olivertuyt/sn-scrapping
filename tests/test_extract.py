"""Tests for LLM response parsing (deterministic part of extract.py)."""

import json

import httpx
import pytest

from src.extract import _parse_json, _response_text, extract_company


def test_thinking_block_first():
    # OpenRouter sometimes returns a thinking block before the text block
    payload = {"content": [
        {"type": "thinking", "thinking": "…"},
        {"type": "text", "text": '{"a": 1}'},
    ]}
    assert _response_text(payload) == '{"a": 1}'


def test_response_no_text_blocks():
    assert _response_text({"content": [{"type": "tool_use"}]}) == ""


def test_plain_json():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_markdown_fences():
    assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_bare_fences():
    assert _parse_json('```\n{"a": 1}\n```') == {"a": 1}


def test_surrounding_whitespace():
    assert _parse_json('\n  {"a": 1}  \n') == {"a": 1}


def test_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        _parse_json("not json at all")


def test_gemini_extract_uses_structured_generate_content_api(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response_data = {
        "capital": {
            "value": "100億円",
            "status": "FOUND",
            "source_url": "https://example.jp/profile",
            "evidence": "資本金 100億円",
        }
    }
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, body=kwargs["json"], headers=kwargs["headers"], kwargs=kwargs)
        return httpx.Response(
            200,
            json={
                "candidates": [{
                    "content": {"parts": [
                        {"text": "not user-facing thought", "thought": True},
                        {"text": json.dumps(response_data, ensure_ascii=False)},
                    ]}
                }]
            },
        )

    monkeypatch.setattr("src.extract.httpx.post", fake_post)

    result = extract_company("Example", [("https://example.jp/profile", "資本金 100億円")])

    assert result == response_data
    assert request["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.1-flash-lite:generateContent"
    )
    assert request["headers"]["x-goog-api-key"] == "test-gemini-key"
    assert "test-gemini-key" not in request["url"]
    assert request["body"]["systemInstruction"]["parts"][0]["text"]
    assert "会社名: Example" in request["body"]["contents"][0]["parts"][0]["text"]
    assert request["body"]["generationConfig"]["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
