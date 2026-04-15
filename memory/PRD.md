# Caca Radar - PRD

## Original Problem Statement
Build a mobile-first web app called "Caca Radar" for Spain. Users report dog feces in public places and view reports on a map.

## All Pages
- / (Map, heatmap, push toggle, report/details/flag drawers)
- /login, /register, /profile
- /subscribe (users + municipalities)
- /leaderboard (national + per-city)
- /rankings (city + barrio rankings, premium)
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics

## Architecture
- `server.py` — FastAPI app, routes, startup (~1863 lines)
- `deps.py` — Shared DB, auth, models, utilities (~251 lines)
- `*_service.py` — Gamification, antispam, validation, ranking, email, webhook, push, clean route, digest, badges, city rankings

## What's Been Implemented
- Interactive Leaflet map with color-coded pins, heatmaps
- Gamification engine (scoring, trust, ranks, badges, weekly leaderboards)
- Premium/Free tiers with App Store/Play Store mock handlers
- Municipality dashboard (€50/month) with analytics, moderation, email verification (Resend)
- PWA, service workers, 11-language support
- Smart Navigation ("Clean Route")
- Registration enforcement, username system
- Photo uploads for all users
- City Rankings (Premium): Cleanest/dirtiest cities by reports per 10k residents
- Barrio Rankings (Premium): Neighborhood rankings within each city
- Rank change notifications
- Report archiving after 30 days, freshness: <48h / 2-6 days / >6 days
- Custom app icon (favicon, PWA, header logos)
- CORS fix (allow_origins=["*"]), secure cookies
- Code decomposition: shared deps extracted to deps.py

## Free Tier
Reporting (GPS, photo, description), viewing map, voting, validation, rank system, rank change notifications

## Premium Tier
Heatmaps, advanced filters, clean route, push notifications, city/barrio rankings, full leaderboard, contributor badge, 1.5x point multiplier

## Municipality Tier (€50/month)
Dashboard, analytics, moderation, photo reviews, digest emails, hotspot tracking

## Prioritized Backlog
- P1: Configure real Apple/Google webhook URLs
- P2: Implement real receipt verification (currently mocked)

## Mocked
- Apple/Google webhook verification (mock: true)
- App store placeholder URLs in social sharing
