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
- `*_service.py` — Gamification, email, rankings, clean route, webhooks, push, etc.
- `config.js` — API URL (relative `/api` for web, full URL for Capacitor native)
- `tokenManager.js` — Bearer token vs HttpOnly cookie hybrid auth
- `AuthContext.js` — Auth state + axios interceptors for token refresh
- `pushManager.js` — Web Push + Capacitor native push utility

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

### User Engagement & Retention Features (2026-04-17)
- Google Auth: Login/Register with Google via Emergent Managed Auth
- Activity Banner: Rotating banner showing nearby reports, active zones, user rank
- Feedback Drawer: Bug reports, suggestions submission
- Points Popup: Animated popup showing earned points
- SVG Flag Icons: Language selector with proper SVG flags for all 11 languages
- Emotional/Social Messaging: Community-driven language in translations
- Username Change: All users can edit username (not just Premium)

### Web Push & Streak Flame (2026-04-17)
- **Web Push Notifications**: Full Web Push support via service worker with VAPID keys
  - Push toggle available to ALL logged-in users (not just Premium)
  - Smart notification prompt after first successful report
  - Backend: /api/push/subscribe, /api/push/unsubscribe, /api/push/status, /api/push/vapid-key
  - Service worker handles push events, notification clicks, and caching
- **Capacitor Native Push**: FCM integration for iOS/Android via @capacitor/push-notifications
  - Falls back gracefully when plugin not available (web only)
  - Native push listeners set up in App.js
- **Profile Notification Toggle**: Real push subscribe/unsubscribe (not just localStorage)
  - Checks actual backend subscription status on profile load
- **Streak Flame Animation**: Shows on map for users with 3+ day streaks
  - 3 visual intensity levels: small (3-6d, orange), medium (7-29d, red-pink), large (30d+, deep red)
  - Animated pulse + glow effects, auto-dismisses after 8 seconds
  - Shows motivational message ("Tu constancia marca la diferencia")

## To Enable Real Payments
Set in backend/.env:
```
# Apple
APPLE_KEY_ID=your_key_id
APPLE_ISSUER_ID=your_issuer_id
APPLE_BUNDLE_ID=com.cacaradar.app
APPLE_KEY_PATH=/path/to/SubscriptionKey.p8
APPLE_ENVIRONMENT=Sandbox

# Google
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
GOOGLE_PACKAGE_NAME=com.cacaradar.app
```

## To Enable Native Push (FCM)
Set in backend/.env:
```
FCM_SERVER_KEY=your_fcm_server_key
```

## Backlog (P0-P2)
- P0: Full `yarn build` production build test
- P1: Apple Auth integration (Sign in with Apple)
- P2: Configure real Apple/Google credentials when app is in stores
- P2: Production deployment and custom domain setup
