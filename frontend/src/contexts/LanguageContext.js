import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { translations, isRtl } from "../i18n/translations";
import { API } from "../config";
import { isCapacitorNative } from "../tokenManager";
import {
  applyLanguagePreference,
  getInitialLanguage,
  normalizeLanguage,
  subscribeToLanguagePreference,
} from "../utils/languagePreference";
import { syncCompanionPreferences } from "../utils/companionBridge";

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => getInitialLanguage());

  useEffect(() => {
    document.documentElement.dir = isRtl(language) ? "rtl" : "ltr";
    document.documentElement.lang = language;
    syncCompanionPreferences({ preferredLanguage: language });
  }, [language]);

  useEffect(() => subscribeToLanguagePreference((nextLanguage) => {
    setLanguageState((currentLanguage) => (currentLanguage === nextLanguage ? currentLanguage : nextLanguage));
  }), []);

  const persistLanguagePreference = useCallback(async (nextLanguage) => {
    try {
      await axios.put(
        `${API}/users/preferences`,
        { preferred_language: nextLanguage },
        { withCredentials: !isCapacitorNative() },
      );
    } catch (error) {
      if (error?.response?.status !== 401) {
        // Keep the UI responsive even if sync is temporarily unavailable.
      }
    }
  }, []);

  const setLanguage = useCallback((lang) => {
    const normalized = normalizeLanguage(lang);
    if (!normalized || !translations[normalized]) return;
    applyLanguagePreference(normalized);
    setLanguageState(normalized);
    void persistLanguagePreference(normalized);
  }, [persistLanguagePreference]);

  const t = useCallback((key) => {
    const keys = key.split(".");
    let value = translations[language];
    for (const k of keys) { value = value?.[k]; }
    if (value === undefined) {
      value = translations.es;
      for (const k of keys) { value = value?.[k]; }
    }
    return value || key;
  }, [language]);

  const tTime = useCallback((key, n) => {
    const template = t(key);
    return template.replace("{n}", n);
  }, [t]);

  const rtl = useMemo(() => isRtl(language), [language]);

  const value = useMemo(() => ({ language, setLanguage, t, tTime, isRtl: rtl }), [language, setLanguage, t, tTime, rtl]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
