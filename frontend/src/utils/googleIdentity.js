import { GOOGLE_CLIENT_ID } from "../config";

const GIS_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

let gisScriptPromise = null;

export function isGoogleIdentitySupported() {
  return typeof window !== "undefined" && !window.Capacitor?.isNativePlatform?.();
}

export function getGoogleClientId() {
  return GOOGLE_CLIENT_ID;
}

export function loadGoogleIdentityScript() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Google Identity Services is only available in the browser"));
  }

  if (window.google?.accounts?.id) {
    return Promise.resolve(window.google);
  }

  if (gisScriptPromise) {
    return gisScriptPromise;
  }

  gisScriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GIS_SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(window.google), { once: true });
      existing.addEventListener("error", () => reject(new Error("Failed to load Google Identity Services")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = GIS_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve(window.google);
    script.onerror = () => reject(new Error("Failed to load Google Identity Services"));
    document.head.appendChild(script);
  });

  return gisScriptPromise;
}

export function disableGoogleAutoSelect() {
  if (typeof window !== "undefined" && window.google?.accounts?.id) {
    window.google.accounts.id.disableAutoSelect();
  }
}
