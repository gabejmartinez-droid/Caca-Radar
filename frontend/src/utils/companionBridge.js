function isNativeRuntime() {
  return typeof window !== "undefined" && (
    window.Capacitor?.isNativePlatform?.() ||
    window.location?.protocol === "capacitor:" ||
    window.location?.protocol === "ionic:"
  );
}

function getCompanionPlugin() {
  if (!isNativeRuntime()) return null;
  return window.Capacitor?.Plugins?.CompanionBridge || null;
}

export async function syncCompanionAuthState({ accessToken, refreshToken, apiBaseUrl }) {
  const plugin = getCompanionPlugin();
  if (!plugin?.syncAuthState) return;
  try {
    const payload = {
      accessToken: accessToken || "",
      apiBaseUrl: apiBaseUrl || "",
    };
    if (refreshToken !== undefined) {
      payload.refreshToken = refreshToken || "";
    } else {
      payload.preserveStoredRefreshToken = true;
    }
    await plugin.syncAuthState(payload);
  } catch {
    // Companion sync should never break app auth flows.
  }
}

export async function getCompanionAuthState() {
  const plugin = getCompanionPlugin();
  if (!plugin?.getAuthState) return { accessToken: "", apiBaseUrl: "" };
  try {
    return await plugin.getAuthState();
  } catch {
    return { accessToken: "", apiBaseUrl: "" };
  }
}

export async function bootstrapNativeSessionFromCookies({ apiBaseUrl }) {
  const plugin = getCompanionPlugin();
  if (!plugin?.bootstrapSessionFromCookies) return { accessToken: "", synced: false };
  try {
    return await plugin.bootstrapSessionFromCookies({
      apiBaseUrl: apiBaseUrl || "",
    });
  } catch {
    return { accessToken: "", synced: false };
  }
}

export async function refreshNativeAccessToken({ apiBaseUrl }) {
  const plugin = getCompanionPlugin();
  if (!plugin?.refreshAccessToken) return { accessToken: "" };
  try {
    return await plugin.refreshAccessToken({
      apiBaseUrl: apiBaseUrl || "",
    });
  } catch {
    return { accessToken: "" };
  }
}

export async function syncCompanionPreferences({ preferredLanguage }) {
  const plugin = getCompanionPlugin();
  if (!plugin?.syncPreferences) return;
  try {
    await plugin.syncPreferences({
      preferredLanguage: preferredLanguage || "",
    });
  } catch {
    // Companion sync should never break preference changes.
  }
}

export async function clearCompanionAuthState() {
  const plugin = getCompanionPlugin();
  if (!plugin?.clearAuthState) return;
  try {
    await plugin.clearAuthState();
  } catch {
    // Companion sync should never break app auth flows.
  }
}
