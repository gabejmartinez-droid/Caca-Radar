# Caca Radar - PRD

## Original Problem Statement
Mobile-first web app for Spain — report dog feces, view on map, gamification, municipality dashboards.

## Pages
- / (Map), /login, /register, /profile, /subscribe, /leaderboard, /rankings
- /dashboard/login, /dashboard/register, /dashboard, /dashboard/analytics
- /admin/login (2FA), /admin (owner dashboard)

## Architecture
- `server.py` — Routes + startup | `deps.py` — Shared DB/auth/models
- `*_service.py` — Gamification, email, rankings, clean route, etc.

## Implemented
- Map with color-coded pins, heatmaps, PWA, 11 languages
- Gamification (ranks, badges, leaderboards), premium/free tiers
- Municipality dashboard (€50/month) with analytics, moderation
- City/Barrio rankings (premium), Clean Route, rank notifications
- Username system, photo uploads, 30-day archive, Resend emails
- **Admin panel** (jefe@cacaradar.es) with 2FA email verification
  - Global stats, user management, photo violation moderation, subscription analytics
- Municipality verification emails include dashboard link
- Custom app icon (favicon + PWA + headers)

## Backlog
- P1: Configure real Apple/Google webhook URLs
- P2: Implement real receipt verification (currently mocked)
