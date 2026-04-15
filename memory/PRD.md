# Caca Radar - PRD

## Original Problem Statement
Build a mobile-first web app called "Caca Radar" for Spain. Users report dog feces in public places and view reports on a map. Features: color-coded pins, report submission with GPS/photo/timestamp, voting system, gamification, freemium model, municipality dashboard, multi-language support.

## All Pages
- / (Map, heatmap toggle, push toggle, report/details/flag drawers)
- /login, /register, /profile
- /subscribe (users + municipalities)
- /leaderboard (national + per-city)
- /rankings (city + barrio rankings, premium)
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics

## Backend Modules
- server.py, scoring_service.py, antispam_service.py, validation_service.py
- ranking_service.py, email_service.py, webhook_handlers.py, push_service.py
- clean_route_service.py, digest_service.py, badges_service.py, city_rankings_service.py

## What's Been Implemented
- Base CRUD, interactive Leaflet map with color-coded pins (freshness-based)
- Gamification engine (scoring, trust, ranks, badges, weekly leaderboards)
- Premium subscription tier with App Store/Play Store mock handlers
- Municipality dashboard with analytics, moderation, email verification (Resend)
- PWA setup, service workers, multi-language support (11 languages)
- Smart Navigation ("Clean Route" hazard detection)
- Registration enforcement (no anonymous reporting/voting)
- Username system: Required at registration, existing users prompted on login
- Photo uploads for all registered users
- CORS fix: allow_origins=["*"] for universal deployment
- Secure cookies: Secure=True for HTTPS
- **Report archiving: 30 days** (was 7 days)
- **Freshness categories doubled**: Recent <48h, Moderate 2-6 days, Old >6 days
- **City Rankings (Premium)**: Cleanest/dirtiest cities by reports per 10k residents using Wikipedia population data, with social sharing + app download links
- **Barrio Rankings (Premium)**: Neighborhood rankings within each city by report density
- **Rank Change Notifications**: Users notified on login when their rank changes (up or down)
- **Subscription page**: Updated with all premium features listed

## Free Tier Features
- Reporting (with GPS, photo, description)
- Viewing map and report details
- Voting (still there / cleaned, upvote / downvote)
- Validation (confirm / reject)
- Rank system and streak tracking
- Rank change notifications

## Premium Tier Features
- Heatmaps
- Advanced filters
- Clean Route (Smart Navigation)
- Push notifications
- City rankings (cleanest/dirtiest)
- Barrio rankings per city
- Full leaderboard access
- Contributor name/rank on reports
- 1.5x point multiplier
- Premium badge on map

## Prioritized Backlog
- P1: Configure real Apple/Google webhook URLs in App Store Connect / Google Play Console
- P2: Implement actual receipt verification against Apple/Google production endpoints (currently mocked)
- P2: Further decompose server.py into route modules

## Mocked Integrations
- Apple App Store / Google Play webhook verification (returns mock: true)
- Placeholder URLs for App store links in social sharing
