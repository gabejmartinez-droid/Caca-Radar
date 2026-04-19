# Play Integrity Setup

This project includes an Android-native Play Integrity scaffold with backend verification support.

## Frontend / Android

Required env vars for Android builds:

- `REACT_APP_ENABLE_PLAY_INTEGRITY=true`
- `REACT_APP_GOOGLE_CLOUD_PROJECT_NUMBER=<your Google Cloud project number>`

The Android app warms the standard Play Integrity token provider during app startup when:

- the app is running natively on Android
- Play Integrity is enabled via env
- a cloud project number is present

## Backend

Required env vars:

- `GOOGLE_SERVICE_ACCOUNT_PATH=<absolute path to service account json>`
- `GOOGLE_PACKAGE_NAME=com.jefe.cacaradar`

Optional diagnostic endpoint:

- `GET /api/play-integrity/status`

Verification endpoint:

- `POST /api/play-integrity/verify`

Example request body:

```json
{
  "integrity_token": "TOKEN_FROM_ANDROID",
  "request_hash": "BASE64URL_SHA256_HASH",
  "action": "login"
}
```

## Notes

- Current mode is `log_only`.
- Web and iOS do not use Play Integrity.
- The Android app now includes `com.google.android.play:integrity:1.6.0`.
- Server verification uses Google-managed token decoding via the linked Cloud project service account.
