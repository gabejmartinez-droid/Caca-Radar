import { API } from "./config";

const isNative = typeof window !== "undefined" && (
  window.Capacitor?.isNativePlatform?.() ||
  window.location?.protocol === "capacitor:" ||
  window.location?.protocol === "ionic:"
);

let accessToken = null;
let tokensInitialized = !isNative;
let tokenInitializationPromise = null;

async function persistNativeTokens(refreshTokenValue = undefined) {
  if (!isNative) return;
  const { syncCompanionAuthState, clearCompanionAuthState } = await import("./utils/companionBridge");
  if (accessToken || refreshTokenValue !== undefined) {
    await syncCompanionAuthState({
      accessToken,
      refreshToken: refreshTokenValue,
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
    return { accessToken };
  }
  if (tokenInitializationPromise) {
    return tokenInitializationPromise;
  }

  tokenInitializationPromise = import("./utils/companionBridge")
    .then(({ getCompanionAuthState }) => getCompanionAuthState())
    .then((state) => {
      accessToken = state?.accessToken || null;
      tokensInitialized = true;
      return { accessToken };
    })
    .catch(() => {
      accessToken = null;
      tokensInitialized = true;
      return { accessToken };
    })
    .finally(() => {
      tokenInitializationPromise = null;
    });

  return tokenInitializationPromise;
}

export async function setTokens(access, refresh) {
  if (!isNative) {
    accessToken = null;
    tokensInitialized = true;
    return;
  }
  accessToken = access || null;
  tokensInitialized = true;
  await persistNativeTokens(refresh);
}

export function getAccessToken() {
  return accessToken;
}

export async function bootstrapNativeSessionFromCookies() {
  if (!isNative) return { accessToken: accessToken || "", synced: false };
  const { bootstrapNativeSessionFromCookies: bootstrapSession } = await import("./utils/companionBridge");
  const state = await bootstrapSession({ apiBaseUrl: API });
  accessToken = state?.accessToken || accessToken || null;
  tokensInitialized = true;
  return state;
}

export async function refreshNativeAccessToken() {
  if (!isNative) return "";
  const { refreshNativeAccessToken: refreshAccessToken } = await import("./utils/companionBridge");
  const state = await refreshAccessToken({ apiBaseUrl: API });
  accessToken = state?.accessToken || null;
  tokensInitialized = true;
  return accessToken;
}

export async function clearTokens() {
  accessToken = null;
  tokensInitialized = true;
  if (!isNative) return;
  await persistNativeTokens();
}
