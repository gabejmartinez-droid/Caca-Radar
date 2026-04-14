# Caca Radar - PRD (Product Requirements Document)

## Original Problem Statement
Build a mobile-first web app called "Caca Radar" for Spain that allows users to report dog feces in public places and view reports on a map.

## Architecture
- **Frontend:** React 19 + TailwindCSS + Shadcn UI + Leaflet (OpenStreetMap)
- **Backend:** FastAPI + MongoDB + Object Storage (Emergent)
- **Auth:** JWT with optional registration (anonymous users allowed)

## User Personas
1. **Anonymous User:** Can report dog feces, view map, vote on reports
2. **Registered User:** Same as anonymous + tracked votes, persistent identity
3. **Admin:** Full access to moderation (flagged content management)

## Core Requirements (Static)
- ✅ Map view centered on Madrid with OpenStreetMap
- ✅ Color-coded pins (Red <24h, Orange 1-3d, Green >3d)
- ✅ Report submission with GPS auto-capture
- ✅ Optional photo upload
- ✅ Confirmation voting system ("Sigue ahí" / "Ya limpio")
- ✅ Auto-archive after 7 days or 3+ "cleaned" votes
- ✅ Flag/moderation system
- ✅ Spanish (Castilian) UI

## What's Been Implemented (2026-04-14)
- Full backend API with auth, reports CRUD, voting, flagging
- Map page with Leaflet, floating "Reportar" FAB
- Report drawer with photo upload
- Details drawer with voting buttons
- Login/Register pages with JWT auth
- Anonymous user support with cookie tracking
- Object Storage integration for photos
- Admin seeding on startup

## Prioritized Backlog
### P0 (Critical) - Completed
- [x] Core map functionality
- [x] Report submission
- [x] Voting system

### P1 (High Priority)
- [ ] PWA manifest and service worker for offline support
- [ ] Push notifications for nearby reports

### P2 (Medium Priority)
- [ ] Admin dashboard for moderation
- [ ] Report categories (trash, noise, etc.)
- [ ] City selection / multi-city support

### P3 (Low Priority)
- [ ] Statistics dashboard
- [ ] Social sharing
- [ ] Leaderboard for reporters

## Next Tasks
1. Add PWA manifest for installable app
2. Implement admin moderation panel
3. Add service worker for offline map caching
