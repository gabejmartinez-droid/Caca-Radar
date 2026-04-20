# Legal / Compliance Checklist — Caca Radar

Updated: 2026-04-20

## Verified from the codebase

### Personal data categories actually collected

- Account data:
  - email
  - username / display name
  - internal user id
  - password hash for email/password accounts
  - linked Google identity data (`subject`, `email`, `name`, `picture`) when Google sign-in is used
- Report data:
  - latitude / longitude
  - description
  - photo
  - municipality / province / barrio from reverse geocoding
  - status, votes, validations, flags, confidence/freshness metadata
- Technical/session data:
  - IP and request metadata server-side
  - app version / environment headers
  - web auth cookies (`access_token`, `refresh_token`)
  - anonymous interaction cookie (`anon_id`)
  - native auth tokens in local storage
- Push data:
  - browser push subscription object
  - native push token for Capacitor/native push
  - lat/lng used for nearby push alerts
- Subscription data:
  - plan type
  - status / expiry
  - Apple / Google store metadata and receipt verification data
- Support/community:
  - feedback records
  - support/privacy emails sent to `jefe@cacaradar.es`

### Vendors / processors actually visible in the repo

- Google
  - Google Sign-In / Google Identity Services
  - Google Play subscription verification / webhooks
  - FCM endpoint for native push delivery
- Apple
  - Apple App Store subscription verification / webhooks
- OpenStreetMap
  - map tiles
- Nominatim
  - reverse geocoding
- Emergent object storage
  - photo uploads via `integrations.emergentagent.com/objstore`
- MongoDB
  - application database

### Cookies / local storage / similar technologies actually used

- Web cookies
  - `access_token` — 1 hour
  - `refresh_token` — 7 days
  - `anon_id` — 365 days
- Local storage
  - `caca-radar-lang`
  - native auth tokens
  - `caca_notifications`
  - `notif_prompted`
  - `activity_banner_daily:*`
- Session storage
  - `activity_banner_dismissals:*`
- Other client-side storage
  - service worker caches for web app shell and map tiles

### Permissions actually requested

- Camera
- Photo library / files
- Location
- Notifications / push

### Public visibility

- Reports are public inside the app/web map UI
- Public fields visible from code:
  - photo
  - description
  - date / freshness / status
  - contributor display name or anonymous fallback
  - municipality / area labels
  - exact map coordinates rendered as map markers
- Reports can be shared by in-app share links

### Moderation / abuse reporting

- In-app flag/report-content flow exists in the report detail drawer
- Backend stores flags and has moderation endpoints
- Email fallback exists via `jefe@cacaradar.es`

### Deletion behavior actually implemented

- `DELETE /api/users/me`:
  - deletes the user record
  - deletes votes, validations, flags, notifications, push subscriptions, saved locations, feedback, subscription receipts
  - anonymizes authored reports and report audit log entries
  - removes auth cookies / local session state client-side

### Subscription status

- Premium/subscription UI exists with concrete pricing shown
- Backend has:
  - direct `/users/subscribe` route with free-trial / mock activation logic
  - Apple and Google receipt verification routes
  - Apple / Google webhook handlers
- This means subscription language must be careful and aligned with actual live production flow

## Public legal/UI work implemented

- `/privacy`
- `/terms`
- `/cookies`
- `/delete-account`
- `/community`
- Help/profile/menu/login/register wiring to relevant legal pages
- Non-official disclaimers added in help/profile/map/legal pages
- In-app deletion path preserved through profile -> delete-account page

## TODO-LEGAL items for manual confirmation

- Confirm production hosting provider name and region
- Confirm MongoDB hosting region and whether any data is processed outside the EEA
- Confirm backup retention / rotation period after account deletion
- Confirm support email retention period
- Confirm operational log retention period
- Confirm whether any additional transactional email provider is used in production
- Confirm whether any non-essential analytics / measurement tool is active in deployed web
- Confirm whether all premium purchase flows shown in UI are live in production or whether some remain mock/demo

## Store / console items to review manually

### Apple App Store

- App Privacy / nutrition labels:
  - account info
  - user content (photos, text, location)
  - identifiers / diagnostics if applicable
  - purchases / subscriptions if live
  - precise location if app reports exact locations
- Review whether Sign in with Apple is required for the exact iOS auth setup at submission time
- Verify delete-account URL and in-app deletion path in App Store Connect
- Verify subscription metadata, cancellation wording, trial wording, and screenshots if premium is live

### Google Play

- Data safety form:
  - account info
  - photos
  - precise location
  - app activity / user content
  - purchases if premium is live
- Verify account deletion URL
- Verify store description includes the non-official / independent nature of the app
- Verify subscription details if premium is live
- Verify Android Google sign-in OAuth client IDs and backend allowlist config

### Web / site

- Confirm production pages are reachable:
  - `/privacy`
  - `/terms`
  - `/cookies`
  - `/delete-account`
  - `/community`
- Confirm any public footer/menu/help links after deploy
