"""Thin wrapper around the Google Gen AI SDK (package: google-genai).

* Text-only and text+image (multimodal) prompts.
* Asks Gemini for JSON and parses it defensively.
* Tries the configured model first, then fallback models (Google retires model names often).
* Raises GeminiUnavailable for ANY failure so callers can fall back to the rule-based engine.
"""
import json
import re
from typing import Optional

from .config import get_settings


class GeminiUnavailable(Exception):
    """Gemini could not produce a usable answer (no key, network/quota error, bad JSON...)."""


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # last resort: grab the outermost {...}
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise GeminiUnavailable("Gemini did not return JSON.")
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError as exc:
            raise GeminiUnavailable(f"Gemini returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GeminiUnavailable("Gemini JSON was not an object.")
    return data


def is_configured() -> bool:
    return bool(get_settings().gemini_api_key)


def generate_json(prompt: str, image_bytes: Optional[bytes] = None, image_mime: Optional[str] = None) -> tuple[dict, str]:
    """Send a text (+ optional image) prompt. Returns (parsed_json, model_used)."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiUnavailable("GEMINI_API_KEY is not set.")
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # pragma: no cover
        raise GeminiUnavailable("google-genai is not installed.") from exc

    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=45_000))
    contents: list = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"))
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4)

    errors: list[str] = []
    for model in settings.gemini_models:
        try:
            resp = client.models.generate_content(model=model, contents=contents, config=config)
            return _parse_json(resp.text), model
        except GeminiUnavailable as exc:
            errors.append(f"{model}: {exc}")
        except Exception as exc:  # network, quota, 404 model not found, safety block, ...
            errors.append(f"{model}: {type(exc).__name__}: {str(exc)[:160]}")
    raise GeminiUnavailable("; ".join(errors) or "No Gemini model available.")
