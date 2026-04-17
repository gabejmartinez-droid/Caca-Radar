# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Pages
- / (Map), /login, /register, /profile, /subscribe, /leaderboard, /rankings
- /impact (Community Impact Map — NEW)
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
- Map with color-coded pins, heatmaps, PWA, 11 languages with SVG flag icons
- Gamification (ranks, badges, leaderboards, streaks), premium/free tiers
- Municipality dashboard (€50/month) with analytics, moderation
- City/Barrio rankings (premium), Clean Route, rank notifications
- Username system (editable by all users), photo uploads, 30-day archive, Resend emails
- Admin panel (jefe@cacaradar.es) with 2FA, global stats, user management, photo moderation
- Real receipt verification: Apple App Store Server API v2 + Google Play Developer API
- Custom app icon (favicon + PWA + headers)
- Capacitor Native Projects for iOS & Android
- Bearer token fallback for Capacitor to bypass Proxy CORS
- Report cooldown (30s) and 1m proximity duplicate confirmation
- GPS Re-center button and forced fresh GPS grab on report submission
- VIP Account configuration (gabejmartinez@gmail.com)
- Google Auth: Login/Register with Google via Emergent Managed Auth
- Activity Banner, Feedback Drawer, Points Popup
- Emotional/Social Messaging in translations
- Web Push Notifications (VAPID) for all logged-in users
- Capacitor Native Push (FCM) integration
- Streak Flame Animation (3+ day streaks on map)

### Community Impact Map (2026-04-17)
- **New page at /impact**: Personal contribution map showing user's reports, cleaned zones, confirmations
- **Backend `/api/users/impact`**: Aggregates reports, votes, validations into impact stats
- **Interactive map**: CircleMarkers color-coded (green=cleaned, red=active, blue=confirmed)
- **Stats grid**: Total reports, cleaned zones, confirmations, municipalities helped
- **Activity timeline**: Monthly bar chart of contributions
- **Areas helped**: Municipalities and barrios tags
- **Share impact**: Generates shareable text with impact stats for social media
- **Empty state**: CTA to start contributing when user has no activity
- **Access**: Profile page button + MapPage user dropdown menu

## Backlog (P0-P2)
- P0: Full `yarn build` production build test
- P1: Apple Auth integration (Sign in with Apple)
- P2: Configure real Apple/Google credentials and FCM key when app is in stores
- P2: Production deployment and custom domain setup
