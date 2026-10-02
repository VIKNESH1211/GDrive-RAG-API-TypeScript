from __future__ import annotations

import logging
import os
import random
import time

import requests

logger = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


class UpstreamError(Exception):
    """OpenAI could not be reached or kept failing after retries."""


def post_json(url: str, payload: dict, timeout: float, attempts: int = 3) -> dict:
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt == attempts:
                raise UpstreamError("OpenAI unreachable") from exc
            _backoff(attempt, None, f"network error ({type(exc).__name__})")
            continue

        if resp.status_code in RETRY_STATUS and attempt < attempts:
            _backoff(attempt, resp.headers.get("Retry-After"), f"HTTP {resp.status_code}")
            continue
        if resp.status_code >= 400:
            logger.error("OpenAI error %s: %s", resp.status_code, resp.text[:300])
            raise UpstreamError(f"OpenAI returned HTTP {resp.status_code}")
        return resp.json()
    raise UpstreamError("OpenAI request failed")  # pragma: no cover


def _backoff(attempt: int, retry_after: str | None, reason: str) -> None:
    try:
        delay = min(float(retry_after), 20.0) if retry_after else 0.0
    except ValueError:
        delay = 0.0
    delay = delay or (2 ** (attempt - 1)) + random.random()
    logger.warning("OpenAI %s, retrying in %.1fs (attempt %d)", reason, delay, attempt)
    time.sleep(delay)
