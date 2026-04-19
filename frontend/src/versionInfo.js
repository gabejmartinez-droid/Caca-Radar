import appVersions from "./appVersions.json";

export function getCurrentPlatform() {
  if (typeof window === "undefined") return "web";
  if (window.Capacitor?.isNativePlatform?.()) {
    return window.Capacitor?.getPlatform?.() || "native";
  }
  if (window.location?.protocol === "capacitor:" || window.location?.protocol === "ionic:") {
    return window.Capacitor?.getPlatform?.() || "native";
  }
  return "web";
}

export function getCurrentAppVersion() {
  const platform = getCurrentPlatform();
  if (platform === "ios") {
    return `${appVersions.ios.version} (${appVersions.ios.build})`;
  }
  if (platform === "android") {
    return `${appVersions.android.version} (${appVersions.android.build})`;
  }
  return appVersions.web;
}

export function getVersionSummary() {
  return {
    web: appVersions.web,
    ios: `${appVersions.ios.version} (${appVersions.ios.build})`,
    android: `${appVersions.android.version} (${appVersions.android.build})`,
    backend: appVersions.backend,
  };
}

export { appVersions };
