"""Plate recognition via kie.ai OpenAI-compatible Gemini multimodal API."""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

import requests

logger = logging.getLogger(__name__)

PLATE_JSON_SCHEMA = {
    "name": "license_plate",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "plate_number": {
                "type": "string",
                "description": "Vehicle plate: uppercase Latin letters and digits only, no spaces or hyphens (UA style).",
            }
        },
        "required": ["plate_number"],
        "additionalProperties": False,
    },
}


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def recognize_plate_kie(
    *,
    api_key: str,
    chat_url: str,
    model: str,
    image_bytes: bytes,
    mime_type: str,
    timeout_sec: int = 90,
) -> str:
    """
    Send image to Gemini via kie; expect JSON {\"plate_number\": \"...\"} in assistant message.
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
    safe_mime = mime_type if "/" in mime_type else "image/jpeg"
    data_url = f"data:{safe_mime};base64,{b64}"

    body: dict[str, Any] = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You read a single vehicle license plate from the image. "
                            "Output JSON only with key plate_number: uppercase A-Z and 0-9, "
                            "no spaces or dashes (normalized). If unreadable, use empty string."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": PLATE_JSON_SCHEMA,
        },
    }

    try:
        resp = requests.post(
            chat_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout_sec,
        )
    except requests.RequestException as exc:
        logger.warning("kie.ai request failed: %s", exc)
        raise RuntimeError("Vision API network error") from exc

    if not resp.ok:
        logger.warning("kie.ai HTTP %s: %s", resp.status_code, resp.text[:800])
        raise RuntimeError(f"Vision API HTTP {resp.status_code}")

    try:
        payload = resp.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Vision API returned non-JSON") from exc

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Vision API: missing choices")

    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        texts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                t = part.get("text")
                if isinstance(t, str):
                    texts.append(t)
        content = "".join(texts) if texts else ""
    if not isinstance(content, str):
        raise RuntimeError("Vision API: unexpected message content")

    parsed = _extract_json_object(content)
    if not parsed:
        raise RuntimeError("Vision API: could not parse plate JSON")

    plate = parsed.get("plate_number") or parsed.get("plate") or parsed.get("response")
    if plate is None:
        raise RuntimeError("Vision API: no plate_number in JSON")

    return str(plate).strip()
