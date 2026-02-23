# Application Fee

Some popup cities require users to pay an application fee before their application can be submitted. This document describes the backend behavior and API changes.

## Overview

When a popup city has `application_fee` configured (e.g. `5.0` USD), the following rules apply:

1. Applications cannot be submitted (status `in review`) until the fee is paid
2. Applications created with status `in review` are **forced to `draft`** by the backend
3. After the fee payment is approved (via payment provider webhook), the backend **automatically submits the application** (transitions it to `in review` or `accepted` depending on popup city config)

When `application_fee` is `null` or `0`, everything works as before -- no changes to existing behavior.

## How to detect if a fee is required and paid

The application response includes two fields:

```
GET /applications/{id}
```

```json
{
  "id": 123,
  "status": "draft",
  "application_fee_required": true,
  "application_fee_paid": false,
  ...
}
```

| Field | Type | Description |
|-------|------|-------------|
| `application_fee_required` | `bool` | Whether this popup city requires a fee before submission |
| `application_fee_paid` | `bool` | Whether an approved fee payment exists for this application |

These fields are computed by the backend. When `application_fee_required` is `false`, `application_fee_paid` is always `false`.

The fee amount is available on the popup city response:

```
GET /popup-cities/{id}
```

```json
{
  "id": 1,
  "name": "Example City",
  "application_fee": 5.0,
  ...
}
```

- `application_fee: null` or `application_fee: 0` -- no fee required
- `application_fee: 5.0` -- fee of $5 USD required before submission

## New endpoint: Create application fee payment

```
POST /payments/application-fee
Authorization: Bearer <token>
```

**Request body:**

```json
{
  "application_id": 123
}
```

**Success response (200):**

```json
{
  "id": 1,
  "application_id": 123,
  "external_id": "sf_abc123",
  "status": "pending",
  "amount": 5.0,
  "currency": "USD",
  "checkout_url": "https://pay.simplefi.tech/...",
  "is_application_fee": true,
  "products_snapshot": [],
  "is_installment_plan": null,
  "installments_total": null,
  "installments_paid": null,
  "created_at": "2026-02-19T12:00:00",
  "updated_at": "2026-02-19T12:00:00"
}
```

The `checkout_url` is the payment link the user should be redirected to (or opened in a new tab/window).

**Error responses:**

| Status | Detail | When |
|--------|--------|------|
| 400 | `Application must be in draft status` | Application is not in `draft` |
| 400 | `This popup city does not require an application fee` | Popup city has no fee configured |
| 400 | `Application fee has already been paid` | An approved fee payment already exists |
| 403 | Forbidden | User doesn't own this application |

**Behavior notes:**

- Only one pending fee payment can exist at a time. Creating a new one **cancels** any previous pending fee payment (the old `checkout_url` becomes invalid).
- This is a single payment (no installments).
- The fee amount is determined by the backend from the popup city config -- the client does not send an amount.

## Changed behavior: Application submission

### Creating an application (`POST /applications/`)

If the popup city has an application fee and the client sends `status: "in review"`, the backend **overrides** the status to `draft` and sets `submitted_at` to `null`. The application cannot be submitted at creation time because the fee hasn't been paid yet.

### Updating an application (`PUT /applications/{id}`)

If the client sends `status: "in review"` and the fee has not been paid:

```
HTTP 402 Payment Required
```

```json
{
  "detail": "Application fee must be paid before submitting"
}
```

If the fee has been paid (approved fee payment exists), the update proceeds normally.

## Payment flow

```
1. Client creates application        --> status: "draft"
2. Client calls POST /payments/application-fee
3. Client redirects user to checkout_url
4. User pays on the payment provider page
5. Payment provider sends webhook to backend
6. Backend approves fee payment and automatically:
   - Sets submitted_at on the application
   - Calculates the new status (in review / accepted)
   - Sends APPLICATION_RECEIVED email if status is "in review"
7. Client polls or refreshes application to see updated status
```

After step 6, the application status will be either:
- `in review` -- if the popup city has `requires_approval: true`
- `accepted` -- if the popup city has `requires_approval: false` and no discount was requested

The client can also manually submit the application via `PUT /applications/{id}` with `status: "in review"` after the fee is paid (step 6 already does this automatically, but the manual path works too).

## Identifying fee payments

The `is_application_fee` field on payment responses distinguishes fee payments from regular product payments:

```
GET /payments/
GET /payments/{id}
```

```json
{
  "id": 1,
  "is_application_fee": true,
  "products_snapshot": [],
  ...
}
```

Fee payments always have an empty `products_snapshot` since they are not associated with any products.
