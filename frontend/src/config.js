/**
 * API base URL configuration.
 * 
 * Web: Always uses relative "/api" — works on any domain (preview, production, custom).
 * Capacitor native: Detected at runtime and uses the full hosted backend URL.
 * 
 * REACT_APP_BACKEND_URL is intentionally NOT used because the Emergent platform
 * bakes the preview URL into the build, which breaks production deployments
 * (cross-origin cookies fail). Relative "/api" is the only reliable web path.
 */

const HOSTED_BACKEND = "https://caca-radar.preview.emergentagent.com";

// This runs at runtime, not build time
function getApiUrl() {
  if (typeof window !== "undefined") {
    const isNative = window.Capacitor?.isNativePlatform?.() ||
      window.location?.protocol === "capacitor:" ||
      window.location?.protocol === "ionic:";
    if (isNative) {
      return HOSTED_BACKEND + "/api";
    }
  }
  return "/api";
}

export const API = getApiUrl();
