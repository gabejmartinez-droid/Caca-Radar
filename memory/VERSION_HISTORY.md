# Caca Radar Version History

This log tracks shipped versions and the next unreleased batch across web, iOS, Android, and backend so we can audit changes and backtrack safely.

## Released

### 2026-04-19 — Production deploy `ba36ba4`

- Web: `1.1.0-web.1`
- iOS: `1.1.0 (2)`
- Android: `1.1.0 (2)`
- Backend: `1.1.0-api.1`

Changes:
- Report voting updated so upvotes act as verification and downvotes can route into the “already gone” flow.
- Language selector order updated to Spanish, English, Basque, Valenciano, Catalan, then the remaining languages.
- Version metadata surfaced in the menu and `/api/version`.
- Privacy and account deletion routes remained live and available for audit.

Production notes:
- Deployed and verified on `cacaradar.es`
- Backend health and version endpoints returned production values
- Frontend bundle verified as updated in production

## Unreleased / Next Batch

### 2026-04-20 — Pending deploy after local validation

Impacted environments:
- Web
- iOS
- Android
- Backend

Planned changes:
- Terms placeholder replaced with full Spanish “Términos de uso y aviso legal” page and linked from Help/Profile.
- Activity banner behavior tightened:
  - “new reports near you” dismisses reliably on web click
  - “new reports near you” appears at most once per day per user session history
- Report confirmations refresh `refreshed_at` so verified/confirmed reports become fresh again.
- Main map report dots reduced by 50%.
- Community Impact and related legal/help shell text expanded for all supported UI languages.

Audit reminder:
- After deployment, record the exact deployed commit hash, production bundle hash, and any version number bumps here.
