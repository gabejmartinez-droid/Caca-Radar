# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Architecture
- **Database**: MongoDB Atlas (`cacaradar.ubswhuj.mongodb.net`), DB: `cacaradar_production`
- **Backend**: FastAPI on port 8001, prefixed `/api`
- **Frontend**: React on port 3000, relative `/api` for web, full URL for Capacitor
- **Auth**: Cookies (web) / Bearer tokens (Capacitor native)
- Production safety guard: refuses startup if MONGO_URL=localhost or DB_NAME=test_database when APP_ENV=production

## Key Endpoints Added (Apr 18)
- `GET /api/version` — environment, db_name, mongo_host, mongo_is_local
- `GET /api/health/deep` — database connectivity, read access, production safety
- `GET /api/admin/report-diagnostics` — report counts by city, timestamps, runtime info
- `report_audit_log` collection — permanent audit trail for every report creation

## Implemented Features
- Map with color-coded pins, heatmaps, PWA, 11 languages with SVG flags
- Gamification (ranks, badges, leaderboards, streaks), premium/free tiers
- Municipality dashboard with analytics, moderation
- Google Auth, Forgot/Reset Password flow
- Web Push + Capacitor Native Push (FCM)
- Community Impact Map, Activity Banner, Feedback Drawer, Streak Flame
- iOS/Android Capacitor native builds with Bearer token auth
- Report audit logging to `report_audit_log` collection

## Backlog
- P0: Full yarn build production test
- P1: Apple Auth integration
- P1: Apple Developer Program activation for iOS Push Notifications signing/capability
- P1: Apple production webhook/certificate setup for App Store server notifications
- P2: Real Apple/Google payment credentials + FCM key
- P2: Production deployment and custom domain

## Waiting On Apple
- Enable the paid Apple Developer account so `com.jefe.cacaradar` can use the Push Notifications capability and a provisioning profile with `aps-environment`.
- Once Apple is active, re-enable iOS push signing in Xcode by restoring the Push Notifications capability and `App/App.entitlements`, then set `REACT_APP_ENABLE_NATIVE_PUSH=true` before the next web/native build.
- Keep local personal-team builds "dev-safe" until then: the app should compile and run, but native iPhone push remains intentionally disabled.
