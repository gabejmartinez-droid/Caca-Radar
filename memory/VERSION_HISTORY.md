# Caca Radar Version History

This log tracks shipped versions and the next unreleased batch across web, iOS, Android, and backend so we can audit changes and backtrack safely.

## Released

### 2026-05-07 — Pending

- Web: `1.1.80-web.1`
- iOS: `1.1.98 (100)`
- Android: `1.1.97 (99)`
- Backend: `1.1.30-api.1`

Changes:
- Split Apple backend key configuration so APNs keeps using `APPLE_KEY_ID` / `APPLE_KEY_PATH` while App Store subscription verification now uses `APPLE_STOREKIT_KEY_ID` / `APPLE_STOREKIT_KEY_PATH`.
- Updated the backend Apple integration status endpoint and operator guidance so it reports StoreKit verification readiness separately from APNs push readiness.
- Hid municipality registration from the iPhone app review path and removed the remaining iPhone-visible Google Play / cross-store cancellation wording from support and account-deletion surfaces.

### 2026-05-06 — Pending

- Web: `1.1.73-web.1`
- iOS: `1.1.91 (93)`
- Android: `1.1.90 (92)`
- Backend: `1.1.26-api.1`

Changes:
- Allow users to mark their own reports as no longer there while still blocking self-upvotes.
- Remove the municipal-operator advisory from the report details window.
- Show all pending report flags, including spam, in the admin moderation dashboard.
- Add admin photo approvals, hide pending report photos until approved, and remove reports when a photo is rejected.
- Switch the admin dashboard interface copy to English by default.
- Fix a `MapPage` temporal dead-zone crash where the photo moderation notice string was referenced before it was declared, causing a white screen on production page load.
- Vendor the Capacitor iOS SwiftPM binary frameworks locally so Xcode Cloud no longer needs GitHub release downloads to resolve `Capacitor` and `Cordova` during iOS builds.
- Remove individual poop-report sharing options and drop the extra admin proximity advisory from the report details drawer.
- Fix the “ya no está / cleaned” report action by routing it through the live downvote flow, allowing users to mark their own reports as cleaned while still blocking self-upvotes, and removing a legacy backend crash in the old cleaned-vote endpoint.
- Restore visibility of approved and legacy report photos for public viewers while keeping pending moderation photos admin-only.
- Archive reports after 14 days of inactivity, using the last confirmation/refresh time when available so reconfirmed reports stay alive.
- Reduce the report-clearing threshold to a single nearby downvote instead of requiring two.
- Run the 14-day cleanup before public, municipal, ranking, and admin dashboard queries so stale reports disappear consistently.
- Tighten client-side report photo compression to smaller square images and a lower target size to reduce storage usage.
- Normalize uploaded report photos on the server, strip EXIF/metadata, and convert them to AVIF when supported by the runtime or WebP/JPEG as fallbacks to reduce storage further.
- Make `/api/city-reports/share-image.png` public so social crawlers can fetch the city-report Open Graph image without authentication.
- Implement a real native Apple StoreKit subscription flow on iPhone, including App Store product loading, purchase handling, and restore purchases.
- Route iPhone premium upgrades through `/api/users/subscribe/apple` using real transaction data instead of the old mock subscribe endpoint.
- Hide the custom free-trial CTA on iPhone unless the App Store product actually reports an introductory offer, so the review build does not promise unsupported trial behavior.
- Configure the default iPhone monthly StoreKit product ID as `com.jefe.cacaradar.premium.monthly`.

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

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.58-web.1`
- iOS `1.1.75 (77)`
- Android `1.1.75 (77)`
- Backend `1.1.16-api.1`

Changes:
- Tightened barrio report mini-map bounds padding so barrio boundaries fill roughly 90% of the preview frame instead of sitting with the looser city-level fit.
- Increased heatmap intensity by 25% by raising the shared density scale from `0.5` to `0.625`, partially undoing the earlier density reduction without going all the way back to the old hotter map.
- Increased the report details popup height on web/desktop so the vote controls remain fully visible and clickable instead of being clipped under the card edge.
- Removed the community advisory block from the report popup again to recover vertical space for the actual report actions.
- Fixed the watch location race helper to use `withThrowingTaskGroup`, which matches the fact that the body rethrows the final chosen location/error.
- Marked the `group.next()` await with `try` so the throwing task-group iteration compiles cleanly in Xcode Cloud.
- Fixed the Apple Watch companion bridge build by importing `CoreLocation` in the watch session bridge where the new raced phone-coordinate helper returns `CLLocationCoordinate2D`.
- Updated the Xcode Cloud pre-`xcodebuild` scripts to disable signing only for Debug configurations inside the CI workspace, so the generic unsigned `xcodebuild build` step can reach real compile errors without disturbing Release/archive signing.

Verification:
- Local `xcodebuild build` with Debug signing disabled now gets past the old signing failure and the watch companion compile error is resolved.
- A full local unsigned build is still noisy under sandboxed package/cache restrictions, but no further Swift compile error surfaced after the import fix.

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.55-web.1`
- iOS `1.1.69 (71)`
- Android `1.1.72 (74)`
- Backend `1.1.16-api.1`

Changes:
- Changed Apple Watch quick reporting to race the watch GPS lookup against a phone-coordinate request and use whichever location arrives first before sending a single report.
- Shortened the watch-only location wait and reduced the phone-side location timeout so the fallback path feels noticeably faster without adding continuous background location syncing.
- Kept the final report submission as a single action to avoid duplicate reports while still preserving the iPhone-backed fallback when watch GPS drags.

Verification:
- iOS native compile check passed.
- Android release bundle rebuilt successfully.

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.54-web.1`
- iOS `1.1.68 (70)`
- Android `1.1.71 (73)`
- Backend `1.1.16-api.1`

Changes:
- Temporarily disabled the Spain-only GPS gate across the shared app so App Review can access the main product flows without being blocked by the location restriction.
- Moved the gate behind a single frontend configuration flag so it can be re-enabled later by setting `REACT_APP_ENABLE_SPAIN_LOCATION_GATE=true`.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.53-web.1`
- iOS `1.1.67 (69)`
- Android `1.1.70 (72)`
- Backend `1.1.16-api.1`

Changes:
- Reworked the municipal pricing section into the new Municipal Básico, Municipal Plus, and Municipal Pro tiers with exact monthly and annual prices shown as `+ IVA`.
- Visually emphasized annual pricing as the recommended option while keeping monthly pricing visible as an alternative on each municipal card.
- Updated each municipal CTA to open a tier-specific email to `jefe@cacaradar.es` including the selected plan, population range, annual price, monthly price, and `+ IVA` in the prefilled message.
- Added the official-population guidance line, the direct payment/invoice contact line, and the tailored-quote note for the Pro tier without changing consumer subscription plans.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.52-web.1`
- iOS `1.1.66 (68)`
- Android `1.1.69 (71)`
- Backend `1.1.16-api.1`

Changes:
- Stopped exposing community reports, report details, report share payloads, and report photos to anonymous/public visitors.
- Required authenticated access for report lists, report detail views, city-report share summaries, and report media, while keeping municipal and other authenticated flows working.
- Replaced public report and city-share landing pages with generic marketing previews so shared links no longer leak live report content to crawlers or logged-out visitors.
- Updated the map, city-report, and legal copy so the app now clearly states that reports are private to authenticated or authorized municipal access.

Verification:
- Backend compile passed.
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-04 — Pending

Impacted environments:
- Web `1.1.51-web.1`
- iOS `1.1.65 (67)`
- Android `1.1.68 (70)`
- Backend `1.1.15-api.1`

Changes:
- Finalized the public legal disclosures with specific infrastructure, provider, region, and retention facts: Emergent hosting, MongoDB Atlas database, Resend transactional email, EU/Spain regional posture, 30-day logs, 12-month support email retention, 30-day backups, and 6-year accounting retention.
- Tightened the published privacy and terms wording to match the stricter public-report visibility model, including approximate public locations and limited anonymous photo exposure.
- Updated the account deletion and cookies pages so the stated retention and provider details match the actual operating policy.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.49-web.1`
- iOS `1.1.63 (65)`
- Android `1.1.66 (68)`
- Backend `1.1.14-api.1`

Changes:
- Changed new-report push notifications so they only fire within 50 m of a user's saved alert places, with the currently selected alert place kept as a fallback when no saved locations exist yet.
- Removed the old user-adjustable alert-radius UI and updated notification settings copy to explain the fixed 50 m saved-place behavior more clearly.

Verification:
- Backend compile passed.
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.48-web.1`
- iOS `1.1.62 (64)`
- Android `1.1.65 (67)`
- Backend `1.1.13-api.1`

Changes:
- Simplified the municipal pricing cards so they now show annual pricing only, removing the approximate monthly equivalents from the UI.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.46-web.1`
- iOS `1.1.60 (62)`
- Android `1.1.63 (65)`
- Backend `1.1.13-api.1`

Changes:
- Reworked the municipal portion of the pricing page into three explicit Ayuntamiento tiers based on population: Small, Medium, and Large Municipality.
- Added annual pricing and per-tier feature lists while making it clear that municipal tools are activated during onboarding and can be configured progressively.
- Highlighted the medium municipality tier as the most common option for towns and small cities.
- Routed every municipal CTA to the manual email contact flow at `jefe@cacaradar.es` for subscriptions, payment questions, and invoice handling.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.45-web.1`
- iOS `1.1.59 (61)`
- Android `1.1.62 (64)`
- Backend `1.1.13-api.1`

Changes:
- Updated the download page to showcase the companion watch app as the fastest way to report from your current location on Apple Watch and Android watches.
- Expanded the municipal subscription offer to highlight custom municipality dashboards, cleaner/management workflows for marking cleaned areas, and support for custom features.
- Removed the content advisory from the report drawer so the floating report window is smaller and easier to use.
- Moved the reporting/photo content advisory to the login screen where it is visible before users start submitting reports.
- Updated municipal pricing display to `75 €/mes` or `1000 €/año`.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.44-web.1`
- iOS `1.1.58 (60)`
- Android `1.1.61 (63)`
- Backend `1.1.13-api.1`

Changes:
- Added a dedicated `municipal_worker` account type for standard users so municipal cleaners can clear reports without the 5 m proximity rule inside their assigned municipality.
- Added admin controls in the users tab to toggle a user between standard and municipal-worker status and assign the municipality/province scope for that account.
- Reduced the anti-spam report cooldown from 30 seconds to 15 seconds.
- Reduced heatmap intensity by 50%, reversing the earlier density increase.

Verification:
- Backend compile passed.
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully.

### 2026-05-03 — Pending

Impacted environments:
- Web `1.1.43-web.1`
- iOS `1.1.57 (59)`
- Android `1.1.60 (62)`
- Backend `1.1.12-api.1`

Changes:
- Expanded the report details popup on mobile so the report-vote controls stay visible and reachable inside the floating window on iPhone.
- Added per-user report-vote state loading so web and mobile can clearly show when a user already marked a report as helpful or not helpful.
- Prevented successful "not helpful" votes from looking broken when they archive a report by refreshing the map and closing the details popup cleanly instead of re-requesting a now-missing record.
- Added `/api/reports/{report_id}/my-report-vote` so the frontend can mirror vote state across platforms.

Verification:
- Backend compile passed.
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt successfully after switching to a fresh Gradle home.
- Local iOS CLI build still hits the existing watch-target product-type issue and is not a reliable signal for this change.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.42-web.1`
- iOS `1.1.56 (58)`
- Android `1.1.59 (61)`
- Backend `1.1.11-api.1`

Changes:
- Removed the on-screen watch debug text from Apple Watch and Wear OS now that watch reporting is functioning.
- Tuned Apple Watch location selection to reuse a recent watch location for longer and fall back to the iPhone path sooner when the watch GPS drags, reducing the time spent on “Buscando tu ubicación…”.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Standalone watchOS CLI build still fails on the existing local duplicate-output Xcode project issue and is not a reliable signal for this change.
- Android release bundle rebuild was attempted but blocked by repeated local Gradle cache corruption in `/tmp/cacaradar-gradle87`.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.41-web.1`
- iOS `1.1.55 (57)`
- Android `1.1.58 (60)`
- Backend `1.1.11-api.1`

Changes:
- Explicitly registered the iOS `CompanionBridge` Capacitor plugin in the app bridge controller so native companion auth sync can actually persist tokens and preferences for the Apple Watch flow.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt on the new version.
- Local iOS CLI build still hits the existing watch target product-type limitation and is not a reliable signal for this change.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.40-web.1`
- iOS `1.1.54 (56)`
- Android `1.1.57 (59)`
- Backend `1.1.11-api.1`

Changes:
- Fixed native 401 handling so the app no longer clears watch companion auth state just because a request failed before a refresh token existed locally.
- Native session bootstrap now falls back to the phone's refresh-cookie session, allowing the app to mint native companion tokens even when the access cookie is gone or the native token store is empty.

Verification:
- Backend compile passed.
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.39-web.1`
- iOS `1.1.53 (55)`
- Android `1.1.56 (58)`
- Backend `1.1.10-api.1`

Changes:
- Fixed the native startup auth race where the app could call `/auth/me` before bootstrapping native companion tokens, get a 401, and clear watch companion auth state back to false.
- Native auth refresh now avoids wiping companion state when no refresh token exists yet, allowing the cookie-backed native bootstrap flow to complete first.

Verification:
- Frontend mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.38-web.1`
- iOS `1.1.52 (54)`
- Android `1.1.55 (57)`
- Backend `1.1.10-api.1`

Changes:
- Fixed native-request classification for Capacitor `localhost` referers so native login and session bootstrap calls are treated as native app traffic instead of being misclassified as web.
- Native login, registration, and social auth flows now immediately bootstrap native companion tokens when the response itself did not include body tokens, reducing the chance of a logged-in phone app leaving the watch unauthenticated.

Verification:
- Backend compile passed.
- Mobile bundle rebuilt and re-synced.
- Android release bundle rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.37-web.1`
- iOS `1.1.51 (53)`
- Android `1.1.54 (56)`
- Backend `1.1.9-api.1`

Changes:
- Fixed native session token bootstrap so a logged-in Capacitor app can rehydrate companion tokens from its existing authenticated session instead of requiring a fresh manual login before the watch can report.
- Relaxed the native body-token heuristic for Capacitor webview requests so native login/registration responses can return tokens again even when the referer contains the app’s local host.

Verification:
- Backend compile will be re-run after the change.
- Mobile bundle will be rebuilt and re-synced after the change.
- Android release bundle will be rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.36-web.1`
- iOS `1.1.50 (52)`
- Android `1.1.53 (55)`

Changes:
- Added explicit runtime diagnostics to the Apple Watch screen so it now exposes the active quick-report branch and failure state, including direct token path, refresh, phone relay fallback, timeout, and returned error-code breadcrumbs.
- Mirrored a comparable debug-status line on Wear OS so Android watch behavior is inspectable too.

Verification:
- Mobile bundle will be rebuilt and re-synced after the change.
- Android release bundle will be rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.35-web.1`
- iOS `1.1.49 (51)`
- Android `1.1.52 (54)`

Changes:
- Apple Watch quick reporting now syncs a secure refresh path from the iPhone companion context, so the watch can recover a fresh access token without requiring the phone app to stay open at the same time.
- Added explicit network/request timeouts to Apple Watch phone-relay and direct-report paths to avoid hanging indefinitely on “Enviando...” when the relay or request stalls.
- Updated the Apple Watch status flow so it switches from location search to a real sending state once coordinates are available.

Verification:
- Mobile bundle will be rebuilt and re-synced after the change.
- Android release bundle will be rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.34-web.1`
- iOS `1.1.48 (50)`
- Android `1.1.51 (53)`

Changes:
- Stopped gating Apple Watch and Wear OS quick reports on a potentially stale “authenticated” companion flag when the paired phone is reachable.
- Both watch UIs now allow report attempts whenever the phone bridge is reachable, so the real relay/direct report logic can run instead of the watch disabling the action prematurely.

Verification:
- Mobile bundle will be rebuilt and re-synced after the change.
- Android release bundle will be rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.33-web.1`
- iOS `1.1.47 (49)`
- Android `1.1.50 (52)`

Changes:
- Replaced the generic helper copy under the Apple Watch and Wear OS titles with the live status line, so the same slot now shows the current ready state or the actual failure reason instead of a generic “tap to report” prompt.
- Removed the duplicate secondary failure text block on both watch UIs so there is a single clearer source of truth for report availability and errors.

Verification:
- Mobile bundle will be rebuilt and re-synced after the change.
- Android release bundle will be rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.32-web.1`
- iOS `1.1.46 (48)`
- Android `1.1.49 (51)`

Changes:
- Changed Apple Watch quick-report submission to prefer the watch’s synced short-lived access token path first, instead of always favoring the paired iPhone relay whenever the phone happened to be reachable.
- The iPhone relay remains as a fallback for recoverable auth/response failures, but the watch no longer blocks on that relay in the common case where it already has valid synced auth context.

Verification:
- Mobile bundle rebuilt and re-synced after the change.
- Android release bundle rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.31-web.1`
- iOS `1.1.45 (47)`
- Android `1.1.48 (50)`

Changes:
- Restored a direct Apple Watch quick-report fallback using a synced short-lived access token and API base URL from the iPhone, while still keeping the refresh token off the watch.
- The watch now enables reporting when it has a valid synced auth context, instead of requiring the iPhone relay to be actively reachable for every report tap.
- If the phone relay is available, the watch still prefers that path first; direct watch submission is the fallback for the unreachable/too-brittle cases that were leaving the report button gray.

Verification:
- Mobile bundle rebuilt and re-synced into embedded iOS/Android web assets.
- Android release bundle rebuilt on the new version.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.30-web.1`
- iOS `1.1.44 (46)`
- Android `1.1.47 (49)`

Changes:
- Fixed the Capacitor iOS companion bridge compile error by replacing the invalid `JSObject(dictionary:)` initializer with explicit `JSObject` payload construction for `getAuthState`.
- Rebuilt the shared mobile bundle and refreshed mobile versions so the next iOS/Xcode Cloud and Android artifacts clearly include this companion-bridge fix.

Verification:
- `yarn build:mobile:raw` passed after the fix.
- Android release bundle was rebuilt on the updated versions.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.29-web.1`
- iOS `1.1.43 (45)`
- Android `1.1.46 (48)`
- Backend `1.1.8-api.1`

Changes:
- Native auth tokens are no longer persisted in browser-style storage plus plaintext preference stores; the mobile app now hydrates them from secure companion storage, using Keychain on iOS and EncryptedSharedPreferences on Android.
- Apple Watch no longer receives reusable auth tokens or server URLs through application context; it now relies on the paired iPhone as the authenticated reporting broker, while the phone keeps tokens in secure storage.
- Wear OS token refresh now reads and writes its auth state through the encrypted Android companion bridge instead of the old plaintext preferences path.
- Added backend security rate limiting for admin 2FA issuance/verification, password reset requests, and municipality verification/resend flows, including genericized municipality verification responses to reduce account enumeration.
- Restricted operational diagnostics endpoints (`/api/webhooks/status`, `/api/health/auth`) to admin access only and tightened native token-body issuance behind an explicit `X-Native-App` signal.

Verification:
- Backend Python compile passed.
- `yarn build:mobile:raw` passed and refreshed embedded mobile web assets.
- Local iOS debug build still hits the pre-existing watch target product-type issue in CLI Xcode builds.
- Android release bundle was rebuilt after the version bump.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.28-web.1`
- iOS `1.1.42 (44)`
- Android `1.1.45 (47)`

Changes:
- Stopped the iPhone companion from overwriting the watch with empty auth payloads during context sync, which could leave the watch stuck in the disabled “open the iPhone app” state even after re-login.
- The watch now keeps its last usable direct-report auth context unless the phone explicitly marks the session unauthenticated.
- Rebuilt the shared mobile web bundle and refreshed mobile version numbers so this watch-auth state fix is easy to identify in testing.

### 2026-05-02 — Pending

Impacted environments:
- Backend `1.1.7-api.1`

Changes:
- Removed hardcoded fallback seed passwords for admin, demo municipality, and App Review startup accounts so GitGuardian no longer sees a checked-in company email password in source.
- Production seeding now requires those credentials to come from environment variables instead of silently inheriting checked-in defaults.
- Non-production seeding now generates random credentials at startup when explicit passwords are not supplied, preserving local convenience without baking secrets into the repository.

### 2026-05-02 — Pending

Impacted environments:
- Web `1.1.27-web.1`
- iOS `1.1.41 (43)`
- Android `1.1.44 (46)`
- Backend `1.1.6-api.1`

Changes:
- Apple Watch quick reporting now prefers the paired iPhone relay whenever the phone is reachable, instead of eagerly using the watch-direct network path and failing on stale auth context.
- The iPhone companion bridge can refresh an expired watch-side access token using the synced refresh token and retry the quick report automatically.
- The watch refreshes companion auth context on launch so the report button is less likely to flash ready and then collapse into a re-login error.
- Shared companion auth sync now includes refresh-token support on the phone-side native bridges, while still keeping the refresh token off the watch itself.
- Wear OS parity was preserved by keeping the Android phone relay refresh-and-retry path in sync and rebuilding the Android phone and wear artifacts after the shared bridge changes.

### 2026-05-01 — Pending

Impacted environments:
- Web `1.1.24-web.1`
- iOS `1.1.35 (37)`
- Android `1.1.37 (39)`
- Backend `1.1.3-api.1`

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
- Let the Apple Watch send quick reports using its synced auth/server context even when the paired iPhone app is not actively reachable, so the report button no longer flips back to disabled just because the phone fell to the background.
- Added a dedicated App Review user (`appletest`) with VIP access and a server-backed geo-review exemption, and updated the Spain gate so signed-in exempt reviewers can use the app outside Spain without disabling the normal production geo block for everyone else.
- Removed the Spain gate from the login and registration screens so App Review can actually sign into the exempt account before the rest of the app applies the location restriction.
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

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `working-tree-dirty`
- Deployment status: `pending`
- Rollback target: `16c930f`

Exact versions:
- Web: `1.1.27-web.1`
- iOS: `1.1.41 (43)`
- Android: `1.1.44 (46)`
- Backend: `1.1.6-api.1`

User-facing release notes:
- Make watch quick reports more resilient when phone auth context is stale or the access token needs a refresh.

Internal release notes:
- Sync refresh tokens into phone-only companion storage, refresh watch report auth on demand on iPhone and Android phone bridges, and tighten Apple Watch submit gating so the button only stays available when a real report path exists.

Store submission notes:
```text
- Improve Apple Watch and Wear OS quick report reliability when paired-phone auth needs refresh.
```

Internal release notes block:
```text
Commit SHA: working-tree-dirty
Deployment status: pending
Rollback target: 16c930f
Versions:
• Web: `1.1.27-web.1`
• iOS: `1.1.41 (43)`
• Android: `1.1.44 (46)`
• Backend: `1.1.6-api.1`
Notes:
- Sync refresh tokens into phone-only companion storage, refresh watch report auth on demand on iPhone and Android phone bridges, and tighten Apple Watch submit gating so the button only stays available when a real report path exists.
```

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `working-tree-dirty`
- Deployment status: `pending`
- Rollback target: `5895fdd`

Exact versions:
- Web: `1.1.26-web.1`
- iOS: `1.1.40 (42)`
- Android: `1.1.43 (45)`
- Backend: `1.1.6-api.1`

User-facing release notes:
- Add an admin municipality tab with active-city selection and mirrored city dashboard data.

Internal release notes:
- Share municipality dashboard payloads between municipality and admin flows, then add admin municipality selection and mirrored map/reports/photos/flags views.

Store submission notes:
```text
- Add municipality dashboard selection for admin oversight and align city-level dashboard views.
```

Internal release notes block:
```text
Commit SHA: working-tree-dirty
Deployment status: pending
Rollback target: 5895fdd
Versions:
• Web: `1.1.26-web.1`
• iOS: `1.1.40 (42)`
• Android: `1.1.43 (45)`
• Backend: `1.1.6-api.1`
Notes:
- Share municipality dashboard payloads between municipality and admin flows, then add admin municipality selection and mirrored map/reports/photos/flags views.
```

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `working-tree-dirty`
- Deployment status: `pending`
- Rollback target: `daaec6e`

Exact versions:
- Web: `1.1.25-web.1`
- iOS: `1.1.39 (41)`
- Android: `1.1.42 (44)`
- Backend: `1.1.5-api.1`

User-facing release notes:
- Harden auth, account recovery, and premium activation security paths.

Internal release notes:
- Require verified municipality accounts for dashboard access, stop auto-auth on municipality registration, hash password reset tokens, fail mock billing closed in production, trim public diagnostics, and stop syncing refresh tokens into watch companion storage.

Store submission notes:
```text
- Harden auth, account recovery, and premium activation security paths.
```

Internal release notes block:
```text
Commit SHA: working-tree-dirty
Deployment status: pending
Rollback target: daaec6e
Versions:
• Web: `1.1.25-web.1`
• iOS: `1.1.39 (41)`
• Android: `1.1.42 (44)`
• Backend: `1.1.5-api.1`
Notes:
- Require verified municipality accounts for dashboard access.
- Stop auto-auth on municipality registration.
- Hash password reset tokens and stop logging them.
- Fail mock premium activation closed in production.
- Trim public runtime diagnostics.
- Stop syncing refresh tokens into watch companion storage.
```

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `eb56ba005ede0b61c7995608c23c0366f421947e-dirty`
- Deployment status: `pending`
- Rollback target: `fc1e28c4ac6f966a78a59ed3119970335f8948ac`

Exact versions:
- Web: `1.1.24-web.1`
- iOS: `1.1.36 (38)`
- Android: `1.1.38 (40)`
- Backend: `1.1.3-api.1`

User-facing release notes:
- Refined Apple Watch text layout and button copy.

Internal release notes:
- Refined Apple Watch text layout and button copy

Store submission notes:
```text
- Refined Apple Watch text layout and button copy.
```

Internal release notes block:
```text
Commit SHA: eb56ba005ede0b61c7995608c23c0366f421947e-dirty
Deployment status: pending
Rollback target: fc1e28c4ac6f966a78a59ed3119970335f8948ac
Versions:
• Web: `1.1.24-web.1`
• iOS: `1.1.36 (38)`
• Android: `1.1.38 (40)`
• Backend: `1.1.3-api.1`
Notes:
- Refined Apple Watch text layout and button copy
```

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `afe809468c3eb5b472ab4334f61c992c5cb38df5-dirty`
- Deployment status: `pending`
- Rollback target: `eb56ba005ede0b61c7995608c23c0366f421947e`

Exact versions:
- Web: `1.1.24-web.1`
- iOS: `1.1.37 (39)`
- Android: `1.1.39 (41)`
- Backend: `1.1.3-api.1`

User-facing release notes:
- Add iPhone location fallback for Apple Watch reports.

Internal release notes:
- Add iPhone location fallback for Apple Watch reports

Store submission notes:
```text
- Add iPhone location fallback for Apple Watch reports.
```

Internal release notes block:
```text
Commit SHA: afe809468c3eb5b472ab4334f61c992c5cb38df5-dirty
Deployment status: pending
Rollback target: eb56ba005ede0b61c7995608c23c0366f421947e
Versions:
• Web: `1.1.24-web.1`
• iOS: `1.1.37 (39)`
• Android: `1.1.39 (41)`
• Backend: `1.1.3-api.1`
Notes:
- Add iPhone location fallback for Apple Watch reports
```

### 2026-05-02 — Pending

Release metadata:
- Commit SHA: `working-tree-dirty`
- Deployment status: `pending`
- Rollback target: `b9672de`

Exact versions:
- Web: `1.1.24-web.1`
- iOS: `1.1.38 (40)`
- Android: `1.1.41 (43)`
- Backend: `1.1.4-api.1`

User-facing release notes:
- Refresh companion watch auth and align Wear OS watch polish.

Internal release notes:
- Refresh Apple Watch auth context before report submission and mirror watch copy/layout updates on Wear OS.

Store submission notes:
```text
- Refresh companion watch auth and align Wear OS watch polish.
```

Internal release notes block:
```text
Commit SHA: working-tree-dirty
Deployment status: pending
Rollback target: b9672de
Versions:
• Web: `1.1.24-web.1`
• iOS: `1.1.38 (40)`
• Android: `1.1.41 (43)`
• Backend: `1.1.4-api.1`
Notes:
- Refresh Apple Watch auth context before report submission and mirror watch copy/layout updates on Wear OS.
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `6d1f3950d9d5a4b297a88576ce4757f8e7b252c1-dirty`
- Deployment status: `pending`
- Rollback target: `8c76457824bf310038a7854a6e15f94916877d60`

Exact versions:
- Web: `1.1.74-web.1`
- iOS: `1.1.92 (94)`
- Android: `1.1.91 (93)`
- Backend: `1.1.26-api.1`

User-facing release notes:
- Support iPhone monthly-only subscription review build.

Internal release notes:
- Support iPhone monthly-only subscription review build

Store submission notes:
```text
- Support iPhone monthly-only subscription review build.
```

Internal release notes block:
```text
Commit SHA: 6d1f3950d9d5a4b297a88576ce4757f8e7b252c1-dirty
Deployment status: pending
Rollback target: 8c76457824bf310038a7854a6e15f94916877d60
Versions:
• Web: `1.1.74-web.1`
• iOS: `1.1.92 (94)`
• Android: `1.1.91 (93)`
• Backend: `1.1.26-api.1`
Notes:
- Support iPhone monthly-only subscription review build
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `d3f788b9064bb70af7c3be54daf7c4bdea45c01e-dirty`
- Deployment status: `pending`
- Rollback target: `6d1f3950d9d5a4b297a88576ce4757f8e7b252c1`

Exact versions:
- Web: `1.1.74-web.1`
- iOS: `1.1.92 (94)`
- Android: `1.1.91 (93)`
- Backend: `1.1.27-api.1`

User-facing release notes:
- Allow rotating app review account independently.

Internal release notes:
- Allow rotating app review account independently

Store submission notes:
```text
- Allow rotating app review account independently.
```

Internal release notes block:
```text
Commit SHA: d3f788b9064bb70af7c3be54daf7c4bdea45c01e-dirty
Deployment status: pending
Rollback target: 6d1f3950d9d5a4b297a88576ce4757f8e7b252c1
Versions:
• Web: `1.1.74-web.1`
• iOS: `1.1.92 (94)`
• Android: `1.1.91 (93)`
• Backend: `1.1.27-api.1`
Notes:
- Allow rotating app review account independently
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `b248c28948d6ba7a151c8fdbaa971ee6e75f4145-dirty`
- Deployment status: `pending`
- Rollback target: `d3f788b9064bb70af7c3be54daf7c4bdea45c01e`

Exact versions:
- Web: `1.1.74-web.1`
- iOS: `1.1.92 (94)`
- Android: `1.1.91 (93)`
- Backend: `1.1.28-api.1`

User-facing release notes:
- Remove app review account from seeded premium access.

Internal release notes:
- Remove app review account from seeded premium access

Store submission notes:
```text
- Remove app review account from seeded premium access.
```

Internal release notes block:
```text
Commit SHA: b248c28948d6ba7a151c8fdbaa971ee6e75f4145-dirty
Deployment status: pending
Rollback target: d3f788b9064bb70af7c3be54daf7c4bdea45c01e
Versions:
• Web: `1.1.74-web.1`
• iOS: `1.1.92 (94)`
• Android: `1.1.91 (93)`
• Backend: `1.1.28-api.1`
Notes:
- Remove app review account from seeded premium access
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `7440a1735014bb1015f7a3a7a1e3d840fb8fc07b-dirty`
- Deployment status: `pending`
- Rollback target: `b248c28948d6ba7a151c8fdbaa971ee6e75f4145`

Exact versions:
- Web: `1.1.74-web.1`
- iOS: `1.1.92 (94)`
- Android: `1.1.91 (93)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Force app review account to stay non-premium.

Internal release notes:
- Force app review account to stay non-premium

Store submission notes:
```text
- Force app review account to stay non-premium.
```

Internal release notes block:
```text
Commit SHA: 7440a1735014bb1015f7a3a7a1e3d840fb8fc07b-dirty
Deployment status: pending
Rollback target: b248c28948d6ba7a151c8fdbaa971ee6e75f4145
Versions:
• Web: `1.1.74-web.1`
• iOS: `1.1.92 (94)`
• Android: `1.1.91 (93)`
• Backend: `1.1.29-api.1`
Notes:
- Force app review account to stay non-premium
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `e562a90e78d3b428989b005ed18ebe672ad1ab09-dirty`
- Deployment status: `pending`
- Rollback target: `7440a1735014bb1015f7a3a7a1e3d840fb8fc07b`

Exact versions:
- Web: `1.1.75-web.1`
- iOS: `1.1.93 (95)`
- Android: `1.1.92 (94)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Fix disabled iPhone monthly subscribe button.

Internal release notes:
- Fix disabled iPhone monthly subscribe button

Store submission notes:
```text
- Fix disabled iPhone monthly subscribe button.
```

Internal release notes block:
```text
Commit SHA: e562a90e78d3b428989b005ed18ebe672ad1ab09-dirty
Deployment status: pending
Rollback target: 7440a1735014bb1015f7a3a7a1e3d840fb8fc07b
Versions:
• Web: `1.1.75-web.1`
• iOS: `1.1.93 (95)`
• Android: `1.1.92 (94)`
• Backend: `1.1.29-api.1`
Notes:
- Fix disabled iPhone monthly subscribe button
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `1a3c5d8f9543933ceb684365dfb369cfa16035cb-dirty`
- Deployment status: `pending`
- Rollback target: `e562a90e78d3b428989b005ed18ebe672ad1ab09`

Exact versions:
- Web: `1.1.76-web.1`
- iOS: `1.1.94 (96)`
- Android: `1.1.93 (95)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Tighten monthly-only Apple subscription config.
- Improve missing App Store product diagnostics.

Internal release notes:
- Tighten monthly-only Apple subscription config
- Improve missing App Store product diagnostics

Store submission notes:
```text
- Tighten monthly-only Apple subscription config.
- Improve missing App Store product diagnostics.
```

Internal release notes block:
```text
Commit SHA: 1a3c5d8f9543933ceb684365dfb369cfa16035cb-dirty
Deployment status: pending
Rollback target: e562a90e78d3b428989b005ed18ebe672ad1ab09
Versions:
• Web: `1.1.76-web.1`
• iOS: `1.1.94 (96)`
• Android: `1.1.93 (95)`
• Backend: `1.1.29-api.1`
Notes:
- Tighten monthly-only Apple subscription config
- Improve missing App Store product diagnostics
```

### 2026-05-06 — Pending

Release metadata:
- Commit SHA: `9d82b904850f44ca0d79b0b2bbdfa77df9351ba9-dirty`
- Deployment status: `pending`
- Rollback target: `1a3c5d8f9543933ceb684365dfb369cfa16035cb`

Exact versions:
- Web: `1.1.77-web.1`
- iOS: `1.1.95 (97)`
- Android: `1.1.94 (96)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Correct premium monthly fallback price display.
- Remove stale hardcoded subscription prices from terms.

Internal release notes:
- Correct premium monthly fallback price display
- Remove stale hardcoded subscription prices from terms

Store submission notes:
```text
- Correct premium monthly fallback price display.
- Remove stale hardcoded subscription prices from terms.
```

Internal release notes block:
```text
Commit SHA: 9d82b904850f44ca0d79b0b2bbdfa77df9351ba9-dirty
Deployment status: pending
Rollback target: 1a3c5d8f9543933ceb684365dfb369cfa16035cb
Versions:
• Web: `1.1.77-web.1`
• iOS: `1.1.95 (97)`
• Android: `1.1.94 (96)`
• Backend: `1.1.29-api.1`
Notes:
- Correct premium monthly fallback price display
- Remove stale hardcoded subscription prices from terms
```

### 2026-05-07 — Pending

Release metadata:
- Commit SHA: `c24724e076b665aef4e40d0f79a12064d08916eb-dirty`
- Deployment status: `pending`
- Rollback target: `9d82b904850f44ca0d79b0b2bbdfa77df9351ba9`

Exact versions:
- Web: `1.1.78-web.1`
- iOS: `1.1.96 (98)`
- Android: `1.1.95 (97)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Update Apple monthly subscription product id.

Internal release notes:
- Update Apple monthly subscription product id

Store submission notes:
```text
- Update Apple monthly subscription product id.
```

Internal release notes block:
```text
Commit SHA: c24724e076b665aef4e40d0f79a12064d08916eb-dirty
Deployment status: pending
Rollback target: 9d82b904850f44ca0d79b0b2bbdfa77df9351ba9
Versions:
• Web: `1.1.78-web.1`
• iOS: `1.1.96 (98)`
• Android: `1.1.95 (97)`
• Backend: `1.1.29-api.1`
Notes:
- Update Apple monthly subscription product id
```

### 2026-05-07 — Pending

Release metadata:
- Commit SHA: `cff017a0b25fe4ae17b1fd0a9542ddc5b46a3c70-dirty`
- Deployment status: `pending`
- Rollback target: `c24724e076b665aef4e40d0f79a12064d08916eb`

Exact versions:
- Web: `1.1.79-web.1`
- iOS: `1.1.97 (99)`
- Android: `1.1.96 (98)`
- Backend: `1.1.29-api.1`

User-facing release notes:
- Make iOS review build metadata-safe.
- Replace Apple-style emoji app icon with custom radar icon.

Internal release notes:
- Make iOS review build metadata-safe
- Replace Apple-style emoji app icon with custom radar icon

Store submission notes:
```text
- Make iOS review build metadata-safe.
- Replace Apple-style emoji app icon with custom radar icon.
```

Internal release notes block:
```text
Commit SHA: cff017a0b25fe4ae17b1fd0a9542ddc5b46a3c70-dirty
Deployment status: pending
Rollback target: c24724e076b665aef4e40d0f79a12064d08916eb
Versions:
• Web: `1.1.79-web.1`
• iOS: `1.1.97 (99)`
• Android: `1.1.96 (98)`
• Backend: `1.1.29-api.1`
Notes:
- Make iOS review build metadata-safe
- Replace Apple-style emoji app icon with custom radar icon
```

### 2026-05-07 — Pending

Release metadata:
- Commit SHA: `87650a6dcb89c642dcd62a8257966744a68f9f97-dirty`
- Deployment status: `pending`
- Rollback target: `9da1e43a483ab35bd439f4d06ec08eba6b73fb82`

Exact versions:
- Web: `1.1.80-web.1`
- iOS: `1.1.99 (101)`
- Android: `1.1.98 (100)`
- Backend: `1.1.30-api.1`

User-facing release notes:
- Tighten iOS review surfaces.

Internal release notes:
- Tighten iOS review surfaces

Store submission notes:
```text
- Tighten iOS review surfaces.
```

Internal release notes block:
```text
Commit SHA: 87650a6dcb89c642dcd62a8257966744a68f9f97-dirty
Deployment status: pending
Rollback target: 9da1e43a483ab35bd439f4d06ec08eba6b73fb82
Versions:
• Web: `1.1.80-web.1`
• iOS: `1.1.99 (101)`
• Android: `1.1.98 (100)`
• Backend: `1.1.30-api.1`
Notes:
- Tighten iOS review surfaces
```

### 2026-05-07 — Pending

Release metadata:
- Commit SHA: `0067ce15808f702022ceff331d4b938931ae56bc-dirty`
- Deployment status: `pending`
- Rollback target: `87650a6dcb89c642dcd62a8257966744a68f9f97`

Exact versions:
- Web: `1.1.80-web.1`
- iOS: `1.1.99 (101)`
- Android: `1.1.98 (100)`
- Backend: `1.1.31-api.1`

User-facing release notes:
- Fix Apple Store Server library ProductType import.

Internal release notes:
- Fix Apple Store Server library ProductType import

Store submission notes:
```text
- Fix Apple Store Server library ProductType import.
```

Internal release notes block:
```text
Commit SHA: 0067ce15808f702022ceff331d4b938931ae56bc-dirty
Deployment status: pending
Rollback target: 87650a6dcb89c642dcd62a8257966744a68f9f97
Versions:
• Web: `1.1.80-web.1`
• iOS: `1.1.99 (101)`
• Android: `1.1.98 (100)`
• Backend: `1.1.31-api.1`
Notes:
- Fix Apple Store Server library ProductType import
```

### 2026-05-08 — Pending

Release metadata:
- Commit SHA: `95be64026ed9cb17672143329ec36ca3f5d8015a-dirty`
- Deployment status: `pending`
- Rollback target: `0067ce15808f702022ceff331d4b938931ae56bc`

Exact versions:
- Web: `1.1.80-web.1`
- iOS: `1.1.99 (101)`
- Android: `1.1.98 (100)`
- Backend: `1.1.32-api.1`

User-facing release notes:
- Allow real Apple premium subscription for app review account.

Internal release notes:
- Allow real Apple premium subscription for app review account

Store submission notes:
```text
- Allow real Apple premium subscription for app review account.
```

Internal release notes block:
```text
Commit SHA: 95be64026ed9cb17672143329ec36ca3f5d8015a-dirty
Deployment status: pending
Rollback target: 0067ce15808f702022ceff331d4b938931ae56bc
Versions:
• Web: `1.1.80-web.1`
• iOS: `1.1.99 (101)`
• Android: `1.1.98 (100)`
• Backend: `1.1.32-api.1`
Notes:
- Allow real Apple premium subscription for app review account
```

