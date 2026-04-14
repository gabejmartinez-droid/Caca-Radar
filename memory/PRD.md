# Caca Radar - PRD

## Architecture
- Frontend: React 19 + TailwindCSS + Shadcn UI + Leaflet + leaflet.heat + PWA
- Backend: FastAPI + MongoDB + Object Storage + Resend + Apple/Google webhooks
- Services: scoring, antispam, validation, ranking, email, webhook_handlers

## All Pages
- / (Map with pins, heatmap toggle, report drawer, details drawer, flag drawer)
- /login, /register
- /profile (gamification stats, trust score, scoring guide)
- /subscribe (€0.99/mo, €9.99/yr users + €49/mo municipalities)
- /leaderboard (national + per-city, subscriber only)
- /dashboard/login, /dashboard/register (municipality)
- /dashboard (stats, reports table, photo review, moderation)

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Credentials Needed for Production
```
RESEND_API_KEY=re_... (from resend.com - add domain cacaradar.es)
APPLE_BUNDLE_ID=com.cacaradar.app
APPLE_KEY_ID=...
APPLE_ISSUER_ID=...
APPLE_KEY_PATH=/path/to/AuthKey.p8
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
GOOGLE_PACKAGE_NAME=com.cacaradar.app
```

## Backend Modules
- server.py (API routes)
- scoring_service.py (points, streaks, multipliers)
- antispam_service.py (trust, cooldowns, proximity, GPS)
- validation_service.py (consensus, weighted votes)
- ranking_service.py (percentile ranks, weekly recalc)
- email_service.py (Resend, verification codes)
- webhook_handlers.py (Apple V2 + Google RTDN)
