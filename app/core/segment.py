import os
import base64
from datetime import datetime, timezone
from typing import Any

import requests

from app.core.logger import logger

SEGMENT_WRITE_KEY = os.getenv('SEGMENT_WRITE_KEY', '')
SEGMENT_API_URL = 'https://api.segment.io/v1'


def _is_enabled() -> bool:
    return bool(SEGMENT_WRITE_KEY)


def _auth_header() -> dict[str, str]:
    encoded = base64.b64encode(f'{SEGMENT_WRITE_KEY}:'.encode()).decode()
    return {'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'}


def _post(endpoint: str, payload: dict[str, Any]) -> None:
    if not _is_enabled():
        return
    try:
        resp = requests.post(
            f'{SEGMENT_API_URL}/{endpoint}',
            json=payload,
            headers=_auth_header(),
            timeout=5,
        )
        if not resp.ok:
            logger.error('[Segment] %s failed: %s %s', endpoint, resp.status_code, resp.text)
    except Exception as e:
        logger.error('[Segment] %s error: %s', endpoint, e)


def identify(user_id: str, traits: dict[str, Any], timestamp: datetime | None = None) -> None:
    _post('identify', {
        'userId': user_id,
        'traits': traits,
        'timestamp': (timestamp or datetime.now(timezone.utc)).isoformat(),
    })


def track(user_id: str, event: str, properties: dict[str, Any], timestamp: datetime | None = None) -> None:
    _post('track', {
        'userId': user_id,
        'event': event,
        'properties': properties,
        'timestamp': (timestamp or datetime.now(timezone.utc)).isoformat(),
    })
