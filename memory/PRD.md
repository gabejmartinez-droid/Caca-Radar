# Caca Radar - PRD

## All Pages
- / (Map, heatmap toggle, push toggle, report/details/flag drawers)
- /login, /register, /profile
- /subscribe (€0.99/mo, €9.99/yr users + €49/mo municipalities)
- /leaderboard (national + per-city, subscriber only)
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics

## Backend Modules (8 files)
- server.py, scoring_service.py, antispam_service.py, validation_service.py
- ranking_service.py, email_service.py, webhook_handlers.py, push_service.py

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Production Credentials Needed
```
RESEND_API_KEY=re_... (resend.com)
APPLE_BUNDLE_ID, APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_KEY_PATH
GOOGLE_SERVICE_ACCOUNT_PATH, GOOGLE_PACKAGE_NAME
```
VAPID keys already generated and configured.
