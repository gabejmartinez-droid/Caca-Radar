/**
 * Token Manager for Capacitor native apps.
 * 
 * ============================================================
 * WHY THIS EXISTS (DO NOT REMOVE):
 * ============================================================
 * The Emergent/Kubernetes/Cloudflare proxy ALWAYS returns:
 *   access-control-allow-origin: *
 * for ALL responses, including OPTIONS preflights. This is
 * platform infrastructure and CANNOT be changed.
 *
 * Browsers reject credentialed requests (withCredentials: true)
 * when the server responds with wildcard CORS. Therefore,
 * cookie-based auth CANNOT work for cross-origin Capacitor apps.
 *
 * SOLUTION (permanent):
 * - Web: Uses relative "/api" paths → same-origin, no CORS needed.
 *   Cookies (httponly, secure, samesite=none) work normally.
 * - Capacitor Native: Uses full hosted URL (cross-origin).
 *   Auth via Authorization: Bearer <token> header.
 *   withCredentials is always set to false.
 *   Tokens are persisted in localStorage so users stay logged in
 *   across app restarts.
 *
 * The axios interceptor in AuthContext.js enforces this by:
 * 1. Attaching the Bearer header on every native request.
 * 2. Force-setting withCredentials = false on every native request,
 *    even if individual call sites pass withCredentials: true.
 * ============================================================
 */

const isNative = typeof window !== "undefined" && (
  window.Capacitor?.isNativePlatform?.() ||
  window.location?.protocol === "capacitor:" ||
  window.location?.protocol === "ionic:"
);

const TOKEN_KEY = "caca_access_token";
const REFRESH_KEY = "caca_refresh_token";

// Initialize from persisted storage for native (survives app restart)
let accessToken = isNative ? localStorage.getItem(TOKEN_KEY) : null;
let refreshToken = isNative ? localStorage.getItem(REFRESH_KEY) : null;

export function isCapacitorNative() {
  return isNative;
}

export function setTokens(access, refresh) {
  accessToken = access || null;
  refreshToken = refresh || null;
  if (isNative) {
    if (access) localStorage.setItem(TOKEN_KEY, access);
    else localStorage.removeItem(TOKEN_KEY);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    else localStorage.removeItem(REFRESH_KEY);
  }
}

export function getAccessToken() {
  return accessToken;
}

export function getRefreshToken() {
  return refreshToken;
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (isNative) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }
}
