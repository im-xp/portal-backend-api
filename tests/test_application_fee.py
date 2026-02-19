import pytest
from fastapi import status

from app.api.applications.schemas import ApplicationStatus
from app.api.payments.models import Payment
from tests.conftest import get_auth_headers_for_citizen


@pytest.fixture
def fee_popup_city(test_popup_city, db_session):
    """Set application_fee on the test popup city."""
    test_popup_city.application_fee = 5.0
    db_session.commit()
    db_session.refresh(test_popup_city)
    return test_popup_city


@pytest.fixture
def draft_application(client, test_application, auth_headers, db_session):
    """Create a draft application."""
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


@pytest.fixture
def draft_application_with_fee(
    client, test_application, auth_headers, fee_popup_city, db_session
):
    """Create a draft application when fee is required (auto-forced to draft)."""
    app_data = {**test_application, 'status': 'in review'}
    response = client.post('/applications/', json=app_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['status'] == 'draft'
    return data


# --- Happy path tests ---


def test_create_application_fee_success(
    client,
    auth_headers,
    draft_application,
    fee_popup_city,
    mock_create_payment,
    db_session,
):
    """POST /payments/application-fee succeeds for draft app with fee configured."""
    response = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['application_id'] == draft_application['id']
    assert data['is_application_fee'] is True
    assert data['status'] == 'pending'
    assert data['external_id'] is not None
    assert data['checkout_url'] is not None
    assert data['amount'] == 5.0
    assert data['products_snapshot'] == []


def test_create_application_fee_cancels_pending(
    client,
    auth_headers,
    draft_application,
    fee_popup_city,
    mock_create_payment,
    db_session,
):
    """Creating a new fee payment cancels existing pending fee payments."""
    # Create first fee payment
    response1 = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response1.status_code == status.HTTP_200_OK
    first_payment_id = response1.json()['id']

    # Create second fee payment
    response2 = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response2.status_code == status.HTTP_200_OK
    second_payment_id = response2.json()['id']

    # Verify first payment was cancelled
    first_payment = db_session.get(Payment, first_payment_id)
    assert first_payment.status == 'cancelled'

    # Verify second payment is pending
    second_payment = db_session.get(Payment, second_payment_id)
    assert second_payment.status == 'pending'


# --- Rejection tests ---


def test_create_application_fee_not_draft(
    client,
    auth_headers,
    draft_application,
    fee_popup_city,
    db_session,
):
    """Reject if application is not in draft status."""
    from app.api.applications.models import Application

    application = db_session.get(Application, draft_application['id'])
    application.status = ApplicationStatus.ACCEPTED.value
    db_session.commit()

    response = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Application must be in draft status'


def test_create_application_fee_no_fee_configured(
    client,
    auth_headers,
    draft_application,
    db_session,
):
    """Reject if popup city has no application fee."""
    response = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()['detail']
        == 'This popup city does not require an application fee'
    )


def test_create_application_fee_already_paid(
    client,
    auth_headers,
    draft_application,
    fee_popup_city,
    mock_create_payment,
    db_session,
):
    """Reject if approved fee payment already exists."""
    # Create and manually approve a fee payment
    response = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    payment_id = response.json()['id']

    payment = db_session.get(Payment, payment_id)
    payment.status = 'approved'
    db_session.commit()

    # Try to create another fee payment
    response = client.post(
        '/payments/application-fee',
        json={'application_id': draft_application['id']},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Application fee has already been paid'


# --- Fee-before-submit gate tests ---


def test_submit_application_rejected_without_fee(
    client,
    auth_headers,
    draft_application_with_fee,
    fee_popup_city,
    db_session,
):
    """PUT /applications/{id} with status=in_review rejected when fee unpaid (402)."""
    response = client.put(
        f'/applications/{draft_application_with_fee["id"]}',
        json={'status': 'in review'},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
    assert response.json()['detail'] == 'Application fee must be paid before submitting'


def test_submit_application_succeeds_with_fee_paid(
    client,
    auth_headers,
    draft_application_with_fee,
    fee_popup_city,
    mock_create_payment,
    mock_email_template,
    db_session,
):
    """PUT /applications/{id} with status=in_review succeeds when fee paid."""
    # Create and approve fee payment
    app_id = draft_application_with_fee['id']
    response = client.post(
        '/payments/application-fee',
        json={'application_id': app_id},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    payment_id = response.json()['id']

    payment = db_session.get(Payment, payment_id)
    payment.status = 'approved'
    db_session.commit()

    # Now submit the application
    response = client.put(
        f'/applications/{app_id}',
        json={'status': 'in review'},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == 'in review'


def test_application_created_with_in_review_forced_to_draft_when_fee_required(
    client,
    auth_headers,
    fee_popup_city,
    test_citizen,
    db_session,
):
    """Application created with IN_REVIEW status forced to DRAFT when fee required."""
    app_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'citizen_id': test_citizen.id,
        'popup_city_id': fee_popup_city.id,
        'status': 'in review',
    }
    response = client.post(
        '/applications/',
        json=app_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['status'] == 'draft'
    assert response.json()['submitted_at'] is None


# --- Webhook integration test ---


def test_webhook_approves_fee_and_submits_application(
    client,
    auth_headers,
    draft_application,
    fee_popup_city,
    mock_create_payment,
    mock_simplefi_response,
    mock_webhook_cache,
    mock_email_template,
    db_session,
):
    """Webhook approval of fee payment transitions app to in_review."""
    app_id = draft_application['id']

    # Create fee payment
    response = client.post(
        '/payments/application-fee',
        json={'application_id': app_id},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    payment = response.json()

    # Simulate webhook approval
    webhook_data = {
        'id': 'test_fee_webhook',
        'event_type': 'new_payment',
        'entity_type': 'payment_request',
        'entity_id': payment['external_id'],
        'data': {
            'payment_request': {
                'id': mock_simplefi_response['id'],
                'order_id': 1,
                'amount': 5.0,
                'amount_paid': 5.0,
                'currency': 'USD',
                'reference': {},
                'status': 'approved',
                'status_detail': 'correct',
                'transactions': [],
                'card_payment': None,
                'payments': [],
            },
            'new_payment': {
                'coin': 'USD',
                'hash': 'test_hash',
                'amount': 5.0,
                'paid_at': '2024-01-01T00:00:00Z',
            },
        },
    }

    response = client.post('/webhooks/simplefi', json=webhook_data)
    assert response.status_code == status.HTTP_200_OK

    # Verify payment was approved
    payment_response = client.get(f'/payments/{payment["id"]}', headers=auth_headers)
    assert payment_response.json()['status'] == 'approved'
    assert payment_response.json()['is_application_fee'] is True

    # Verify application was submitted (transitioned to in_review)
    from app.api.applications.models import Application

    application = db_session.get(Application, app_id)
    db_session.refresh(application)
    assert application.submitted_at is not None
    assert application.status == 'in review'


def test_submit_application_without_fee_no_gate(
    client,
    auth_headers,
    draft_application,
    mock_email_template,
    db_session,
):
    """Submitting application works normally when no fee is configured."""
    response = client.put(
        f'/applications/{draft_application["id"]}',
        json={'status': 'in review'},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == 'in review'
