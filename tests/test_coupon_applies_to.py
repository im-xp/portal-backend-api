"""Regression tests for coupon `applies_to` field at /payments/preview.

Bug context: coupon_codes have an `applies_to` column with values 'pass',
'lodging', or 'all'. Pre-fix, the backend ignored the field entirely and
treated lodging as non-discountable in all cases, so a coupon could not
actually discount lodging at checkout even when configured to.

These tests pin the backend behavior at /payments/preview under strict
scope semantics:

  - 'pass'    : only passes discount; lodging full price (legacy default)
  - 'lodging' : only lodging discounts; passes full price
  - 'all'     : both passes and lodging discount

portal-patron, donations, and the patreon/supporter buckets are never
discounted regardless of scope.
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


def test_preview_applies_to_lodging_discounts_lodging_only(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='lodging': only lodging discounts. The pass stays full price.

    Cart = pass $100 + lodging $200, 10% coupon.
    Expected amount = 100 + 180 = 280.
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
    assert data['amount'] == pytest.approx(280.0)
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


def test_preview_applies_to_lodging_no_lodging_in_cart_no_discount(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='lodging' with only a pass in cart: nothing in scope, no
    discount applied. The coupon is silently inert (response.amount equals
    the un-discounted total, no coupon code stamped on the response).

    Cart = pass $100, 10% lodging-scoped coupon.
    Expected amount = 100.
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
    assert data['amount'] == pytest.approx(100.0)
    assert data['original_amount'] == pytest.approx(100.0)
    # Coupon was out of scope, so it does not get stamped on the response.
    assert data.get('coupon_code') is None


def test_preview_applies_to_lodging_lodging_only_cart_discounts_lodging(
    client,
    auth_headers,
    db_session,
    test_popup_city,
    pass_and_lodging_products,
    accepted_application,
):
    """applies_to='lodging' with only lodging in cart: lodging discounts.

    Cart = lodging $200, 10% lodging-scoped coupon.
    Expected amount = 180.
    """
    _, lodging_product = pass_and_lodging_products
    application, attendee = accepted_application
    coupon = _make_coupon(db_session, test_popup_city.id, applies_to='lodging')

    payload = {
        'application_id': application.id,
        'coupon_code': coupon.code,
        'products': [
            {'product_id': lodging_product.id, 'attendee_id': attendee.id, 'quantity': 1},
        ],
    }
    response = client.post('/payments/preview', json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['amount'] == pytest.approx(180.0)
    assert data['original_amount'] == pytest.approx(200.0)
    assert data['coupon_code'] == coupon.code
