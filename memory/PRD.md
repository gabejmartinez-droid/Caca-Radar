# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Pages
- / (Map), /login, /register, /profile, /subscribe, /leaderboard, /rankings
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics
- /admin/login (2FA), /admin (owner dashboard)
- /auth/google/callback (Google OAuth callback handler)

## Architecture
- `server.py` — Routes + startup | `deps.py` — Shared DB/auth/models
- `*_service.py` — Gamification, email, rankings, clean route, webhooks, etc.
- `config.js` — API URL (relative `/api` for web, full URL for Capacitor native)
- `tokenManager.js` — Bearer token vs HttpOnly cookie hybrid auth
- `AuthContext.js` — Auth state + axios interceptors for token refresh

## Implemented
- Map with color-coded pins, heatmaps, PWA, 11 languages
- Gamification (ranks, badges, leaderboards, streaks), premium/free tiers
- Municipality dashboard (€50/month) with analytics, moderation
- City/Barrio rankings (premium), Clean Route, rank notifications
- Username system, photo uploads, 30-day archive, Resend emails
- Admin panel (jefe@cacaradar.es) with 2FA, global stats, user management, photo moderation
- Real receipt verification: Apple App Store Server API v2 + Google Play Developer API
- Custom app icon (favicon + PWA + headers)
- Capacitor Native Projects for iOS & Android
- Bearer token fallback for Capacitor to bypass Proxy CORS
- Report cooldown (30s) and 1m proximity duplicate confirmation
- GPS Re-center button and forced fresh GPS grab on report submission
- VIP Account configuration (gabejmartinez@gmail.com)

### User Engagement & Retention Features (Completed 2026-04-17)
- **Google Auth**: Login/Register with Google via Emergent Managed Auth, callback page, auto-generated username
- **Activity Banner**: Rotating banner showing nearby reports, active zones, user rank
- **Feedback Drawer**: Bug reports, suggestions, and general feedback submission
- **Points Popup**: Animated popup showing earned points after actions
- **SVG Flag Icons**: Language selector with proper SVG flags for all 11 languages (replaced emoji)
- **Emotional/Social Messaging**: Community-driven language in translations ("Help your neighborhood", "Together for cleaner streets")
- **Notification Settings**: Toggle in Profile page (on/off via localStorage)
- **Username Change**: All users can edit username (not just Premium)

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

## Backlog (P0-P2)
- P0: Full `yarn build` production build test
- P1: Apple Auth integration (Sign in with Apple)
- P2: Web Push / Native Push notifications via Capacitor (currently localStorage-based toggle)
- P2: Configure real Apple/Google credentials when app is in stores
- P2: Production deployment and custom domain setup
