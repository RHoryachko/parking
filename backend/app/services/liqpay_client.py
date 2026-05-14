"""Minimal LiqPay checkout signing (compatible with liqpay.ua sandbox / prod keys)."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from decimal import Decimal
from typing import Any

import requests

logger = logging.getLogger(__name__)

LIQPAY_CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout/"


def _signature(private_key: str, data_b64: str) -> str:
    raw = private_key + data_b64 + private_key
    return base64.b64encode(hashlib.sha1(raw.encode("utf-8")).digest()).decode("ascii")


def verify_callback_signature(*, private_key: str, data_b64: str, signature: str) -> bool:
    return _signature(private_key, data_b64) == signature


def encode_checkout_request(*, private_key: str, payload: dict[str, Any]) -> tuple[str, str]:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    data_b64 = base64.b64encode(body).decode("ascii")
    return data_b64, _signature(private_key, data_b64)


def request_checkout_redirect_url(
    *,
    public_key: str,
    private_key: str,
    amount: Decimal,
    order_id: str,
    description: str,
    server_url: str,
    result_url: str,
) -> str:
    payload: dict[str, Any] = {
        "version": 3,
        "public_key": public_key,
        "action": "pay",
        "amount": float(amount.quantize(Decimal("0.01"))),
        "currency": "UAH",
        "description": description[:255],
        "order_id": order_id,
        "server_url": server_url,
        "result_url": result_url,
        "language": "uk",
    }
    data_b64, sig = encode_checkout_request(private_key=private_key, payload=payload)
    try:
        resp = requests.post(
            LIQPAY_CHECKOUT_URL,
            data={"data": data_b64, "signature": sig},
            timeout=45,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        logger.warning("LiqPay request failed: %s", exc)
        raise RuntimeError("LiqPay network error") from exc
    if resp.status_code in (301, 302, 303, 307, 308):
        loc = (resp.headers.get("Location") or "").strip()
        if not loc:
            logger.warning("LiqPay redirect %s without Location", resp.status_code)
            raise RuntimeError("LiqPay checkout redirect without Location header")
        return loc
    if not resp.ok:
        logger.warning("LiqPay HTTP %s: %s", resp.status_code, resp.text[:500])
        raise RuntimeError(f"LiqPay HTTP {resp.status_code}")
    logger.warning("LiqPay unexpected %s response (no redirect)", resp.status_code)
    raise RuntimeError(f"LiqPay unexpected HTTP {resp.status_code}")
