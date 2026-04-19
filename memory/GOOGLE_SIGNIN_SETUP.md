# Google Sign-In Setup

This project uses the official Google Identity Services (GIS) web library for authentication.

## Required environment variables

### Frontend

- `REACT_APP_GOOGLE_CLIENT_ID`
  - The Google OAuth Web Client ID for the current deployment origin.

### Backend

- `GOOGLE_WEB_CLIENT_ID`
  - Primary allowed Google OAuth Web Client ID.
- `GOOGLE_ALLOWED_CLIENT_IDS` (optional)
  - Comma-separated additional Web Client IDs allowed to verify ID tokens.
  - Use this when one backend serves multiple approved browser origins across environments.

## Recommended deployment mapping

### Production

- Origin: `https://cacaradar.es`
- Frontend:
  - `REACT_APP_GOOGLE_CLIENT_ID=<production web client id>`
- Backend:
  - `GOOGLE_WEB_CLIENT_ID=<production web client id>`

### Staging / Preview

- Origin examples:
  - `https://caca-radar.emergent.host`
  - any preview URL actually used by the deployment
- Frontend:
  - `REACT_APP_GOOGLE_CLIENT_ID=<staging web client id>`
- Backend:
  - `GOOGLE_WEB_CLIENT_ID=<staging web client id>`
  - or keep production as primary and add staging to `GOOGLE_ALLOWED_CLIENT_IDS`

### Local development

- Origin examples:
  - `http://localhost:3000`
  - any additional localhost port used by this repo
- Frontend:
  - `REACT_APP_GOOGLE_CLIENT_ID=<local web client id>`
- Backend:
  - `GOOGLE_WEB_CLIENT_ID=<local web client id>`
  - or add the local client ID to `GOOGLE_ALLOWED_CLIENT_IDS`

## Google Cloud Console configuration

Create a **Web application** OAuth client in Google Cloud Console.

### Authorized JavaScript origins

Add the exact origins used by the app:

- `https://cacaradar.es`
- `https://caca-radar.emergent.host`
- `http://localhost:3000`
- any other localhost/dev port actually used

### Authorized redirect URIs

Not required for the main login flow.

This app uses the GIS popup ID-token flow, not the authorization-code redirect flow.

## App behavior

- Login and registration pages render the official Google button from `https://accounts.google.com/gsi/client`
- GIS returns an ID token credential directly in the browser
- Frontend sends `{ credential }` to:
  - `POST /api/auth/google/login`
- Backend verifies the ID token with `google-auth`
- Existing Google users are matched by:
  - `linked_providers.google.subject`
- Existing non-Google accounts are **not** merged automatically by email
- Logged-in users can link Google from the profile page through:
  - `POST /api/auth/google/link`

## Common failure modes

### The Google button says sign-in is not configured

Check:

- frontend has `REACT_APP_GOOGLE_CLIENT_ID`
- the frontend was rebuilt and redeployed after changing it

### Backend returns audience mismatch

Check:

- the ID token's `aud` claim matches one of:
  - `GOOGLE_WEB_CLIENT_ID`
  - `GOOGLE_ALLOWED_CLIENT_IDS`

### Popup opens and immediately fails

Check:

- the current site origin is listed under **Authorized JavaScript origins**
- the browser is not blocking popups

### Existing password account cannot sign in with Google

This is expected until Google is explicitly linked.

Safe flow:

1. Sign in with the existing method
2. Go to profile/settings
3. Link Google there

## Debug endpoints / checks

- `GET /api/health`
- `GET /api/version`
- `GET /api/health/auth`

`/api/health/auth` now reports whether Google client IDs are configured for GIS verification.
