/**
 * API base URL configuration.
 * 
 * ============================================================
 * DUAL-AUTH ARCHITECTURE (DO NOT CHANGE):
 * ============================================================
 * Web:
 *   - Uses relative "/api" → same-origin → no CORS needed.
 *   - Auth via httponly cookies (set by backend).
 * 
 * Capacitor Native (iOS/Android):
 *   - Uses full hosted URL (cross-origin to capacitor://localhost).
 *   - Auth via Authorization: Bearer <token> header.
 *   - The Emergent proxy ALWAYS returns access-control-allow-origin: *
 *     which is fine because withCredentials is forced to false.
 *   - See tokenManager.js for full explanation.
 * ============================================================
 */

const HOSTED_BACKEND = "https://cacaradar.es";

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
export const HOSTED_WEB_URL = HOSTED_BACKEND;
export const APP_ENVIRONMENT = API.startsWith("http") ? "native-production" : "web";
export const APP_VERSION = process.env.REACT_APP_VERSION || "dev";
export const NATIVE_PUSH_ENABLED = process.env.REACT_APP_ENABLE_NATIVE_PUSH === "true";
