# Mobile Rebuild Checklist

When updating the web app, ensure these Capacitor/mobile compatibility fixes are preserved:

## Backend (server.py)
- [ ] CORS must include `capacitor://localhost` and `ionic://localhost` in allow_origins
- [ ] CORS must include `allow_origin_regex` for `https://.*\.emergentagent\.com`
- [ ] Do NOT use `allow_origins=["*"]` with `allow_credentials=True`
- [ ] All `set_cookie` calls must use `samesite="none"` and `secure=True`

## Frontend Config (src/config.js)
- [ ] API must use `DEFAULT_BACKEND_URL` fallback, NOT relative `/api`
- [ ] `const DEFAULT_BACKEND_URL = "https://caca-radar.emergent.host"`
- [ ] `export const API = (process.env.REACT_APP_BACKEND_URL || DEFAULT_BACKEND_URL) + "/api"`

## Frontend API Imports
- [ ] All page/component files must use `import { API } from "../config"` (or correct path)
- [ ] No file should define `const API = "/api"` locally
- [ ] Files: AuthContext, NotificationChecker, UsernamePrompt, all pages

## MapPage.js Safe Areas
- [ ] Header: `style={{ top: "calc(env(safe-area-inset-top, 0px) + 16px)" }}`
- [ ] Filter bar: `style={{ top: "calc(env(safe-area-inset-top, 0px) + 64px)" }}`
- [ ] Report FAB: `style={{ bottom: "calc(env(safe-area-inset-bottom, 0px) + 32px)" }}`
- [ ] Reports fetch: guard with `Array.isArray(data) ? data : []`
- [ ] Reports error: `setReports([])` on catch

## index.html
- [ ] No `emergent-badge` element
- [ ] No `assets.emergent.sh` scripts
- [ ] No PostHog scripts
- [ ] Has `viewport-fit=cover` in viewport meta

## package.json
- [ ] `"homepage": "."` is set
- [ ] Capacitor deps: `@capacitor/core`, `@capacitor/ios`, `@capacitor/android`
- [ ] Capacitor CLI in devDeps: `@capacitor/cli`
- [ ] Scripts: `cap:copy`, `cap:sync`, `cap:open:ios`, `cap:open:android`, `build:mobile`

## capacitor.config.json
- [ ] `appId: "com.jefe.cacaradar"`
- [ ] `webDir: "build"`

## Native Identity
- [ ] iOS bundle: `com.jefe.cacaradar`
- [ ] Android applicationId: `com.jefe.cacaradar`
- [ ] Android namespace: `com.jefe.cacaradar`
- [ ] Icons generated from `public/caca-radar-icon.png`

## Build Verification
- [ ] `yarn build` succeeds
- [ ] Built assets use relative paths (`./static/js/...`)
- [ ] No `emergent-badge`, `Made with Emergent`, `posthog` in built HTML
- [ ] No conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in any file
