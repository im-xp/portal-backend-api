#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from email.utils import formataddr
from typing import Iterable

import requests
from dotenv import load_dotenv

POSTMARK_URL = 'https://api.postmarkapp.com/email/withTemplate'
DEFAULT_ALIAS = 'iceland-volunteer-invitation'
DEFAULT_RECIPIENT = 'francisco@muvinai.com'
DEFAULT_FROM_ADDRESS = 'test@icelandeclipse.com'
DEFAULT_FROM_NAME = 'Iceland Eclipse'
DEFAULT_CONFIRMATION_LINK = 'https://example.com/iceland-volunteer-confirmation'


@dataclass(frozen=True)
class ApprovedPhase:
    name: str
    arrival_date: str
    work_requirement: str
    accommodation: str
    meals: str
    latest_arrival_date: str


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    deposit_mode: str
    approved_phases: list[ApprovedPhase]


SINGLE_PHASES = [
    ApprovedPhase(
        name='Arrival and Build Phase',
        arrival_date='July 27, 2026',
        work_requirement='4 volunteer shifts',
        accommodation='Shared volunteer housing',
        meals='Breakfast and dinner provided',
        latest_arrival_date='July 26, 2026',
    )
]

MULTI_PHASES = [
    ApprovedPhase(
        name='Arrival and Build Phase',
        arrival_date='July 27, 2026',
        work_requirement='4 volunteer shifts',
        accommodation='Shared volunteer housing',
        meals='Breakfast and dinner provided',
        latest_arrival_date='July 26, 2026',
    ),
    ApprovedPhase(
        name='Event Operations Phase',
        arrival_date='August 2, 2026',
        work_requirement='3 volunteer shifts',
        accommodation='Shared volunteer housing',
        meals='Breakfast and dinner provided',
        latest_arrival_date='August 1, 2026',
    ),
]

ALL_VARIANTS = [
    Variant(
        key='single-deposit',
        label='Single phase / refundable deposit',
        deposit_mode='pay_refundable_deposit',
        approved_phases=SINGLE_PHASES,
    ),
    Variant(
        key='single-waived',
        label='Single phase / deposit waived',
        deposit_mode='waived',
        approved_phases=SINGLE_PHASES,
    ),
    Variant(
        key='single-ticketholder',
        label='Single phase / ticketholder',
        deposit_mode='ticketholder',
        approved_phases=SINGLE_PHASES,
    ),
    Variant(
        key='multi-deposit',
        label='Multiple phases / refundable deposit',
        deposit_mode='pay_refundable_deposit',
        approved_phases=MULTI_PHASES,
    ),
    Variant(
        key='multi-waived',
        label='Multiple phases / deposit waived',
        deposit_mode='waived',
        approved_phases=MULTI_PHASES,
    ),
    Variant(
        key='multi-ticketholder',
        label='Multiple phases / ticketholder',
        deposit_mode='ticketholder',
        approved_phases=MULTI_PHASES,
    ),
]


def build_template_model(
    *,
    first_name: str,
    confirmation_link: str,
    deposit_amount: int,
    variant: Variant,
) -> dict:
    approved_phases = [asdict(phase) for phase in variant.approved_phases]
    approved_phase_names = ', '.join(phase['name'] for phase in approved_phases)
    deposit_mode = variant.deposit_mode

    model = {
        'first_name': first_name,
        'discount_assigned': 0,
        'confirmation_form_link': confirmation_link,
        'deposit_amount': deposit_amount,
        'approved_phases': approved_phases,
        'approved_phase_count': len(approved_phases),
        'approved_phase_names': approved_phase_names,
        'has_single_approved_phase': len(approved_phases) == 1,
        'has_multiple_approved_phases': len(approved_phases) > 1,
        'requires_refundable_deposit': deposit_mode == 'pay_refundable_deposit',
        'deposit_waived': deposit_mode == 'waived',
        'ticket_holder_credit': deposit_mode == 'ticketholder',
    }
    if len(approved_phases) == 1:
        model['single_phase'] = approved_phases[0]
    return model


def get_variants(selected_keys: Iterable[str]) -> list[Variant]:
    if not selected_keys:
        return ALL_VARIANTS
    selected = set(selected_keys)
    variants = [variant for variant in ALL_VARIANTS if variant.key in selected]
    missing = selected - {variant.key for variant in variants}
    if missing:
        raise ValueError(f'Unknown variant(s): {", ".join(sorted(missing))}')
    return variants


def build_payload(
    *,
    recipient: str,
    alias: str,
    from_address: str,
    from_name: str,
    reply_to: str | None,
    model: dict,
) -> dict:
    payload = {
        'From': formataddr((from_name, from_address)),
        'To': recipient,
        'TemplateAlias': alias,
        'TemplateModel': model,
    }
    if reply_to:
        payload['ReplyTo'] = reply_to
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Send Iceland volunteer invitation template variants via Postmark.'
    )
    parser.add_argument(
        '--recipient',
        default=os.getenv('ICELAND_TEST_RECIPIENT', DEFAULT_RECIPIENT),
        help='Recipient email address.',
    )
    parser.add_argument(
        '--alias',
        default=os.getenv('POSTMARK_TEMPLATE_ALIAS', DEFAULT_ALIAS),
        help='Postmark template alias.',
    )
    parser.add_argument(
        '--from-address',
        default=os.getenv('EMAIL_FROM_ADDRESS', DEFAULT_FROM_ADDRESS),
        help='From email address.',
    )
    parser.add_argument(
        '--from-name',
        default=os.getenv('EMAIL_FROM_NAME', DEFAULT_FROM_NAME),
        help='From display name.',
    )
    parser.add_argument(
        '--reply-to',
        default=os.getenv('EMAIL_REPLY_TO'),
        help='Optional reply-to email address.',
    )
    parser.add_argument(
        '--first-name',
        default=os.getenv('ICELAND_TEST_FIRST_NAME', 'Francisco'),
        help='First name used inside the template model.',
    )
    parser.add_argument(
        '--confirmation-link',
        default=os.getenv(
            'ICELAND_VOLUNTEER_CONFIRMATION_LINK',
            DEFAULT_CONFIRMATION_LINK,
        ),
        help='Confirmation form link inserted into each email.',
    )
    parser.add_argument(
        '--deposit-amount',
        type=int,
        default=int(os.getenv('ICELAND_VOLUNTEER_DEPOSIT_AMOUNT', '600')),
        help='Refundable deposit amount in USD.',
    )
    parser.add_argument(
        '--variant',
        action='append',
        default=[],
        help='Send only specific variant key(s). Repeat the flag to select multiple.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print payloads without sending anything.',
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.deposit_amount <= 0:
        raise ValueError('--deposit-amount must be greater than 0')


def send_payload(token: str, payload: dict) -> dict:
    response = requests.post(
        POSTMARK_URL,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Postmark-Server-Token': token,
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    load_dotenv()
    args = parse_args()

    try:
        validate_args(args)
        variants = get_variants(args.variant)
    except ValueError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2

    token = os.getenv('POSTMARK_API_TOKEN')
    if not token and not args.dry_run:
        print(
            'Error: POSTMARK_API_TOKEN is required to send emails. '
            'Add it to .env or export it in your shell.',
            file=sys.stderr,
        )
        return 2

    if args.confirmation_link == DEFAULT_CONFIRMATION_LINK:
        print(
            'Warning: using placeholder confirmation link. '
            'Set ICELAND_VOLUNTEER_CONFIRMATION_LINK or pass --confirmation-link '
            'to use a real form URL.',
            file=sys.stderr,
        )

    failures = 0
    for variant in variants:
        model = build_template_model(
            first_name=args.first_name,
            confirmation_link=args.confirmation_link,
            deposit_amount=args.deposit_amount,
            variant=variant,
        )
        payload = build_payload(
            recipient=args.recipient,
            alias=args.alias,
            from_address=args.from_address,
            from_name=args.from_name,
            reply_to=args.reply_to,
            model=model,
        )

        if args.dry_run:
            print(f'=== {variant.key} | {variant.label} ===')
            print(json.dumps(payload, indent=2))
            continue

        try:
            response_data = send_payload(token, payload)
            message_id = response_data.get('MessageID', '<unknown>')
            print(f'Sent {variant.key}: {message_id}')
        except requests.HTTPError as exc:
            failures += 1
            body = exc.response.text if exc.response is not None else str(exc)
            print(f'Failed {variant.key}: {body}', file=sys.stderr)
        except requests.RequestException as exc:
            failures += 1
            print(f'Failed {variant.key}: {exc}', file=sys.stderr)

    if failures:
        print(f'Completed with {failures} failure(s).', file=sys.stderr)
        return 1

    print(f'Completed {len(variants)} variant(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
