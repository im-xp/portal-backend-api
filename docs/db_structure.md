## Database Structure

This document describes the main entities, relationships, and lifecycle flows that power the citizen portal. It reflects the current SQLAlchemy models under `app/api/**/models.py` and the intended behavior described by the product flow.

### Key Concepts

- **Humans (Citizens)**: Users of the portal. Identity is verified via their primary email.
- **Pop-up City**: A time-bound event/city where applications, attendees, and products (tickets/passes) are scoped.
- **Application**: A form submitted by a human to participate in a specific pop-up city. One human may have at most one application per pop-up city.
- **Attendees**: People associated with an application. The first attendee is the main attendee (the applicant). They may add spouse and children attendees
- **Products**: Tickets/passes/items available for a pop-up city.
- **Payments**: Checkout sessions with a snapshot of the items being purchased for specific attendees.

---

### Entities

#### Humans (`humans`)
- Model: `app/api/citizens/models.py::Citizen`
- Purpose: Represents portal users; the `primary_email` is used for identity validation.
- Important fields:
  - `id` (PK)
  - `primary_email` (unique when present)
  - `email_validated` (boolean)
  - Profile fields: `first_name`, `last_name`, `x_user`, `telegram`, etc.
- Relationships:
  - `applications` → `Application` (1-to-many)
  - Many-to-many with `organizations` via `citizen_organizations`
  - Group participation via `group_members` and `group_leaders`

#### Pop-up City (`popups`)
- Model: `app/api/popup_city/models.py::PopUpCity`
- Purpose: Defines each pop-up event/city.
- Important fields:
  - `id` (PK), `name`, `slug`, `prefix`
  - Date range: `start_date`, `end_date`
  - Feature flags: `allows_spouse`, `allows_children`, `allows_coupons`, `requires_approval`
  - Portal visibility and ordering fields

#### Application (`applications`)
- Model: `app/api/applications/models.py::Application`
- Purpose: Application form data from a human to a specific pop-up city.
- Important fields:
  - `id` (PK)
  - `citizen_id` → `humans.id` (FK)
  - `popup_city_id` → `popups.id` (FK)
  - Unique constraint: `(citizen_id, popup_city_id)` ensures one application per human per pop-up
  - Status-related fields: `status` (computed via synonym), `accepted_at`, `submitted_at`, discount flags, reviews
- Relationships:
  - `citizen` → `Citizen`
  - `popup_city` → `PopUpCity`
  - `attendees` → `Attendee` (1-to-many, cascade delete-orphan)
  - `payments` → `Payment` (1-to-many)
  - Optional `organization_rel` and `group`
- Notes:
  - Helper methods include `get_main_attendee()` and `get_products()`.

#### Attendee (`attendees`)
- Model: `app/api/attendees/models.py::Attendee`
- Purpose: People linked to an application: main (applicant), spouse, or children.
- Important fields:
  - `id` (PK)
  - `application_id` → `applications.id` (FK)
  - `category` (e.g., `main`, `spouse`, `kid`)
  - `check_in_code`
- Relationships:
  - `application` → `Application`
  - `attendee_products` (join rows with quantities)
  - `products` (many-to-many via `attendee_products`)
  - `payment_products` (links to purchased snapshot by attendee)

#### Attendee–Product (`attendee_products`)
- Model: `app/api/attendees/models.py::AttendeeProduct`
- Purpose: Many-to-many association between attendees and products, with `quantity`.
- Composite PK: `(attendee_id, product_id)`

#### Product (`products`)
- Model: `app/api/products/models.py::Product`
- Purpose: Tickets/passes/items available for a given pop-up city.
- Important fields:
  - `id` (PK)
  - `popup_city_id` → `popups.id` (FK)
  - `name`, `slug`, `price`, `category`, `attendee_category`
  - Lifecycle: `start_date`, `end_date`, `is_active`, `exclusive`
- Relationships:
  - `attendees` (view-only) and `attendee_products`
  - `payment_products` (snapshots of purchases)

#### Payment (`payments`) and Payment Products (`payment_products`)
- Models: `app/api/payments/models.py::{Payment, PaymentProduct}`
- Purpose: Captures a checkout and a snapshot of items per attendee.
- Payment fields:
  - `id` (PK)
  - `application_id` → `applications.id` (FK)
  - `status`, `amount`, `currency`, `rate`, `source`, `checkout_url`
  - Coupon fields: `coupon_code_id`, `coupon_code`, `discount_value`
  - Optional `group_id`
- PaymentProduct fields:
  - Composite PK: `(payment_id, product_id, attendee_id)`
  - Snapshot: `product_name`, `product_description`, `product_price`, `product_category`
  - `quantity`
- Relationships:
  - `Payment.products_snapshot` → list of `PaymentProduct`
  - `PaymentProduct.attendee` / `.product` / `.payment`

#### Coupon Codes (`coupon_codes`)
- Model: `app/api/coupon_codes/models.py::CouponCode`
- Purpose: Optional discounts scoped to a pop-up city.
- Constraint: unique `(code, popup_city_id)`

#### Groups (`groups`)
- Model: `app/api/groups/models.py::Group`
- Purpose: Cohorts with discounting and express checkout per pop-up.
- Relationships include `applications`, `leaders`, `members`, `products`, and `popup_city`.

#### Organizations (`organizations`) and Memberships (`citizen_organizations`)
- Models: `app/api/organizations/models.py::Organization` and association in `citizens/models.py`
- Purpose: Many-to-many linkage between citizens and organizations.

#### Email Logs (`email_logs`)
- Model: `app/api/email_logs/models.py::EmailLog`
- Purpose: Audit of sent emails. Auto-links `citizen_id` by `receiver_email` when possible.

#### Check-in (`check_ins`)
- Model: `app/api/check_in/models.py::CheckIn`
- Purpose: Arrival/departure and QR/virtual check-in by attendee.

---

### Core Relationships (ER overview)

- Human `1 — n` Application
- Pop-up City `1 — n` Application
- Application `1 — n` Attendee
- Attendee `n — m` Product (via `attendee_products`, with `quantity`)
- Application `1 — n` Payment
- Payment `1 — n` PaymentProduct
- PaymentProduct `n — 1` Product
- PaymentProduct `n — 1` Attendee
- Citizen `n — m` Organization (via `citizen_organizations`)
- Group relationships to citizens, applications, and products as defined above

---

### Lifecycle Flows

#### Identity and Access
1. A portal user is represented by a row in `humans`.
2. The `primary_email` is the identity anchor and must be validated before sensitive operations.

#### Applying to a Pop-up City
1. A human creates an `Application` for an active `PopUpCity` (enforced unique per human per pop-up).
2. Upon application creation, a corresponding `Attendee` is created with `category = 'main'` and linked via `application_id`.
3. Depending on pop-up city configuration (`allows_spouse`, `allows_children`), the main attendee may add spouse and child attendees to the same application.

#### Purchasing Tickets/Products
1. When an application is accepted (per `Application.status` rules), the user can purchase `Product`s for attendees.
2. A `/payments` checkout is created, generating a `Payment` and `PaymentProduct` snapshot rows for the selected products and quantities, per attendee.
3. On payment approval, products are assigned to attendees by creating/updating rows in `attendee_products` with the purchased `quantity` per `(attendee, product)`.
4. The application’s purchased items can be retrieved via `Application.get_products()` or per-attendee via `Attendee.attendee_products`/`Attendee.products`.

#### Check-in and Tickets Access
1. Each attendee has a `check_in_code`. Additional flows exist for ticket retrieval via `AttendeeTicketApiKey` and check-in via `check_ins`.

---

### Constraints and Integrity Notes

- `applications`: unique `(citizen_id, popup_city_id)` prevents duplicate applications by the same human for the same pop-up.
- `attendee_products`: composite PK with `quantity` maintains unique product assignment per attendee.
- Payment snapshots (`payment_products`) store denormalized product data to preserve historical purchase details even if products change later.
- Many relationships enforce cascading or are loaded `lazy='joined'` where appropriate for performance and integrity.

---

### Table Reference

- `humans` (citizens)
- `popups`
- `applications`
- `attendees`
- `attendee_products`
- `products`
- `payments`
- `payment_products`
- `coupon_codes`
- `groups`, `group_members`, `group_leaders`, `group_products`
- `organizations`, `citizen_organizations`
- `email_logs`
- `check_ins`
