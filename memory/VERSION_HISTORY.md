# Caca Radar Version History

This log tracks shipped versions and the next unreleased batch across web, iOS, Android, and backend so we can audit changes and backtrack safely.

## Released

### 2026-04-21 — Production deploy `commit unknown in runtime`

- Web: `1.1.5-web.1`
- iOS: `1.1.2 (4)`
- Android: `1.1.4 (6)`
- Backend: `1.1.0-api.1`

Changes:
- Legal/compliance pages are live in production.
- Google sign-in works on web, Android, and iPhone production builds.
- Android release bundle/toolchain alignment and native iOS Google sign-in changes are included in the deployed app versions.

Production notes:
- `https://cacaradar.es/api/health` returned `{"status":"ok"}`
- `https://cacaradar.es/api/version` returned production metadata with the versions above
- Runtime commit reporting is still `unknown` in production and should be replaced with an injected `GIT_SHA` on the next deploy
- Repo metadata has been reconciled so web version tracking matches the deployed production version
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

### 2026-04-20 — Pending deploy after local validation (post-`06d7918`)

Impacted environments:
- Web `1.1.1-web.1`
- iOS `1.1.1 (3)`
- Android `1.1.1 (3)`
- Backend unchanged at `1.1.0-api.1`

Changes:
- Main map menu dropdown now caps its height dynamically so it does not conflict with the report button on smaller screens.
- Version numbers were incremented for the platforms touched by this batch and left unchanged for backend.
- Audit log updated so deploy/backtrack work can tie a shipped version to the specific UI changes in this batch.

Next deploy checklist:
- Record the deployed commit hash and production bundle hash
- Confirm `/api/version` returns web `1.1.1-web.1`, iOS `1.1.1 (3)`, Android `1.1.1 (3)`, backend `1.1.0-api.1`

### 2026-04-20 — Pending deploy

Impacted environments:
- Web `1.1.2-web.1`
- iOS `1.1.2 (4)`
- Android `1.1.2 (4)`

Changes:
- Automated build tracking enabled for web and mobile builds.
- Native iOS Google sign-in added and verified with Xcode build.

### 2026-04-20 — Pending deploy

Impacted environments:
- Android `1.1.3 (5)`

Changes:
- Android upload bundle rebuilt after iPhone Google sign-in validation.

### 2026-04-20 — Pending deploy

Impacted environments:
- Android `1.1.4 (6)`

Changes:
- Android Gradle wrapper and Android Gradle Plugin settings aligned with the build toolchain used for the release bundle.

### 2026-04-21 — Pending deploy

Impacted environments:
- Web `1.1.6-web.1`

Changes:
- Automated web build

### 2026-04-22 — Pending deploy

Impacted environments:
- Android `1.1.5 (7)`

Changes:
- Iterated Android upload bundle after Google Play version conflict

### 2026-04-23 — Pending deploy

Impacted environments:
- iOS `1.1.3 (5)`
- Android `1.1.6 (8)`

Changes:
- Rebuilt iOS bundle
- Rebuilt Android bundle

### 2026-04-24 — Pending

Release metadata:
- Commit SHA: `f109bbd56a962ff52cf6ea33aa86254774f73d3d-dirty`
- Deployment status: `pending`
- Rollback target: `617f900cd750cdd9a552c7db2a7057089286082b`

Exact versions:
- Web: `1.1.7-web.1`
- iOS: `1.1.3 (5)`
- Android: `1.1.6 (8)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: f109bbd56a962ff52cf6ea33aa86254774f73d3d-dirty
Deployment status: pending
Rollback target: 617f900cd750cdd9a552c7db2a7057089286082b
Versions:
• Web: `1.1.7-web.1`
• iOS: `1.1.3 (5)`
• Android: `1.1.6 (8)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `091f63092624d8ac8385a3058084f098275453db-dirty`
- Deployment status: `pending`
- Rollback target: `f109bbd56a962ff52cf6ea33aa86254774f73d3d`

Exact versions:
- Web: `1.1.8-web.1`
- iOS: `1.1.3 (5)`
- Android: `1.1.6 (8)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: 091f63092624d8ac8385a3058084f098275453db-dirty
Deployment status: pending
Rollback target: f109bbd56a962ff52cf6ea33aa86254774f73d3d
Versions:
• Web: `1.1.8-web.1`
• iOS: `1.1.3 (5)`
• Android: `1.1.6 (8)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `3ce842a12ac3a0080a95b39ccbef66450c4cd615-dirty`
- Deployment status: `pending`
- Rollback target: `091f63092624d8ac8385a3058084f098275453db`

Exact versions:
- Web: `1.1.9-web.1`
- iOS: `1.1.4 (6)`
- Android: `1.1.7 (9)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared mobile build.

Internal release notes:
- Prepared mobile build

Store submission notes:
```text
- Prepared mobile build.
```

Internal release notes block:
```text
Commit SHA: 3ce842a12ac3a0080a95b39ccbef66450c4cd615-dirty
Deployment status: pending
Rollback target: 091f63092624d8ac8385a3058084f098275453db
Versions:
• Web: `1.1.9-web.1`
• iOS: `1.1.4 (6)`
• Android: `1.1.7 (9)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared mobile build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `de390afba8c6beb2397a4060807769838e093ebc-dirty`
- Deployment status: `pending`
- Rollback target: `3ce842a12ac3a0080a95b39ccbef66450c4cd615`

Exact versions:
- Web: `1.1.10-web.1`
- iOS: `1.1.5 (7)`
- Android: `1.1.8 (10)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared mobile build.

Internal release notes:
- Prepared mobile build

Store submission notes:
```text
- Prepared mobile build.
```

Internal release notes block:
```text
Commit SHA: de390afba8c6beb2397a4060807769838e093ebc-dirty
Deployment status: pending
Rollback target: 3ce842a12ac3a0080a95b39ccbef66450c4cd615
Versions:
• Web: `1.1.10-web.1`
• iOS: `1.1.5 (7)`
• Android: `1.1.8 (10)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared mobile build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `95e6f0e2fbfa03d6e2043dccbfaa022f6becea1f-dirty`
- Deployment status: `pending`
- Rollback target: `de390afba8c6beb2397a4060807769838e093ebc`

Exact versions:
- Web: `1.1.11-web.1`
- iOS: `1.1.6 (8)`
- Android: `1.1.9 (11)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared mobile build.

Internal release notes:
- Prepared mobile build

Store submission notes:
```text
- Prepared mobile build.
```

Internal release notes block:
```text
Commit SHA: 95e6f0e2fbfa03d6e2043dccbfaa022f6becea1f-dirty
Deployment status: pending
Rollback target: de390afba8c6beb2397a4060807769838e093ebc
Versions:
• Web: `1.1.11-web.1`
• iOS: `1.1.6 (8)`
• Android: `1.1.9 (11)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared mobile build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `a892e6eedba9a828af23235e34bdc552b6bea1eb-dirty`
- Deployment status: `pending`
- Rollback target: `95e6f0e2fbfa03d6e2043dccbfaa022f6becea1f`

Exact versions:
- Web: `1.1.12-web.1`
- iOS: `1.1.7 (9)`
- Android: `1.1.10 (12)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared mobile build.

Internal release notes:
- Prepared mobile build

Store submission notes:
```text
- Prepared mobile build.
```

Internal release notes block:
```text
Commit SHA: a892e6eedba9a828af23235e34bdc552b6bea1eb-dirty
Deployment status: pending
Rollback target: 95e6f0e2fbfa03d6e2043dccbfaa022f6becea1f
Versions:
• Web: `1.1.12-web.1`
• iOS: `1.1.7 (9)`
• Android: `1.1.10 (12)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared mobile build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `01476a419c34622979a27b65fd0952cb73a3c7d9-dirty`
- Deployment status: `pending`
- Rollback target: `78fd47033335e9c44d4d83cfb04c4c8985e8ed04`

Exact versions:
- Web: `1.1.13-web.1`
- iOS: `1.1.7 (9)`
- Android: `1.1.10 (12)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: 01476a419c34622979a27b65fd0952cb73a3c7d9-dirty
Deployment status: pending
Rollback target: 78fd47033335e9c44d4d83cfb04c4c8985e8ed04
Versions:
• Web: `1.1.13-web.1`
• iOS: `1.1.7 (9)`
• Android: `1.1.10 (12)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `01476a419c34622979a27b65fd0952cb73a3c7d9-dirty`
- Deployment status: `pending`
- Rollback target: `78fd47033335e9c44d4d83cfb04c4c8985e8ed04`

Exact versions:
- Web: `1.1.14-web.1`
- iOS: `1.1.7 (9)`
- Android: `1.1.10 (12)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: 01476a419c34622979a27b65fd0952cb73a3c7d9-dirty
Deployment status: pending
Rollback target: 78fd47033335e9c44d4d83cfb04c4c8985e8ed04
Versions:
• Web: `1.1.14-web.1`
• iOS: `1.1.7 (9)`
• Android: `1.1.10 (12)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `01476a419c34622979a27b65fd0952cb73a3c7d9-dirty`
- Deployment status: `pending`
- Rollback target: `78fd47033335e9c44d4d83cfb04c4c8985e8ed04`

Exact versions:
- Web: `1.1.14-web.1`
- iOS: `1.1.8 (10)`
- Android: `1.1.11 (13)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Rebuilt iOS bundle.
- Rebuilt Android bundle.

Internal release notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle

Store submission notes:
```text
- Rebuilt iOS bundle.
- Rebuilt Android bundle.
```

Internal release notes block:
```text
Commit SHA: 01476a419c34622979a27b65fd0952cb73a3c7d9-dirty
Deployment status: pending
Rollback target: 78fd47033335e9c44d4d83cfb04c4c8985e8ed04
Versions:
• Web: `1.1.14-web.1`
• iOS: `1.1.8 (10)`
• Android: `1.1.11 (13)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `01476a419c34622979a27b65fd0952cb73a3c7d9-dirty`
- Deployment status: `pending`
- Rollback target: `78fd47033335e9c44d4d83cfb04c4c8985e8ed04`

Exact versions:
- Web: `1.1.14-web.1`
- iOS: `1.1.9 (11)`
- Android: `1.1.12 (14)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Rebuilt iOS bundle.
- Rebuilt Android bundle.

Internal release notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle

Store submission notes:
```text
- Rebuilt iOS bundle.
- Rebuilt Android bundle.
```

Internal release notes block:
```text
Commit SHA: 01476a419c34622979a27b65fd0952cb73a3c7d9-dirty
Deployment status: pending
Rollback target: 78fd47033335e9c44d4d83cfb04c4c8985e8ed04
Versions:
• Web: `1.1.14-web.1`
• iOS: `1.1.9 (11)`
• Android: `1.1.12 (14)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `aee8e46ad89109b94b973117d400567a1e96722e-dirty`
- Deployment status: `pending`
- Rollback target: `01476a419c34622979a27b65fd0952cb73a3c7d9`

Exact versions:
- Web: `1.1.15-web.1`
- iOS: `1.1.9 (11)`
- Android: `1.1.12 (14)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: aee8e46ad89109b94b973117d400567a1e96722e-dirty
Deployment status: pending
Rollback target: 01476a419c34622979a27b65fd0952cb73a3c7d9
Versions:
• Web: `1.1.15-web.1`
• iOS: `1.1.9 (11)`
• Android: `1.1.12 (14)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `aee8e46ad89109b94b973117d400567a1e96722e-dirty`
- Deployment status: `pending`
- Rollback target: `01476a419c34622979a27b65fd0952cb73a3c7d9`

Exact versions:
- Web: `1.1.15-web.1`
- iOS: `1.1.10 (12)`
- Android: `1.1.13 (15)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Rebuilt iOS bundle.
- Rebuilt Android bundle.

Internal release notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle

Store submission notes:
```text
- Rebuilt iOS bundle.
- Rebuilt Android bundle.
```

Internal release notes block:
```text
Commit SHA: aee8e46ad89109b94b973117d400567a1e96722e-dirty
Deployment status: pending
Rollback target: 01476a419c34622979a27b65fd0952cb73a3c7d9
Versions:
• Web: `1.1.15-web.1`
• iOS: `1.1.10 (12)`
• Android: `1.1.13 (15)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `9b62b38e46fb1e1d98b9050b5e02eb98d3f56639-dirty`
- Deployment status: `pending`
- Rollback target: `4c39a45cb411581e0ca8ea94c101bc9f46382054`

Exact versions:
- Web: `1.1.16-web.1`
- iOS: `1.1.10 (12)`
- Android: `1.1.13 (15)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Prepared web build.

Internal release notes:
- Prepared web build

Store submission notes:
```text
- Prepared web build.
```

Internal release notes block:
```text
Commit SHA: 9b62b38e46fb1e1d98b9050b5e02eb98d3f56639-dirty
Deployment status: pending
Rollback target: 4c39a45cb411581e0ca8ea94c101bc9f46382054
Versions:
• Web: `1.1.16-web.1`
• iOS: `1.1.10 (12)`
• Android: `1.1.13 (15)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `9b62b38e46fb1e1d98b9050b5e02eb98d3f56639-dirty`
- Deployment status: `pending`
- Rollback target: `4c39a45cb411581e0ca8ea94c101bc9f46382054`

Exact versions:
- Web: `1.1.16-web.1`
- iOS: `1.1.11 (13)`
- Android: `1.1.14 (16)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Rebuilt iOS bundle.
- Rebuilt Android bundle.

Internal release notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle

Store submission notes:
```text
- Rebuilt iOS bundle.
- Rebuilt Android bundle.
```

Internal release notes block:
```text
Commit SHA: 9b62b38e46fb1e1d98b9050b5e02eb98d3f56639-dirty
Deployment status: pending
Rollback target: 4c39a45cb411581e0ca8ea94c101bc9f46382054
Versions:
• Web: `1.1.16-web.1`
• iOS: `1.1.11 (13)`
• Android: `1.1.14 (16)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

