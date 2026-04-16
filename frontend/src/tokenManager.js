/**
 * Token manager for Capacitor native apps.
 * 
 * On native (capacitor://localhost), cookies don't work with the remote API
 * because the Kubernetes proxy overwrites CORS headers with wildcard "*",
 * which breaks credentialed cookie requests.
 * 
 * Solution: On native platforms, store JWT tokens in memory and send them
 * via Authorization: Bearer header. On web, cookies work normally.
 */

// Detect if running inside Capacitor native shell
const isNative = typeof window !== "undefined" && (
  window.Capacitor?.isNativePlatform?.() ||
  window.location?.protocol === "capacitor:" ||
  window.location?.protocol === "ionic:"
);

let accessToken = null;
let refreshToken = null;

export function isCapacitorNative() {
  return isNative;
}

export function setTokens(access, refresh) {
  accessToken = access || null;
  refreshToken = refresh || null;
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
}
