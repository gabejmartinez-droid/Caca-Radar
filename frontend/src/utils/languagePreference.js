import { translations } from "../i18n/translations";

export const LANGUAGE_STORAGE_KEY = "caca-radar-lang";
const LANGUAGE_EVENT = "caca-radar-language-change";

export function normalizeLanguage(language) {
  if (!language || typeof language !== "string") return null;
  const normalized = language.trim().toLowerCase();
  return translations[normalized] ? normalized : null;
}

export function getBrowserLanguage() {
  if (typeof navigator === "undefined") return null;
  return normalizeLanguage(navigator.language?.split("-")[0]);
}

export function getStoredLanguage() {
  if (typeof window === "undefined") return null;
  return normalizeLanguage(window.localStorage.getItem(LANGUAGE_STORAGE_KEY));
}

export function getInitialLanguage() {
  return getStoredLanguage() || getBrowserLanguage() || "es";
}

export function applyLanguagePreference(language) {
  const normalized = normalizeLanguage(language);
  if (!normalized || typeof window === "undefined") return null;
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, normalized);
  window.dispatchEvent(new CustomEvent(LANGUAGE_EVENT, { detail: { language: normalized } }));
  return normalized;
}

export function subscribeToLanguagePreference(callback) {
  if (typeof window === "undefined") return () => {};

  const handler = (event) => {
    const nextLanguage = normalizeLanguage(event.detail?.language);
    if (nextLanguage) {
      callback(nextLanguage);
    }
  };

  window.addEventListener(LANGUAGE_EVENT, handler);
  return () => window.removeEventListener(LANGUAGE_EVENT, handler);
}
