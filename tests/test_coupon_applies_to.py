"""Regression tests for coupon `applies_to` field at /payments/preview.

Bug context: coupon_codes have an `applies_to` column with values 'pass',
'lodging', or 'all'. The frontend (portal-frontend TotalStrategy.ts) honors
this field when computing the displayed discount. The backend, however,
hard-codes lodging as non-discountable in `_classify_products`, so the
amount sent to Stripe at checkout was always the un-discounted lodging
price even when the coupon's `applies_to` said otherwise. The result: the
displayed price on EdgeOS looked discounted, but the charge wasn't.

These tests pin the backend behavior at /payments/preview so the discounted
amount returned matches what `applies_to` says it should be.
"""

from datetime import timedelta

import pytest
from fastapi import status

from app.api.applications.models import Application
from app.api.applications.schemas import ApplicationStatus
from app.api.attendees.models import Attendee
from app.api.coupon_codes.models import CouponCode
from app.api.products.models import Product
from app.core.utils import current_time


# ----------------------------------------------------------------------------
# Fixtures isolated to this module (so the existing test_products / test_coupon
# fixtures keep their categories/values and we don't touch other tests).
# ----------------------------------------------------------------------------


@pytest.fixture
def pass_and_lodging_products(db_session, test_popup_city):
    """A discountable pass product ($100) and a lodging product ($200)."""
    pass_product = Product(
        id=101,
        name='Test Entry Pass',
        slug='test-entry-pass',
        description='Discountable pass',
        price=100.0,
        category='week',
        popup_city_id=test_popup_city.id,
        is_active=True,
    )
    lodging_product = Product(
        id=102,
        name='Test Lodging',
        slug='test-lodging',
        description='Lodging product',
        price=200.0,
        category='lodging',
        popup_city_id=test_popup_city.id,
        is_active=True,
    )
    db_session.add_all([pass_product, lodging_product])
    db_session.commit()
    return pass_product, lodging_product


@pytest.fixture
def accepted_application(db_session, test_citizen, test_popup_city):
    """An ACCEPTED application + a main attendee, ready to receive a payment."""
    application = Application(
        id=501,
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()

    attendee = Attendee(
        id=601,
        application_id=application.id,
        name='Main Attendee',
        category='main',
        email=test_citizen.primary_email,
        check_in_code='APPLIES-TO-1',
    )
    db_session.add(attendee)
    db_session.commit()
    return application, attendee


def _make_coupon(db_session, popup_city_id, *, applies_to, discount_value=10.0):
    coupon = CouponCode(
        code=f'APPLIES{applies_to.upper()}',
        popup_city_id=popup_city_id,
        discount_value=discount_value,
        applies_to=applies_to,
        max_uses=100,
        current_uses=0,
        is_active=True,
        start_date=current_time() - timedelta(days=1),
        end_date=current_time() + timedelta(days=1),
    )
    db_session.add(coupon)
    db_session.commit()
    return coupon


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_preview_applies_to_pass_only_discounts_pass(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='pass': pass discounted, lodging full price (current behavior).

    Cart = pass $100 + lodging $200, 10% coupon.
    Expected amount = 90 + 200 = 290.
    """
    pass_product, lodging_product = pass_and_lodging_products
    application, attendee = accepted_application
    coupon = _make_coupon(db_session, test_popup_city.id, applies_to='pass')

    payload = {
        'application_id': application.id,
        'coupon_code': coupon.code,
        'products': [
            {'product_id': pass_product.id, 'attendee_id': attendee.id, 'quantity': 1},
            {'product_id': lodging_product.id, 'attendee_id': attendee.id, 'quantity': 1},
        ],
    }
    response = client.post('/payments/preview', json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['amount'] == pytest.approx(290.0)
    assert data['original_amount'] == pytest.approx(300.0)
    assert data['coupon_code'] == coupon.code
    assert data['discount_value'] == pytest.approx(10.0)


def test_preview_applies_to_lodging_discounts_pass_and_lodging(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='lodging': lodging joins the discountable bucket; passes were
    already discountable. Both discount.

    This mirrors the frontend (portal-frontend/src/strategies/TotalStrategy.ts)
    where `applies_to` only controls whether lodging is INCLUDED in the
    discountable filter — it never excludes passes. The bug being fixed is
    that the backend ignored applies_to entirely; the goal is to make the
    backend match what EdgeOS already displays to users.

    Cart = pass $100 + lodging $200, 10% coupon.
    Expected amount = 90 + 180 = 270 (same as applies_to='all' for this cart).
    """
    pass_product, lodging_product = pass_and_lodging_products
    application, attendee = accepted_application
    coupon = _make_coupon(db_session, test_popup_city.id, applies_to='lodging')

    payload = {
        'application_id': application.id,
        'coupon_code': coupon.code,
        'products': [
            {'product_id': pass_product.id, 'attendee_id': attendee.id, 'quantity': 1},
            {'product_id': lodging_product.id, 'attendee_id': attendee.id, 'quantity': 1},
        ],
    }
    response = client.post('/payments/preview', json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['amount'] == pytest.approx(270.0)
    assert data['original_amount'] == pytest.approx(300.0)
    assert data['coupon_code'] == coupon.code


def test_preview_applies_to_all_discounts_everything(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='all': both pass and lodging discounted.

    Cart = pass $100 + lodging $200, 10% coupon.
    Expected amount = 90 + 180 = 270.
    """
    pass_product, lodging_product = pass_and_lodging_products
    application, attendee = accepted_application
    coupon = _make_coupon(db_session, test_popup_city.id, applies_to='all')

    payload = {
        'application_id': application.id,
        'coupon_code': coupon.code,
        'products': [
            {'product_id': pass_product.id, 'attendee_id': attendee.id, 'quantity': 1},
            {'product_id': lodging_product.id, 'attendee_id': attendee.id, 'quantity': 1},
        ],
    }
    response = client.post('/payments/preview', json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['amount'] == pytest.approx(270.0)
    assert data['original_amount'] == pytest.approx(300.0)
    assert data['coupon_code'] == coupon.code


def test_preview_applies_to_lodging_no_lodging_in_cart_still_discounts_pass(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='lodging' with only a pass in cart.

    Per frontend semantics (TotalStrategy.ts) `applies_to` only controls
    whether lodging is included — passes are always discountable. So a
    lodging-scoped coupon still discounts a pass when no lodging is present.

    Cart = pass $100, 10% lodging-scoped coupon.
    Expected amount = 90.
    """
    pass_product, _ = pass_and_lodging_products
    application, attendee = accepted_application
    coupon = _make_coupon(db_session, test_popup_city.id, applies_to='lodging')

    payload = {
        'application_id': application.id,
        'coupon_code': coupon.code,
        'products': [
            {'product_id': pass_product.id, 'attendee_id': attendee.id, 'quantity': 1},
        ],
    }
    response = client.post('/payments/preview', json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['amount'] == pytest.approx(90.0)
    assert data['original_amount'] == pytest.approx(100.0)
    assert data['coupon_code'] == coupon.code
