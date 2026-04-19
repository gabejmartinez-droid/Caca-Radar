import { registerPlugin } from "@capacitor/core";
import { PLAY_INTEGRITY_CLOUD_PROJECT_NUMBER, PLAY_INTEGRITY_ENABLED } from "../config";

const PlayIntegrity = registerPlugin("PlayIntegrity");

function isAndroidNative() {
  return window.Capacitor?.isNativePlatform?.() && window.Capacitor?.getPlatform?.() === "android";
}

export function isPlayIntegrityAvailable() {
  return Boolean(PLAY_INTEGRITY_ENABLED && PLAY_INTEGRITY_CLOUD_PROJECT_NUMBER && isAndroidNative());
}

export async function preparePlayIntegrity() {
  if (!isPlayIntegrityAvailable()) {
    return { enabled: false, prepared: false, skipped: true };
  }

  return PlayIntegrity.prepare({
    cloudProjectNumber: Number(PLAY_INTEGRITY_CLOUD_PROJECT_NUMBER),
  });
}

async function sha256Base64Url(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const base64 = btoa(String.fromCharCode(...new Uint8Array(digest)));
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

export async function requestPlayIntegrityToken(payload) {
  if (!isPlayIntegrityAvailable()) {
    return { enabled: false, skipped: true };
  }

  const requestHash = await sha256Base64Url(typeof payload === "string" ? payload : JSON.stringify(payload));
  const response = await PlayIntegrity.requestToken({ requestHash });
  return { ...response, enabled: true };
}

export async function getPlayIntegrityStatus() {
  if (!isAndroidNative()) {
    return { available: false, prepared: false };
  }
  try {
    const status = await PlayIntegrity.getStatus();
    return { available: isPlayIntegrityAvailable(), ...status };
  } catch {
    return { available: false, prepared: false };
  }
}
