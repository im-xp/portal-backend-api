# Account Linking - Frontend Integration Guide

## Overview

The account linking feature allows users to merge multiple accounts they own into a single unified account. When accounts are linked, the user's profile will show combined data (applications, total days, referrals) from all linked accounts.

## User Flow

1. User is logged into **Account A** (e.g., `alice@personal.com`)
2. User wants to link **Account B** (e.g., `alice@work.com`)
3. User enters Account B's email address
4. System sends a 6-digit verification code to Account B's email
5. User checks Account B's email and enters the verification code
6. Accounts are now linked!

**Important:** The user stays logged into Account A during the entire process. They just need to prove they own Account B by entering the code sent to that email.

---

## API Endpoints

Base URL: `/account-clusters`

All endpoints require authentication via Bearer token.

### 1. Initiate Account Link

**Endpoint:** `POST /account-clusters/initiate`

**Purpose:** Start the linking process by sending a verification code to the target account's email.

**Request:**
```json
{
  "target_email": "alice@work.com"
}
```

**Success Response (201):**
```json
{
  "message": "Verification code sent to alice@work.com",
  "request_id": 42
}
```

**Error Responses:**
- **404** - Target email not found
```json
{
  "detail": "No account found with email alice@work.com"
}
```

- **400** - Cannot link to self
```json
{
  "detail": "Cannot link account to itself"
}
```

- **400** - Accounts already linked
```json
{
  "detail": "Accounts are already linked"
}
```

- **400** - Email send failure
```json
{
  "detail": "Failed to send verification email to alice@work.com. Please try again later."
}
```

---

### 2. Verify and Complete Link

**Endpoint:** `POST /account-clusters/verify`

**Purpose:** Complete the linking process by verifying the 6-digit code.

**Request:**
```json
{
  "verification_code": "123456"
}
```

**Success Response (200):**
```json
{
  "message": "Accounts successfully linked",
  "cluster_id": 1
}
```

**Error Responses:**
- **404** - Invalid code
```json
{
  "detail": "Invalid verification code"
}
```

- **400** - Expired code
```json
{
  "detail": "Verification code has expired"
}
```

- **403** - Not authorized
```json
{
  "detail": "Only the account that initiated the link request can verify the code"
}
```

**Note:** Verification codes expire after 5 minutes.

---

### 3. View Linked Accounts

**Endpoint:** `GET /account-clusters/my-cluster`

**Purpose:** See all accounts currently linked together.

**Success Response (200):**
```json
{
  "cluster_id": 1,
  "citizen_ids": [100, 101, 102],
  "member_count": 3,
  "created_at": "2025-01-15T10:30:00"
}
```

**Note:** If the user is not in any cluster, returns:
```json
{
  "cluster_id": 0,
  "citizen_ids": [100],
  "member_count": 1,
  "created_at": null
}
```

---

### 4. Unlink Account (Leave Cluster)

**Endpoint:** `DELETE /account-clusters/leave`

**Purpose:** Remove the current account from its cluster. This is reversible.

**Success Response (200):**
```json
{
  "message": "Successfully left the account cluster"
}
```

**Error Response:**
- **404** - Not in any cluster
```json
{
  "detail": "You are not in any cluster"
}
```

---

## UI/UX Recommendations

### Suggested UI Flow

1. **Link Account Modal/Page**
   ```
   ┌─────────────────────────────────────┐
   │  Link Another Account               │
   ├─────────────────────────────────────┤
   │                                     │
   │  Enter email of account to link:    │
   │  [________________________]         │
   │                                     │
   │  [Cancel]  [Send Code]             │
   └─────────────────────────────────────┘
   ```

2. **Verification Code Input**
   ```
   ┌─────────────────────────────────────┐
   │  Verify Email                       │
   ├─────────────────────────────────────┤
   │                                     │
   │  We sent a code to:                 │
   │  alice@work.com                     │
   │                                     │
   │  Enter 6-digit code:                │
   │  [___] [___] [___] [___] [___] [___]│
   │                                     │
   │  Code expires in: 4:32              │
   │                                     │
   │  [Cancel]  [Verify]                │
   └─────────────────────────────────────┘
   ```

3. **Success Message**
   ```
   ┌─────────────────────────────────────┐
   │  ✓ Accounts Linked Successfully!    │
   ├─────────────────────────────────────┤
   │                                     │
   │  Your accounts are now linked.      │
   │  Your profile now shows combined    │
   │  data from both accounts.           │
   │                                     │
   │  [Close]                           │
   └─────────────────────────────────────┘
   ```

### Important UX Notes

- **Code expiration:** Show a countdown timer (5 minutes)
- **Resend code:** Consider adding a "Resend code" button (would require calling initiate again)
- **Input validation:**
  - Email format validation before submitting
  - Code should be exactly 6 digits
- **Loading states:** Show spinners while API calls are in progress
- **Clear error messages:** Display API error messages to the user
- **Don't allow self-linking:** Disable submit if user enters their own email

---

## Testing

Use the test script provided at `scripts/test_account_linking.py` to test the flow:

```bash
python scripts/test_account_linking.py
```

This will guide you through the linking process step by step.

---

## Common Issues

### Issue: "Invalid verification code"
- **Cause:** Code was entered incorrectly or doesn't exist
- **Solution:** Double-check the code in the email

### Issue: "Verification code has expired"
- **Cause:** More than 5 minutes passed since code was sent
- **Solution:** Start the process again by calling initiate endpoint

### Issue: "Only the account that initiated the link request can verify the code"
- **Cause:** User logged out and logged into a different account before verifying
- **Solution:** User must stay logged into the account that initiated the request

### Issue: "Failed to send verification email"
- **Cause:** Email service is down or target email is invalid
- **Solution:** Try again later or contact support

---

## Profile Data Aggregation

Once accounts are linked, the following data is automatically aggregated:

**Endpoint:** `GET /citizens/profile`

The profile response will include:
- ✅ All applications from all linked accounts
- ✅ Total days (summed across all accounts)
- ✅ Referral count (summed across all accounts)
- ✅ All POAPs from all accounts

**No changes needed to the profile endpoint** - the aggregation happens automatically on the backend!

---

## Questions?

Contact the backend team or check the API documentation at `/docs` (Swagger UI).
