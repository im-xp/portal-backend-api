from fastapi import status

from app.api.applications.models import Application
from app.api.applications.schemas import ApplicationStatus
from app.api.product_segments.models import (
    ApplicationProductSegment,
    ProductSegment,
    ProductSegmentProduct,
)
from app.core.config import settings


# -- Fixtures helpers --


def _create_segment(db_session, popup_city_id, name, slug, product_ids=None):
    segment = ProductSegment(
        name=name,
        slug=slug,
        popup_city_id=popup_city_id,
    )
    db_session.add(segment)
    db_session.flush()

    for pid in product_ids or []:
        db_session.add(
            ProductSegmentProduct(product_segment_id=segment.id, product_id=pid)
        )

    db_session.commit()
    return segment


def _assign_segments(db_session, application_id, segment_ids):
    for sid in segment_ids:
        db_session.add(
            ApplicationProductSegment(
                application_id=application_id, product_segment_id=sid
            )
        )
    db_session.commit()


# =========================================================================
# GET /product-segments/ tests
# =========================================================================


def test_get_product_segments_success(
    client, db_session, test_popup_city, test_products
):
    _create_segment(
        db_session, test_popup_city.id, 'Segment A', 'segment-a', [test_products[0].id]
    )

    response = client.get(
        '/product-segments/',
        params={'popup_city_slug': test_popup_city.slug},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Segment A'
    assert data[0]['slug'] == 'segment-a'
    assert len(data[0]['products']) == 1
    assert data[0]['products'][0]['id'] == test_products[0].id


def test_get_product_segments_filters_by_popup(
    client, db_session, test_popup_city, test_products
):
    from app.api.popup_city.models import PopUpCity

    other_popup = PopUpCity(
        id=2,
        name='Other City',
        slug='other-city',
        prefix='OC',
        location='Other',
        requires_approval=True,
    )
    db_session.add(other_popup)
    db_session.commit()

    _create_segment(db_session, test_popup_city.id, 'Seg A', 'seg-a')
    _create_segment(db_session, other_popup.id, 'Seg B', 'seg-b')

    response = client.get(
        '/product-segments/',
        params={'popup_city_slug': test_popup_city.slug},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['slug'] == 'seg-a'


def test_get_product_segments_invalid_api_key(client):
    response = client.get(
        '/product-segments/',
        headers={'x-api-key': 'invalid'},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_product_segments_empty(client, test_popup_city):
    response = client.get(
        '/product-segments/',
        params={'popup_city_slug': test_popup_city.slug},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


# =========================================================================
# PATCH /applications/{id}/review with segment_slugs
# =========================================================================


def test_review_accept_with_single_segment(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    seg = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['status'] == ApplicationStatus.ACCEPTED.value
    assert data['product_segment_ids'] == [seg.id]


def test_review_accept_with_multiple_segments(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    seg1 = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )
    seg2 = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'Builder',
        'builder',
        [test_products[1].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip', 'builder'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert set(data['product_segment_ids']) == {seg1.id, seg2.id}


def test_review_accept_with_segments_and_coordinator_notes(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    seg = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip'],
            'coordinator_notes': 'Offer VIP intro on arrival',
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['product_segment_ids'] == [seg.id]
    assert 'coordinator_notes' not in data

    application = db_session.get(Application, app_id)
    assert application.coordinator_notes == 'Offer VIP intro on arrival'


def test_review_accept_requires_segments_when_popup_has_segments(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.ACCEPTED.value, 'discount_assigned': 0},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'segment_slugs is required' in response.json()['detail']


def test_review_accept_without_segments_when_popup_has_no_segments(
    client,
    auth_headers,
    test_application,
    mock_email_template,
    mock_send_mail,
):
    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.ACCEPTED.value, 'discount_assigned': 0},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['product_segment_ids'] == []


def test_review_accept_with_invalid_segment_slug(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['nonexistent'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'not found' in response.json()['detail']


def test_review_accept_with_one_valid_one_invalid_slug(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip', 'nonexistent'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'not found' in response.json()['detail']


def test_review_accept_with_duplicate_segment_slugs_deduplicates_cleanly(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    seg = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    response = client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip', 'vip'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['product_segment_ids'] == [seg.id]


def test_review_reject_ignores_segment_slugs(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    # Rejecting should work even when popup has segments and no segment_slugs is given
    response = client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.REJECTED.value},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.REJECTED.value


def test_review_reject_clears_segments(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    """Rejecting a previously-accepted application must clear product segments."""
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    # Accept with segment
    client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    # Now reject
    response = client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.REJECTED.value},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['product_segment_ids'] == []


def test_review_reaccept_resets_stale_segments(
    client,
    auth_headers,
    test_application,
    db_session,
    test_products,
    mock_email_template,
    mock_send_mail,
):
    """Re-accepting after segments are removed must not keep the old segments."""
    _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    create_resp = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    app_id = create_resp.json()['id']

    # Accept with segment
    client.patch(
        f'/applications/{app_id}/review',
        json={
            'status': ApplicationStatus.ACCEPTED.value,
            'discount_assigned': 0,
            'segment_slugs': ['vip'],
        },
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    # Reject
    client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.REJECTED.value},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    # Remove all segments from the popup
    db_session.query(ApplicationProductSegment).delete()
    db_session.query(ProductSegmentProduct).delete()
    db_session.query(ProductSegment).delete()
    db_session.commit()

    # Re-accept without segment (popup now has no segments)
    response = client.patch(
        f'/applications/{app_id}/review',
        json={'status': ApplicationStatus.ACCEPTED.value, 'discount_assigned': 0},
        headers={'x-api-key': settings.APPLICATION_REVIEW_API_KEY},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['product_segment_ids'] == []


def test_create_application_cannot_set_product_segment_ids(
    client, auth_headers, test_application, db_session, test_products
):
    """Users must not be able to self-assign product_segment_ids on creation."""
    seg = _create_segment(
        db_session,
        test_application['popup_city_id'],
        'VIP',
        'vip',
        [test_products[0].id],
    )

    payload = {**test_application, 'product_segment_ids': [seg.id]}
    response = client.post('/applications/', json=payload, headers=auth_headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['product_segment_ids'] == []


# =========================================================================
# GET /products/ — segment filtering
# =========================================================================


def test_get_products_filtered_by_single_segment(
    client, db_session, test_citizen, test_popup_city, test_products, auth_headers
):
    product1, product2 = test_products
    seg = _create_segment(db_session, test_popup_city.id, 'VIP', 'vip', [product1.id])

    # Create application with segment assigned
    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()
    _assign_segments(db_session, application.id, [seg.id])

    response = client.get(
        '/products/',
        params={'popup_city_id': test_popup_city.id},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    product_ids = [p['id'] for p in data]
    assert product1.id in product_ids
    assert product2.id not in product_ids


def test_get_products_filtered_by_multiple_segments(
    client, db_session, test_citizen, test_popup_city, test_products, auth_headers
):
    product1, product2 = test_products
    seg1 = _create_segment(db_session, test_popup_city.id, 'VIP', 'vip', [product1.id])
    seg2 = _create_segment(
        db_session, test_popup_city.id, 'Builder', 'builder', [product2.id]
    )

    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()
    _assign_segments(db_session, application.id, [seg1.id, seg2.id])

    response = client.get(
        '/products/',
        params={'popup_city_id': test_popup_city.id},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    product_ids = [p['id'] for p in data]
    # Both products should be visible (union of both segments)
    assert product1.id in product_ids
    assert product2.id in product_ids


def test_get_products_no_segment_returns_all(
    client, db_session, test_citizen, test_popup_city, test_products, auth_headers
):
    product1, product2 = test_products

    # Create application without segment
    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.commit()

    response = client.get(
        '/products/',
        params={'popup_city_id': test_popup_city.id},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    product_ids = [p['id'] for p in data]
    assert product1.id in product_ids
    assert product2.id in product_ids


# =========================================================================
# Payment validation — segment enforcement
# =========================================================================


def test_payment_rejects_product_outside_segment(
    client,
    db_session,
    test_citizen,
    test_popup_city,
    test_products,
    auth_headers,
    mock_create_payment,
):
    from app.api.attendees.models import Attendee

    product1, product2 = test_products
    seg = _create_segment(db_session, test_popup_city.id, 'VIP', 'vip', [product1.id])

    # Create application with segment
    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()
    _assign_segments(db_session, application.id, [seg.id])

    attendee = Attendee(
        application_id=application.id,
        name='Test Attendee',
        category='main',
        email=test_citizen.primary_email,
        check_in_code='TEST999',
    )
    db_session.add(attendee)
    db_session.commit()

    # Try to buy product2 which is NOT in the segment
    response = client.post(
        '/payments/',
        json={
            'application_id': application.id,
            'products': [
                {
                    'product_id': product2.id,
                    'attendee_id': attendee.id,
                    'quantity': 1,
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'segment' in response.json()['detail'].lower()


def test_payment_allows_product_in_segment(
    client,
    db_session,
    test_citizen,
    test_popup_city,
    test_products,
    auth_headers,
    mock_create_payment,
):
    from app.api.attendees.models import Attendee

    product1, product2 = test_products
    seg = _create_segment(db_session, test_popup_city.id, 'VIP', 'vip', [product1.id])

    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()
    _assign_segments(db_session, application.id, [seg.id])

    attendee = Attendee(
        application_id=application.id,
        name='Test Attendee',
        category='main',
        email=test_citizen.primary_email,
        check_in_code='TEST888',
    )
    db_session.add(attendee)
    db_session.commit()

    # Buy product1 which IS in the segment
    response = client.post(
        '/payments/',
        json={
            'application_id': application.id,
            'products': [
                {
                    'product_id': product1.id,
                    'attendee_id': attendee.id,
                    'quantity': 1,
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK


def test_payment_allows_product_in_any_of_multiple_segments(
    client,
    db_session,
    test_citizen,
    test_popup_city,
    test_products,
    auth_headers,
    mock_create_payment,
):
    from app.api.attendees.models import Attendee

    product1, product2 = test_products
    seg1 = _create_segment(db_session, test_popup_city.id, 'VIP', 'vip', [product1.id])
    seg2 = _create_segment(
        db_session, test_popup_city.id, 'Builder', 'builder', [product2.id]
    )

    application = Application(
        first_name='Test',
        last_name='User',
        email=test_citizen.primary_email,
        citizen_id=test_citizen.id,
        popup_city_id=test_popup_city.id,
        _status=ApplicationStatus.ACCEPTED.value,
    )
    db_session.add(application)
    db_session.flush()
    _assign_segments(db_session, application.id, [seg1.id, seg2.id])

    attendee = Attendee(
        application_id=application.id,
        name='Test Attendee',
        category='main',
        email=test_citizen.primary_email,
        check_in_code='TEST777',
    )
    db_session.add(attendee)
    db_session.commit()

    # Buy both products — each is in a different segment but both are allowed
    response = client.post(
        '/payments/',
        json={
            'application_id': application.id,
            'products': [
                {
                    'product_id': product1.id,
                    'attendee_id': attendee.id,
                    'quantity': 1,
                },
                {
                    'product_id': product2.id,
                    'attendee_id': attendee.id,
                    'quantity': 1,
                },
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
