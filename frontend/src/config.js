import { getCurrentAppVersion } from "./versionInfo";

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
export const APP_VERSION = process.env.REACT_APP_VERSION || getCurrentAppVersion();
export const NATIVE_PUSH_ENABLED = process.env.REACT_APP_ENABLE_NATIVE_PUSH === "true";
export const GOOGLE_CLIENT_ID =
  process.env.REACT_APP_GOOGLE_CLIENT_ID ||
  "685896513137-l455qbtk0bsgkuhlfiihc1bd0q5o1jia.apps.googleusercontent.com";
export const GOOGLE_IOS_CLIENT_ID =
  process.env.REACT_APP_GOOGLE_IOS_CLIENT_ID ||
  "685896513137-h75c4t1ikftjofpl6vovakoj4f6vgn1l.apps.googleusercontent.com";
export const PLAY_INTEGRITY_ENABLED = process.env.REACT_APP_ENABLE_PLAY_INTEGRITY === "true";
export const PLAY_INTEGRITY_CLOUD_PROJECT_NUMBER = process.env.REACT_APP_GOOGLE_CLOUD_PROJECT_NUMBER || "";
