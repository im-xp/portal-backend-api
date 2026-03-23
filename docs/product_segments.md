# Product Segments API

Product segments allow restricting which products (tickets/passes) an applicant can see and purchase. Segments are optional per popup city — popups without segments work as before. An application can be assigned multiple segments; the user sees the union of products across all their segments.

## Auth

All endpoints below use the `x-api-key` header with the `APPLICATION_REVIEW_API_KEY` value.

## Endpoints

### List segments for a popup city

```
GET /product-segments/?popup_city_slug={slug}
```

**Headers:** `x-api-key: <APPLICATION_REVIEW_API_KEY>`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "VIP",
    "slug": "vip",
    "description": "VIP ticket holders",
    "popup_city_id": 5,
    "products": [
      { "id": 10, "name": "VIP Pass", "slug": "vip-pass", "price": 500.0, ... }
    ],
    "created_at": "2026-03-19T00:00:00",
    "updated_at": "2026-03-19T00:00:00"
  }
]
```

Returns an empty list if the popup has no segments configured.

### Accept an application with segments

```
PATCH /applications/{application_id}/review
```

**Headers:** `x-api-key: <APPLICATION_REVIEW_API_KEY>`

**Body:**
```json
{
  "status": "accepted",
  "discount_assigned": 70,
  "segment_slugs": ["long-build", "vip"]
}
```

**Rules:**
- `segment_slugs` is only used when `status` is `"accepted"`. It is ignored on rejection.
- If the popup city has segments configured, `segment_slugs` is **required** when accepting (at least one). Omitting it returns `400`.
- If the popup city has no segments, omit `segment_slugs` (or set to `null`). Behavior is unchanged from before.
- Any invalid slug in the list returns `400`.

**Response:** `200 OK` — returns the full application object. The `product_segment_ids` field reflects the assigned segment IDs (or `[]`).

## Side effects for end users

These happen automatically — no reviewer action needed beyond assigning the segments:

- **`GET /products/?popup_city_id={id}`** (user auth) — If the user's application has segments, only products in the union of those segments are returned. No segments means all products are returned as before.
- **`POST /payments/`** (user auth) — If the user has segments, purchasing a product outside the union of all assigned segments returns `400`.
