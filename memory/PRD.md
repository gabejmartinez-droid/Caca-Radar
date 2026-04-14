# Caca Radar - PRD

## Architecture
- **Frontend:** React 19 + TailwindCSS + Shadcn UI + Leaflet + PWA
- **Backend:** FastAPI + MongoDB + Object Storage + Apple/Google receipt verification
- **Services:** scoring_service.py, antispam_service.py, validation_service.py, ranking_service.py

## Gamification System (Implemented)
### Scoring: 10 base + 5 photo + 3 description (max 5/day, 1.5x subscriber)
### Trust: 0-100 (start 50), tiers: trusted/normal/low/restricted
### Ranks: 10 Spanish titles by percentile (weekly recalc)
### Anti-spam: 60s cooldown, GPS check, proximity duplicate detection, spam pattern detection

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Key Endpoints
- POST /api/reports (with description, anti-spam, scoring)
- POST /api/reports/{id}/validate (confirm/reject with weighted consensus)
- POST /api/reports/{id}/upvote | /downvote
- GET /api/users/profile (full gamification stats)
- GET /api/leaderboard/national (sorted by total_score)
- POST /api/admin/recalculate-ranks

## Remaining
- [ ] Connect email service for municipality verification codes
- [ ] App Store/Google Play notification webhooks
