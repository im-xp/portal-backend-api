"""
Quick test: send a test identify + Order Completed to Segment.
Verify events appear in Sources > EdgeOS Portal > Debugger.

Usage: python3 scripts/test_segment.py
"""

import base64
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

SEGMENT_WRITE_KEY = 'rgLWt318zoWFuHg78qRdEuEoWeHWHGu1'
SEGMENT_API_URL = 'https://api.segment.io/v1'
TEST_EMAIL = 'segment-test@icelandeclipse.com'


def post(endpoint, payload):
    encoded = base64.b64encode(f'{SEGMENT_WRITE_KEY}:'.encode()).decode()
    data = json.dumps(payload).encode()
    req = Request(
        f'{SEGMENT_API_URL}/{endpoint}',
        data=data,
        headers={'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'},
    )
    resp = urlopen(req)
    print(f'  {endpoint}: {resp.status}')


now = datetime.now(timezone.utc).isoformat()

print('Sending test identify...')
post('identify', {
    'userId': TEST_EMAIL,
    'traits': {
        'email': TEST_EMAIL,
        'first_name': 'Segment',
        'last_name': 'Test',
        'event': 'Iceland Eclipse',
        'application_status': 'accepted',
    },
    'timestamp': now,
})

print('Sending test Order Completed...')
post('track', {
    'userId': TEST_EMAIL,
    'event': 'Order Completed',
    'properties': {
        'order_id': 'test_0',
        'total': 99.99,
        'currency': 'USD',
        'products': [
            {'product_id': 0, 'name': 'Test Product', 'price': 99.99, 'quantity': 1},
        ],
    },
    'timestamp': now,
})

print('Done. Check Segment debugger for events from segment-test@icelandeclipse.com')
