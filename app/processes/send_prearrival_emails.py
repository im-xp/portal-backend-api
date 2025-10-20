import time
from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.attendees.models import Attendee
from app.api.email_logs.crud import email_log as email_log_crud
from app.api.email_logs.models import EmailLog
from app.api.email_logs.schemas import EmailAttachment, EmailEvent
from app.api.popup_city.models import PopUpCity
from app.core import models  # noqa: F401
from app.core.config import Environment, settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.core.qr_generator import generate_qr_code_base64
from app.core.utils import current_time

POPUP_CITY_SLUG = 'edge-patagonia'
DAYS_BEFORE_START = 5


def generate_qr_attachment(check_in_code: str, attendee_name: str):
    """Generate a modern, styled QR code attachment for an attendee."""
    logger.info('Generating QR code for %s %s', check_in_code, attendee_name)
    return EmailAttachment(
        name=f'{attendee_name}.png',
        content_id='cid:qr.png',
        content=generate_qr_code_base64(check_in_code, attendee_name),
        content_type='image/png',
    )


def generate_qr_attachments(attendees: List[Attendee]):
    """Generate QR code attachments for all attendees with products."""
    attachments = []
    for attendee in attendees:
        if attendee.products:
            qr = generate_qr_attachment(attendee.check_in_code, attendee.name)
            attachments.append(qr)
    return attachments


def get_earliest_start_date(application: Application):
    """
    Get the earliest start date from all products across all attendees.
    Fallback to popup city start date if no product has a start date.
    """
    earliest_date = None
    for attendee in application.attendees:
        for product in attendee.products:
            if product.start_date:
                if not earliest_date or product.start_date < earliest_date:
                    earliest_date = product.start_date

    if not earliest_date:
        # Fallback to popup city start date
        earliest_date = application.popup_city.start_date

    return earliest_date


def get_sent_prearrival_emails(db: Session) -> List[str]:
    """Get list of application emails that have already received pre-arrival emails."""
    logs = (
        db.query(EmailLog.receiver_email.distinct())
        .filter(EmailLog.event == EmailEvent.PRE_ARRIVAL.value)
        .all()
    )
    return [log[0] for log in logs]


def get_applications_for_prearrival(db: Session):
    """
    Get applications that need to receive pre-arrival emails.

    Criteria:
    - From Edge Patagonia (popup_city slug == 'edge-patagonia')
    - Has attendees with products
    - Earliest product start date is 5 days or less away
    - Haven't received pre-arrival email yet (deduplication handled by exclusion list)
    """
    excluded_emails = get_sent_prearrival_emails(db)
    logger.info('Excluded application emails: %s', excluded_emails)

    today = current_time()
    target_date = today + timedelta(days=DAYS_BEFORE_START)

    # Get all applications from Edge Patagonia with attendees that have products
    applications = (
        db.query(Application)
        .join(Application.popup_city)
        .join(Application.attendees)
        .join(Attendee.products)
        .filter(
            PopUpCity.slug == POPUP_CITY_SLUG,
            Application.email.notin_(excluded_emails),
        )
        .distinct()
        .all()
    )

    logger.info('Applications before filter: %s', len(applications))

    # Filter to only include applications where the earliest start date
    # is 5 days or less away
    filtered_applications = []
    for application in applications:
        earliest_date = get_earliest_start_date(application)
        logger.info(
            'Earliest date for application %s %s: %s',
            application.id,
            application.email,
            earliest_date.strftime('%Y-%m-%d'),
        )
        if not earliest_date:
            logger.error('No earliest date for application %s', application.id)
            continue

        # Check if earliest start date is at most 5 days away
        if earliest_date <= target_date:
            logger.info('Application %s is 5 days or less away', application.id)
            filtered_applications.append(application)

    logger.info('Total applications found: %s', len(filtered_applications))
    logger.info('Emails: %s', [a.email for a in filtered_applications])
    logger.info(
        'Applications ids to process: %s', [a.id for a in filtered_applications]
    )

    return filtered_applications


def process_application_for_prearrival(application: Application):
    """Send pre-arrival email to application with QR codes for all attendees."""
    logger.info('Processing application %s %s', application.id, application.email)

    attachments = generate_qr_attachments(application.attendees)

    params = {
        'first_name': application.first_name,
    }

    logger.info('Sending pre-arrival email to %s', application.email)

    email_log_crud.send_mail(
        receiver_mail=application.email,
        event=EmailEvent.PRE_ARRIVAL.value,
        popup_city=application.popup_city,
        params=params,
        entity_type='application',
        entity_id=application.id,
        attachments=attachments,
    )


def send_prearrival_emails(db: Session):
    """Main function to process and send pre-arrival emails."""
    logger.info('Starting pre-arrival email process')
    applications = get_applications_for_prearrival(db)
    logger.info('Total applications to process: %s', len(applications))

    for application in applications:
        try:
            process_application_for_prearrival(application)
        except Exception as e:
            logger.error('Error processing application %s: %s', application.id, str(e))
            continue

    logger.info('Finished pre-arrival email process')


def main():
    if settings.ENVIRONMENT != Environment.PRODUCTION:
        logger.info(
            'Not running pre-arrival email process in %s environment',
            settings.ENVIRONMENT,
        )
        logger.info('Sleeping for 10 hours...')
        time.sleep(10 * 60 * 60)
        return

    with SessionLocal() as db:
        send_prearrival_emails(db)
    logger.info('Pre-arrival email process completed')


if __name__ == '__main__':
    main()
