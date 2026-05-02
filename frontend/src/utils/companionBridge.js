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
    await plugin.syncAuthState({
      accessToken: accessToken || "",
      refreshToken: refreshToken || "",
      apiBaseUrl: apiBaseUrl || "",
    });
  } catch {
    // Companion sync should never break app auth flows.
  }
}

export async function getCompanionAuthState() {
  const plugin = getCompanionPlugin();
  if (!plugin?.getAuthState) return { accessToken: "", refreshToken: "", apiBaseUrl: "" };
  try {
    return await plugin.getAuthState();
  } catch {
    return { accessToken: "", refreshToken: "", apiBaseUrl: "" };
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
