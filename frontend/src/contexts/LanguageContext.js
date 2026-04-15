import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { translations, isRtl } from "../i18n/translations";

const LanguageContext = createContext(null);

const STORAGE_KEY = "caca-radar-lang";

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && translations[saved]) return saved;
    const browserLang = navigator.language?.split("-")[0];
    if (browserLang && translations[browserLang]) return browserLang;
    return "es";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.dir = isRtl(language) ? "rtl" : "ltr";
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = useCallback((lang) => {
    if (translations[lang]) setLanguageState(lang);
  }, []);

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
