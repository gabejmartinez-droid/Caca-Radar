# Caca Radar - PRD

## Original Problem Statement
Build a mobile-first web app called "Caca Radar" for Spain. Users report dog feces in public places and view reports on a map. Features: color-coded pins, report submission with GPS/photo/timestamp, voting system, gamification, freemium model, municipality dashboard, multi-language support.

## All Pages
- / (Map, heatmap toggle, push toggle, report/details/flag drawers)
- /login, /register, /profile
- /subscribe (users + municipalities)
- /leaderboard (national + per-city)
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics

## Backend Modules
- server.py, scoring_service.py, antispam_service.py, validation_service.py
- ranking_service.py, email_service.py, webhook_handlers.py, push_service.py
- clean_route_service.py, digest_service.py, badges_service.py

## What's Been Implemented
- Base CRUD, interactive Leaflet map with color-coded pins (freshness-based)
- Gamification engine (scoring, trust, ranks, badges, weekly leaderboards)
- Premium subscription tier with App Store/Play Store mock handlers
- Municipality dashboard with analytics, moderation, email verification (Resend)
- PWA setup, service workers, multi-language support (11 languages)
- Smart Navigation ("Clean Route" hazard detection)
- Registration enforcement (no anonymous reporting/voting)
- Code quality refactoring (component splitting, backend service extraction)
- **Username system** (Apr 2026): Required at registration, existing users prompted on login. Username displayed publicly instead of email.
- **Photo uploads for all users** (Apr 2026): Removed premium gate — any registered user can upload photos with reports. Detail drawer fetches fresh report data to always show latest photo.
- CORS fix: `allow_origins=["*"]` for universal deployment compatibility
- Secure cookies: `Secure=True` flag for HTTPS environments

## Free Tier Features
- Reporting (with GPS, photo, description)
- Viewing map and report details
- Voting (still there / cleaned, upvote / downvote)
- Validation (confirm / reject)

## Premium Tier Features
- Heatmaps
- Advanced filters
- Clean Route (Smart Navigation)
- Push notifications
- Leaderboard access

## Production Credentials Needed
```
RESEND_API_KEY=re_... (configured, domain verified)
APPLE_BUNDLE_ID, APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_KEY_PATH
GOOGLE_SERVICE_ACCOUNT_PATH, GOOGLE_PACKAGE_NAME
```
VAPID keys already generated and configured.

## Prioritized Backlog
- P1: Configure real Apple/Google webhook URLs in App Store Connect / Google Play Console
- P2: Implement actual receipt verification against Apple/Google production endpoints (currently mocked)
- P2: Further decompose server.py (~2050 lines) into route modules

## Mocked Integrations
- Apple App Store / Google Play webhook verification (returns mock: true)
- Placeholder URLs for App store links in social sharing
