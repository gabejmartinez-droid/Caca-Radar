import { API } from "./config";

const isNative = typeof window !== "undefined" && (
  window.Capacitor?.isNativePlatform?.() ||
  window.location?.protocol === "capacitor:" ||
  window.location?.protocol === "ionic:"
);

let accessToken = null;
let refreshToken = null;
let tokensInitialized = !isNative;
let tokenInitializationPromise = null;

async function persistNativeTokens() {
  if (!isNative) return;
  const { syncCompanionAuthState, clearCompanionAuthState } = await import("./utils/companionBridge");
  if (accessToken || refreshToken) {
    await syncCompanionAuthState({
      accessToken,
      refreshToken,
      apiBaseUrl: API,
    });
    return;
  }
  await clearCompanionAuthState();
}

export function isCapacitorNative() {
  return isNative;
}

export async function initializeTokens() {
  if (!isNative || tokensInitialized) {
    return { accessToken, refreshToken };
  }
  if (tokenInitializationPromise) {
    return tokenInitializationPromise;
  }

  tokenInitializationPromise = import("./utils/companionBridge")
    .then(({ getCompanionAuthState }) => getCompanionAuthState())
    .then((state) => {
      accessToken = state?.accessToken || null;
      refreshToken = state?.refreshToken || null;
      tokensInitialized = true;
      return { accessToken, refreshToken };
    })
    .catch(() => {
      accessToken = null;
      refreshToken = null;
      tokensInitialized = true;
      return { accessToken, refreshToken };
    })
    .finally(() => {
      tokenInitializationPromise = null;
    });

  return tokenInitializationPromise;
}

export async function setTokens(access, refresh) {
  accessToken = access || null;
  refreshToken = refresh || null;
  tokensInitialized = true;
  await persistNativeTokens();
}

export function getAccessToken() {
  return accessToken;
}

export function getRefreshToken() {
  return refreshToken;
}

export async function clearTokens() {
  accessToken = null;
  refreshToken = null;
  tokensInitialized = true;
  await persistNativeTokens();
}
