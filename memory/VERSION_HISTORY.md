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

### 2026-05-01 — Pending

Impacted environments:
- Web `1.1.23-web.1`
- iOS `1.1.33 (35)`
- Android `1.1.35 (37)`
- Backend `1.1.2-api.1`

Changes:
- Apple Watch companion is now embedded into the main iPhone archive path with a proper watch extension, so TestFlight builds can carry the watch app.
- Local iOS archive validation succeeded with the watch companion bundled.
- Android version was bumped and the phone bundle was refreshed to keep mobile release tracking aligned.
- Watch app metadata was corrected so App Store Connect can recognize it as a valid watch app bundle:
  - proper `WKWatchKitApp` key
  - required display names
  - watch icon asset catalog
- Follow-up App Store Connect fixes adjusted the watch bundle metadata to match Apple's expected schema:
  - removed invalid top-level `CFBundleIconName` from the watch app plist
  - moved the watch location usage string to the watch extension plist
  - replaced the invalid extension principal-class key with `WKExtensionDelegateClassName`
  - added the missing Series 4 long-look watch icons
- Added an explicit bundled `AppIcon50x50@2x.png` watch resource and plist reference so the 44mm long-look icon is present in the final watch app bundle that App Store Connect validates.
- Replaced the watch app's asset-catalog-driven icon setup with an explicit set of bundled raw `AppIcon*.png` files and a full `CFBundleIconFiles` list so the 44mm long-look `50x50@2x` icon is shipped in the simplest form Apple expects.
- Restored the watch app's `WatchAppIcon` asset-catalog identity alongside the explicit raw icon files so App Store Connect sees both `CFBundleIconName` and the concrete bundled icon files in the final watch bundle.
- Added an explicit root-level `long-look-44mm@2x.png` resource to the watch app bundle and referenced it in the plist so the exact Series 4 long-look filename Apple names in `ITMS-90741` is present after archiving.
- Recreated the watch icon asset catalog through Xcode so the watch target now uses Xcode-generated universal watchOS icon slots instead of the earlier hand-authored role/subtype layout.
- Fixed the Apple Watch quick-report flow so location permission is handled asynchronously instead of failing with the generic “operation couldn’t be completed” error when the watch asks for GPS access.
- Made the Apple Watch location lookup more resilient by accepting a fresh cached fix, starting live updates, and timing out cleanly instead of hanging forever on “Buscando tu ubicación”.
- Added a saved `preferred_language` user preference that now travels through auth/profile responses, persists to the backend, and restores automatically when the same user signs in on another device.
- Synced the saved language into both companion bridges so the Apple Watch and Wear OS quick-report UIs can mirror the phone app language instead of falling back to device defaults.

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

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8-dirty`
- Deployment status: `pending`
- Rollback target: `9b62b38e46fb1e1d98b9050b5e02eb98d3f56639`

Exact versions:
- Web: `1.1.17-web.1`
- iOS: `1.1.11 (13)`
- Android: `1.1.14 (16)`
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
Commit SHA: 3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8-dirty
Deployment status: pending
Rollback target: 9b62b38e46fb1e1d98b9050b5e02eb98d3f56639
Versions:
• Web: `1.1.17-web.1`
• iOS: `1.1.11 (13)`
• Android: `1.1.14 (16)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8-dirty`
- Deployment status: `pending`
- Rollback target: `9b62b38e46fb1e1d98b9050b5e02eb98d3f56639`

Exact versions:
- Web: `1.1.17-web.1`
- iOS: `1.1.12 (14)`
- Android: `1.1.15 (17)`
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
Commit SHA: 3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8-dirty
Deployment status: pending
Rollback target: 9b62b38e46fb1e1d98b9050b5e02eb98d3f56639
Versions:
• Web: `1.1.17-web.1`
• iOS: `1.1.12 (14)`
• Android: `1.1.15 (17)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `d373fe29034346e804b8b4b7cf5875af3cd1189f-dirty`
- Deployment status: `pending`
- Rollback target: `3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8`

Exact versions:
- Web: `1.1.17-web.1`
- iOS: `1.1.13 (15)`
- Android: `1.1.16 (18)`
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
Commit SHA: d373fe29034346e804b8b4b7cf5875af3cd1189f-dirty
Deployment status: pending
Rollback target: 3dcdbed1fbf5dbdd46ad23f0716403bd2e8f86b8
Versions:
• Web: `1.1.17-web.1`
• iOS: `1.1.13 (15)`
• Android: `1.1.16 (18)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-26 — Pending

Release metadata:
- Commit SHA: `b37b9746971c479a890dc264c2188067d1068aa2-dirty`
- Deployment status: `pending`
- Rollback target: `d373fe29034346e804b8b4b7cf5875af3cd1189f`

Exact versions:
- Web: `1.1.17-web.1`
- iOS: `1.1.14 (16)`
- Android: `1.1.17 (19)`
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
Commit SHA: b37b9746971c479a890dc264c2188067d1068aa2-dirty
Deployment status: pending
Rollback target: d373fe29034346e804b8b4b7cf5875af3cd1189f
Versions:
• Web: `1.1.17-web.1`
• iOS: `1.1.14 (16)`
• Android: `1.1.17 (19)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-27 — Pending

Release metadata:
- Commit SHA: `27745cae771223da0a9c586216066cc4087413e5-dirty`
- Deployment status: `pending`
- Rollback target: `2d9cd1504f2271a36c43682b7d99837d3071a567`

Exact versions:
- Web: `1.1.17-web.1`
- iOS: `1.1.15 (17)`
- Android: `1.1.18 (20)`
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
Commit SHA: 27745cae771223da0a9c586216066cc4087413e5-dirty
Deployment status: pending
Rollback target: 2d9cd1504f2271a36c43682b7d99837d3071a567
Versions:
• Web: `1.1.17-web.1`
• iOS: `1.1.15 (17)`
• Android: `1.1.18 (20)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-27 — Pending

Release metadata:
- Commit SHA: `e5b324e1613a58b72d87462d8d01d7c2edc7e349-dirty`
- Deployment status: `pending`
- Rollback target: `27745cae771223da0a9c586216066cc4087413e5`

Exact versions:
- Web: `1.1.18-web.1`
- iOS: `1.1.15 (17)`
- Android: `1.1.18 (20)`
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
Commit SHA: e5b324e1613a58b72d87462d8d01d7c2edc7e349-dirty
Deployment status: pending
Rollback target: 27745cae771223da0a9c586216066cc4087413e5
Versions:
• Web: `1.1.18-web.1`
• iOS: `1.1.15 (17)`
• Android: `1.1.18 (20)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-28 — Pending

Release metadata:
- Commit SHA: `1ccc0d357f8e07de413223245430b38e16b56da6-dirty`
- Deployment status: `pending`
- Rollback target: `c326b9da565653753cea632aa438b6852ca4c5a3`

Exact versions:
- Web: `1.1.19-web.1`
- iOS: `1.1.15 (17)`
- Android: `1.1.18 (20)`
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
Commit SHA: 1ccc0d357f8e07de413223245430b38e16b56da6-dirty
Deployment status: pending
Rollback target: c326b9da565653753cea632aa438b6852ca4c5a3
Versions:
• Web: `1.1.19-web.1`
• iOS: `1.1.15 (17)`
• Android: `1.1.18 (20)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-04-28 — Pending

Release metadata:
- Commit SHA: `1ccc0d357f8e07de413223245430b38e16b56da6-dirty`
- Deployment status: `pending`
- Rollback target: `c326b9da565653753cea632aa438b6852ca4c5a3`

Exact versions:
- Web: `1.1.19-web.1`
- iOS: `1.1.16 (18)`
- Android: `1.1.19 (21)`
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
Commit SHA: 1ccc0d357f8e07de413223245430b38e16b56da6-dirty
Deployment status: pending
Rollback target: c326b9da565653753cea632aa438b6852ca4c5a3
Versions:
• Web: `1.1.19-web.1`
• iOS: `1.1.16 (18)`
• Android: `1.1.19 (21)`
• Backend: `1.1.0-api.1`
Notes:
- Rebuilt iOS bundle
- Rebuilt Android bundle
```

### 2026-04-28 — Pending

Release metadata:
- Commit SHA: `d0928dc8c57c6649fb7ffa13d7104e12cfdcb204-dirty`
- Deployment status: `pending`
- Rollback target: `9fe5f194be627041e048eaa9d95234f710439127`

Exact versions:
- Web: `1.1.20-web.1`
- iOS: `1.1.16 (18)`
- Android: `1.1.19 (21)`
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
Commit SHA: d0928dc8c57c6649fb7ffa13d7104e12cfdcb204-dirty
Deployment status: pending
Rollback target: 9fe5f194be627041e048eaa9d95234f710439127
Versions:
• Web: `1.1.20-web.1`
• iOS: `1.1.16 (18)`
• Android: `1.1.19 (21)`
• Backend: `1.1.0-api.1`
Notes:
- Prepared web build
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `951a3d2a5cf66c38c9e1da3c213d33d553b63f35-dirty`
- Deployment status: `pending`
- Rollback target: `e4943c5d20c5bcc658a18907795d1928b40c038c`

Exact versions:
- Web: `1.1.20-web.1`
- iOS: `1.1.17 (19)`
- Android: `1.1.19 (21)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Incremented iOS build for Sign in with Apple rollout.

Internal release notes:
- Incremented iOS build for Sign in with Apple rollout

Store submission notes:
```text
- Incremented iOS build for Sign in with Apple rollout.
```

Internal release notes block:
```text
Commit SHA: 951a3d2a5cf66c38c9e1da3c213d33d553b63f35-dirty
Deployment status: pending
Rollback target: e4943c5d20c5bcc658a18907795d1928b40c038c
Versions:
• Web: `1.1.20-web.1`
• iOS: `1.1.17 (19)`
• Android: `1.1.19 (21)`
• Backend: `1.1.0-api.1`
Notes:
- Incremented iOS build for Sign in with Apple rollout
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `b0ee962ecbcc0bd733ee1fadb01abdc791628a28-dirty`
- Deployment status: `pending`
- Rollback target: `a5a0747ef0ebf64c62488f805a961571f760847c`

Exact versions:
- Web: `1.1.20-web.1`
- iOS: `1.1.18 (20)`
- Android: `1.1.20 (22)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Notification settings fixes and saved location fallback.

Internal release notes:
- Notification settings fixes and saved location fallback

Store submission notes:
```text
- Notification settings fixes and saved location fallback.
```

Internal release notes block:
```text
Commit SHA: b0ee962ecbcc0bd733ee1fadb01abdc791628a28-dirty
Deployment status: pending
Rollback target: a5a0747ef0ebf64c62488f805a961571f760847c
Versions:
• Web: `1.1.20-web.1`
• iOS: `1.1.18 (20)`
• Android: `1.1.20 (22)`
• Backend: `1.1.0-api.1`
Notes:
- Notification settings fixes and saved location fallback
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `b0ee962ecbcc0bd733ee1fadb01abdc791628a28-dirty`
- Deployment status: `pending`
- Rollback target: `a5a0747ef0ebf64c62488f805a961571f760847c`

Exact versions:
- Web: `1.1.20-web.1`
- iOS: `1.1.19 (21)`
- Android: `1.1.21 (23)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Notification location fallback and settings updates.

Internal release notes:
- Notification location fallback and settings updates

Store submission notes:
```text
- Notification location fallback and settings updates.
```

Internal release notes block:
```text
Commit SHA: b0ee962ecbcc0bd733ee1fadb01abdc791628a28-dirty
Deployment status: pending
Rollback target: a5a0747ef0ebf64c62488f805a961571f760847c
Versions:
• Web: `1.1.20-web.1`
• iOS: `1.1.19 (21)`
• Android: `1.1.21 (23)`
• Backend: `1.1.0-api.1`
Notes:
- Notification location fallback and settings updates
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `eab1e9fc35c2794321c1eb41184cbe5709d048e4-dirty`
- Deployment status: `pending`
- Rollback target: `e7d1a098a5e14523c3b478e88cc395be70f27b0a`

Exact versions:
- Web: `1.1.20-web.1`
- iOS: `1.1.20 (22)`
- Android: `1.1.22 (24)`
- Backend: `1.1.0-api.1`

User-facing release notes:
- Make social share buttons auto-fit under zoom.

Internal release notes:
- Make social share buttons auto-fit under zoom

Store submission notes:
```text
- Make social share buttons auto-fit under zoom.
```

Internal release notes block:
```text
Commit SHA: eab1e9fc35c2794321c1eb41184cbe5709d048e4-dirty
Deployment status: pending
Rollback target: e7d1a098a5e14523c3b478e88cc395be70f27b0a
Versions:
• Web: `1.1.20-web.1`
• iOS: `1.1.20 (22)`
• Android: `1.1.22 (24)`
• Backend: `1.1.0-api.1`
Notes:
- Make social share buttons auto-fit under zoom
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `dd776de4253916895149f0787e64f57617d4549b-dirty`
- Deployment status: `pending`
- Rollback target: `eab1e9fc35c2794321c1eb41184cbe5709d048e4`

Exact versions:
- Web: `1.1.21-web.1`
- iOS: `1.1.21 (23)`
- Android: `1.1.23 (25)`
- Backend: `1.1.1-api.1`

User-facing release notes:
- Scaffold watch companion quick report flow.

Internal release notes:
- Scaffold watch companion quick report flow

Store submission notes:
```text
- Scaffold watch companion quick report flow.
```

Internal release notes block:
```text
Commit SHA: dd776de4253916895149f0787e64f57617d4549b-dirty
Deployment status: pending
Rollback target: eab1e9fc35c2794321c1eb41184cbe5709d048e4
Versions:
• Web: `1.1.21-web.1`
• iOS: `1.1.21 (23)`
• Android: `1.1.23 (25)`
• Backend: `1.1.1-api.1`
Notes:
- Scaffold watch companion quick report flow
```

### 2026-05-01 — Pending

Release metadata:
- Commit SHA: `5f3e6b1106317da00a5caf281dcdc7dd584a5d60-dirty`
- Deployment status: `pending`
- Rollback target: `dd776de4253916895149f0787e64f57617d4549b`

Exact versions:
- Web: `1.1.21-web.1`
- iOS: `1.1.22 (24)`
- Android: `1.1.24 (26)`
- Backend: `1.1.1-api.1`

User-facing release notes:
- Integrate watch companion targets.

Internal release notes:
- Integrate watch companion targets

Store submission notes:
```text
- Integrate watch companion targets.
```

Internal release notes block:
```text
Commit SHA: 5f3e6b1106317da00a5caf281dcdc7dd584a5d60-dirty
Deployment status: pending
Rollback target: dd776de4253916895149f0787e64f57617d4549b
Versions:
• Web: `1.1.21-web.1`
• iOS: `1.1.22 (24)`
• Android: `1.1.24 (26)`
• Backend: `1.1.1-api.1`
Notes:
- Integrate watch companion targets
```
