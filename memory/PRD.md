# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Pages
- / (Map), /login, /register, /profile, /subscribe, /leaderboard, /rankings
- /impact (Community Impact Map)
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics
- /admin/login (2FA), /admin (owner dashboard)
- /auth/google/callback (Google OAuth callback handler)

## Dual-Auth Architecture (PERMANENT)
The Emergent/Kubernetes/Cloudflare proxy ALWAYS returns `access-control-allow-origin: *` for all responses. This is platform infrastructure and CANNOT be changed. Cookie-based auth breaks for cross-origin Capacitor requests.

**Solution (DO NOT CHANGE):**
- **Web**: Relative `/api` paths → same-origin → no CORS. Cookies (httponly, secure, samesite=none) work normally.
- **Capacitor Native**: Full hosted URL (cross-origin). Auth via `Authorization: Bearer <token>`. `withCredentials` forced to `false`. Tokens persisted in localStorage (survives app restart). Axios interceptor in `AuthContext.js` enforces this on every request.

Key files: `tokenManager.js`, `config.js`, `AuthContext.js` (interceptor)

## Implemented
- Map with color-coded pins, heatmaps, PWA, 11 languages with SVG flag icons
- Gamification (ranks, badges, leaderboards, streaks), premium/free tiers
- Municipality dashboard (€50/month) with analytics, moderation
- City/Barrio rankings (premium), Clean Route, rank notifications
- Username system (editable by all users), photo uploads, 30-day archive, Resend emails
- Admin panel with 2FA, global stats, user management, photo moderation
- Real receipt verification: Apple App Store Server API v2 + Google Play Developer API
- Capacitor Native Projects for iOS & Android with Bearer token auth
- Google Auth: Login/Register via Emergent Managed Auth (redirect fix for native)
- Activity Banner, Feedback Drawer, Points Popup, Streak Flame Animation
- Web Push Notifications (VAPID) + Capacitor Native Push (FCM)
- Community Impact Map with shareable impact card
- Emotional/Social Messaging in translations

## Backlog (P0-P2)
- P0: Full `yarn build` production build test
- P1: Apple Auth integration (Sign in with Apple)
- P2: Configure real Apple/Google credentials and FCM key when app is in stores
- P2: Production deployment and custom domain setup
