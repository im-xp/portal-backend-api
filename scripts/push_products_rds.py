#!/usr/bin/env python3
"""
Push products directly to RDS (no confirmation prompt).
"""

import csv
import json
import os
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Direct connection - no app imports needed
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'edgeos_db')
DB_USER = os.environ.get('DB_USERNAME', 'myuser')
DB_PASS = os.environ.get('DB_PASSWORD', 'secret')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


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


def parse_datetime(val):
    if not val or val.strip() == '':
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None


def main():
    print(f'Connecting to: {DB_HOST}:{DB_PORT}/{DB_NAME}')

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get popup city ID
        result = session.execute(text('SELECT id, name FROM popups LIMIT 1')).fetchone()

        if not result:
            print('ERROR: No popup city found. Create one first.')
            return

        popup_city_id, popup_name = result
        print(f'Using popup city: {popup_name} (ID: {popup_city_id})')

        # Read products CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'products.csv')
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            products = list(reader)

        print(f'Found {len(products)} products to insert')

        inserted = 0
        skipped = 0

        for row in products:
            slug = row.get('slug')

            # Check if exists
            exists = session.execute(
                text(
                    'SELECT id FROM products WHERE slug = :slug AND popup_city_id = :popup_id'
                ),
                {'slug': slug, 'popup_id': popup_city_id},
            ).fetchone()

            if exists:
                print(f'  Skipping (exists): {slug}')
                skipped += 1
                continue

            # Insert
            session.execute(
                text("""
                INSERT INTO products (
                    name, slug, price, compare_price, popup_city_id,
                    description, category, attendee_category,
                    start_date, end_date, is_active, exclusive,
                    created_at, updated_at, created_by
                ) VALUES (
                    :name, :slug, :price, :compare_price, :popup_city_id,
                    :description, :category, :attendee_category,
                    :start_date, :end_date, :is_active, :exclusive,
                    NOW(), NOW(), 'system'
                )
                """),
                {
                    'name': row.get('name'),
                    'slug': slug,
                    'price': parse_float(row.get('price')),
                    'compare_price': parse_float(row.get('compare_price')),
                    'popup_city_id': popup_city_id,
                    'description': row.get('description') or None,
                    'category': row.get('category') or None,
                    'attendee_category': row.get('attendee_category') or None,
                    'start_date': parse_datetime(row.get('start_date')),
                    'end_date': parse_datetime(row.get('end_date')),
                    'is_active': parse_bool(row.get('is_active')),
                    'exclusive': parse_bool(row.get('exclusive')),
                },
            )
            print(f'  ✓ Inserted: {row.get("name")} ({slug})')
            inserted += 1

        session.commit()
        print(f'\nDone! Inserted: {inserted}, Skipped: {skipped}')

    except Exception as e:
        print(f'ERROR: {e}')
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
