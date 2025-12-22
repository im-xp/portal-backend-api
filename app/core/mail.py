import requests

from app.api.email_logs.schemas import EmailAttachment, EmailStatus
from app.core.config import Environment, settings
from app.core.logger import logger


def send_mail(
    receiver_mail: str,
    *,
    template: str,
    params: dict,
    attachments: list[EmailAttachment] = None,
    from_address: str = None,
    from_name: str = None,
    reply_to: str = None,
):
    # Use provided values or fall back to global settings
    from_addr = from_address or settings.EMAIL_FROM_ADDRESS
    from_nm = from_name or settings.EMAIL_FROM_NAME
    reply = reply_to if reply_to is not None else settings.EMAIL_REPLY_TO

    logger.info('sending %s email to %s from %s', template, receiver_mail, from_addr)
    url = 'https://api.postmarkapp.com/email/withTemplate'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Postmark-Server-Token': settings.POSTMARK_API_TOKEN,
    }
    data = {
        'From': f'{from_nm} <{from_addr}>',
        'To': receiver_mail,
        'TemplateAlias': template,
        'TemplateModel': params,
    }
    if reply:
        data['ReplyTo'] = reply

    if attachments:
        data['Attachments'] = [a.model_dump(by_alias=True) for a in attachments]

    if settings.ENVIRONMENT == Environment.TEST:
        return {'status': EmailStatus.SUCCESS}

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    return {'status': EmailStatus.SUCCESS, 'response': response.json()}
