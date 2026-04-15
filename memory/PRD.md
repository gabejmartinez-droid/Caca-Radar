# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Pages
- / (Map), /login, /register, /profile, /subscribe, /leaderboard, /rankings
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics
- /admin/login (2FA), /admin (owner dashboard)

## Architecture
- `server.py` — Routes + startup | `deps.py` — Shared DB/auth/models
- `*_service.py` — Gamification, email, rankings, clean route, webhooks, etc.

## Implemented
- Map with color-coded pins, heatmaps, PWA, 11 languages
- Gamification (ranks, badges, leaderboards), premium/free tiers
- Municipality dashboard (€50/month) with analytics, moderation
- City/Barrio rankings (premium), Clean Route, rank notifications
- Username system, photo uploads, 30-day archive, Resend emails
- Admin panel (jefe@cacaradar.es) with 2FA, global stats, user management, photo moderation
- **Real receipt verification**: Apple App Store Server API v2 + Google Play Developer API
  - Falls back to mock when credentials not configured
  - Subscription expiry auto-deactivation on startup
  - Admin integration-status endpoint to check what's configured
- Custom app icon (favicon + PWA + headers)

## To Enable Real Payments
Set in backend/.env:
```
# Apple
APPLE_KEY_ID=your_key_id
APPLE_ISSUER_ID=your_issuer_id
APPLE_BUNDLE_ID=com.cacaradar.app
APPLE_KEY_PATH=/path/to/SubscriptionKey.p8
APPLE_ENVIRONMENT=Sandbox  (or Production)

# Google
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
GOOGLE_PACKAGE_NAME=com.cacaradar.app
```

## Backlog
All major features complete. Remaining:
- Configure real Apple/Google credentials when app is in stores
- Production deployment and custom domain setup
