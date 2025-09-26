## Third‑Party Authentication Integration Guide

This guide explains how an external application can authenticate a user via EdgeOS and obtain a Bearer token to call protected endpoints.

### Overview
- **Goal**: Verify a user by email using a short‑lived code and receive a JWT Bearer token.
- **Prerequisites**: Your application must be registered as an authorized third-party app with a valid API key.
- **Flow**:
  1. Your app calls `POST /citizens/authenticate-third-party` with the user's email and your API key in the `X-API-Key` header.
  2. EdgeOS validates your API key and sends a 6‑digit code to the user's email (valid for 5 minutes).
  3. Your app collects the code from the user and calls `POST /citizens/login` with `email` and `code` as query parameters.
  4. You receive a JWT Bearer token to access protected endpoints.

Use `https://<BASE_URL>` for your deployment host.

### Authorization Setup

Before using the authentication flow, your application must be registered in the system:

1. **Registration**: Send an email to **francisco@muvinai.com** to register your third-party application. Include your application name and intended use case.
2. **API Key**: Once approved and registered, you'll receive a unique API key that identifies your application.
3. **Security**: Store your API key securely and never expose it in client-side code or logs.

### Endpoints

#### 1) Request email code
- **Method/Path**: `POST /citizens/authenticate-third-party`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-API-Key: <your-api-key>` *(required)*
- **Body (JSON)**:
```json
{
  "email": "user@example.com"
}
```
- **Success (200)**:
```json
{ "message": "Mail sent successfully" }
```
- **Errors**:
  - 401 if the API key is invalid
  - 404 if the citizen does not exist

Example cURL:
```bash
curl -X POST \
  "https://<BASE_URL>/citizens/authenticate-third-party" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "email": "user@example.com"
  }'
```

#### 2) Exchange code for token
- **Method/Path**: `POST /citizens/login`
- **Query parameters**: `email` (string), `code` (integer)
- **Success (200)**:
```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer"
}
```
- **Errors**:
  - 400 if `email` and `code` are not both provided
  - 401 if the code is invalid or expired
  - 404 if the citizen is not found

Example cURL:
```bash
curl -X POST \
  "https://<BASE_URL>/citizens/login?email=user%40example.com&code=123456"
```

Token details:
- **Format**: JWT (HS256).
- **Claims**: includes `citizen_id`, `email`, and `third_party_app` (containing the name of the authorized app).
- **Usage**: send in the `Authorization` header as `Bearer <token>`.

### Using the token
Example: Get the authenticated citizen's profile
```bash
curl -X GET \
  "https://<BASE_URL>/citizens/profile" \
  -H "Authorization: Bearer <token>"
```

### Practical considerations
- **API Key Security**: Store your API key securely (environment variables, secure key management). Never expose it in client-side code, logs, or version control.
- **HTTPS**: Always use HTTPS in production and never log or expose authentication codes or tokens.
- **Code lifetime**: Authentication codes are valid for 5 minutes; prompt the user to request a new code on failure.
- **Token lifetime**: The API validates JWT signatures server‑side. If you receive 401 responses, repeat the code exchange flow.
- **App Registration**: Your registered app name will be embedded in tokens for traceability and audit purposes.
- **Rate limiting**: Implement appropriate rate limiting in your application to avoid overwhelming the authentication endpoints.
