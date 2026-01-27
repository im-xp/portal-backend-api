#!/usr/bin/env python3
"""
Push products from local CSV to NocoDB Cloud.

Usage:
    python scripts/push_products_to_cloud.py --token YOUR_TOKEN --popup-city-id 1
"""

import argparse
import csv
import os
import requests

NOCODB_BASE_URL = 'https://app.nocodb.com/api/v2'
PRODUCTS_TABLE_ID = 'mjt8xx9ltkhfcbu'


def parse_bool(val):
    if isinstance(val, bool):
        return val
    if val is None or val == '':
        return False
    return str(val).strip().lower() == 'true'


def parse_float(val):
    try:
        return float(val) if val not in (None, '', 'None') else None
    except Exception:
        return None


def read_products_csv(csv_path: str):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def push_product(token: str, product: dict):
    """Push a single product to NocoDB Cloud."""
    url = f'{NOCODB_BASE_URL}/tables/{PRODUCTS_TABLE_ID}/records'
    headers = {'xc-token': token, 'Content-Type': 'application/json'}

    response = requests.post(url, json=product, headers=headers)
    return response


def main():
    parser = argparse.ArgumentParser(description='Push products to NocoDB Cloud')
    parser.add_argument('--token', required=True, help='NocoDB API token')
    parser.add_argument(
        '--popup-city-name',
        default='The Portal at Iceland Eclipse (Pre-Approved)',
        help='Popup city name for linking',
    )
    parser.add_argument(
        '--dry-run', action='store_true', help='Print products without pushing'
    )
    args = parser.parse_args()

    csv_path = os.path.join(os.path.dirname(__file__), 'products.csv')
    rows = read_products_csv(csv_path)

    print(f'Found {len(rows)} products to push')

    success = 0
    failed = 0

    for row in rows:
        product = {
            'name': row.get('name'),
            'slug': row.get('slug'),
            'price': parse_float(row.get('price')),
            'compare_price': parse_float(row.get('compare_price')),
            # Use the linked record field name with display value
            'popups': args.popup_city_name,
            'description': row.get('description') or None,
            'category': row.get('category') or None,
            'attendee_category': row.get('attendee_category') or None,
            'start_date': row.get('start_date') or None,
            'end_date': row.get('end_date') or None,
            'is_active': parse_bool(row.get('is_active')),
            'exclusive': parse_bool(row.get('exclusive')),
        }

        # Remove None values (NocoDB doesn't like explicit nulls for some fields)
        product = {k: v for k, v in product.items() if v is not None}

        if args.dry_run:
            print(f'  Would push: {product["name"]} ({product["slug"]})')
            continue

        response = push_product(args.token, product)

        if response.status_code in (200, 201):
            print(f'  ✓ {product["name"]} ({product["slug"]})')
            success += 1
        else:
            print(f'  ✗ {product["name"]}: {response.status_code} - {response.text}')
            failed += 1

    if not args.dry_run:
        print(f'\nDone! {success} succeeded, {failed} failed')


if __name__ == '__main__':
    main()
