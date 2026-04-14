# Caca Radar - PRD (Product Requirements Document)

## Original Problem Statement
Build a mobile-first web app called "Caca Radar" for Spain that allows users to report dog feces in public places and view reports on a map. Available anywhere in Spain with auto-municipality tagging.

## Architecture
- **Frontend:** React 19 + TailwindCSS + Shadcn UI + Leaflet (OpenStreetMap)
- **Backend:** FastAPI + MongoDB + Object Storage (Emergent)
- **Auth:** JWT with optional registration (anonymous users allowed)
- **Geocoding:** Nominatim (OpenStreetMap) reverse geocoding
- **Payments:** App Store / Google Play (MOCKED in backend)

## User Personas
1. **Anonymous User:** Report poop, view map, vote — free
2. **Free Registered User:** Same + tracked identity
3. **Premium Subscriber (€0.99/mo or €9.99/yr):** Custom username, leaderboards (national + per-city)
4. **Ayuntamiento (Municipality):** Dashboard with stats, report management, moderation, flag review
5. **Admin:** Full access

## What's Been Implemented (2026-04-14)
### Core
- Full-screen map with Leaflet/OpenStreetMap, color-coded pins
- Report submission with GPS auto-capture + photo upload (Object Storage)
- Voting system ("Sigue ahí" / "Ya limpio"), auto-archive logic
- 8-language support (ES, EN, DE, NL, PL, AR, UK, RU) with RTL for Arabic

### Municipality System
- Auto-tagging reports to municipality via Nominatim reverse geocoding
- Ayuntamiento dashboard (/dashboard) with login
- Stats overview, reports table with filters, moderation actions
- Flag review queue with violation categories

### Moderation & Content Policy
- Photo upload policy warning (no license plates, faces, names, PII)
- Enhanced flag system with 7 reason categories
- Auto-hide after 3+ flags, manual moderate (hide/restore/dismiss)

### Subscription & Leaderboard
- Premium subscription page (€0.99/month, €9.99/year)
- National + per-city leaderboards (subscriber-only)
- Subscription activation (MOCKED — verified via App Store/Google Play in production)

### Auth
- JWT auth with httpOnly cookies
- Admin + municipality + user roles
- Brute force protection
- Demo municipality seeded (Madrid)

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Mocked Integrations
- User subscription (POST /api/users/subscribe) — production will verify via App Store receipts
- Municipality subscription (POST /api/municipality/subscribe)

## Prioritized Backlog
### P0 (Done)
- [x] Map, reports, voting, flagging
- [x] Municipality auto-tagging
- [x] Ayuntamiento dashboard
- [x] Subscription & leaderboards
- [x] Multi-language, content policy

### P1 (High Priority)
- [ ] PWA manifest + service worker for offline/installable
- [ ] App Store receipt verification for real payments
- [ ] Push notifications for nearby reports
- [ ] Municipality self-registration flow with verification

### P2 (Medium)
- [ ] Additional report categories (trash, noise, etc.)
- [ ] Advanced analytics dashboard for municipalities
- [ ] User profile page with stats and badges
- [ ] Social sharing of reports

### P3 (Low)
- [ ] Heatmap visualization
- [ ] Email notifications for municipalities
- [ ] Export data as CSV for municipalities
