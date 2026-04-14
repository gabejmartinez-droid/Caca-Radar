# Caca Radar - PRD

## Architecture
- **Frontend:** React 19 + TailwindCSS + Shadcn UI + Leaflet (OpenStreetMap) + PWA
- **Backend:** FastAPI + MongoDB + Object Storage + Apple/Google receipt verification
- **Auth:** JWT with httpOnly cookies, roles: user/municipality/admin

## What's Been Implemented (2026-04-14)

### Core
- Full-screen map with Leaflet/OpenStreetMap, color-coded pins (red/orange/green)
- Report submission with GPS auto-capture + photo upload (Object Storage)
- Voting system ("Sigue ahí" / "Ya limpio"), auto-archive logic
- 8-language support (ES, EN, DE, NL, PL, AR, UK, RU) with RTL for Arabic
- Content policy for photos + enhanced flag system with 7 violation reasons

### Municipality System
- Auto-tagging reports via Nominatim reverse geocoding
- Municipality self-registration with domain verification (blocks Gmail/Hotmail etc)
- 6-digit email verification code flow
- Dashboard with stats, reports table, moderation actions, flag review queue

### Subscriptions & Payments
- Apple App Store receipt verification (app-store-server-library v3)
- Google Play receipt verification (google-api-python-client)
- Mock fallback when credentials not configured
- Receipt audit trail in DB
- €0.99/month or €9.99/year pricing
- Leaderboards (national + per-city) for subscribers

### PWA
- manifest.json with app icons
- Service worker with offline caching (static assets + map tiles)
- Apple mobile web app meta tags
- Installable on mobile devices

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Environment Variables for Production
```
# Apple App Store Server API
APPLE_KEY_ID=your_key_id
APPLE_ISSUER_ID=your_issuer_id
APPLE_BUNDLE_ID=com.cacaradar.app
APPLE_KEY_PATH=/path/to/AuthKey.p8
APPLE_ENVIRONMENT=Production

# Google Play Developer API
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
GOOGLE_PACKAGE_NAME=com.cacaradar.app
```

## Remaining Backlog
### P1
- [ ] Connect real email service for municipality verification codes
- [ ] App Store Server Notifications V2 webhook for subscription status changes
- [ ] Google Play RTDN webhook for subscription updates

### P2
- [ ] Additional report categories (trash, noise, etc.)
- [ ] Advanced analytics for municipalities
- [ ] User profile page with stats
