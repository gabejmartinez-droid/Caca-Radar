import { createContext, useContext, useState, useEffect } from "react";
import { translations, isRtl } from "../i18n/translations";

const LanguageContext = createContext(null);

const STORAGE_KEY = "caca-radar-lang";

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    // Check localStorage first
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && translations[saved]) return saved;
    
    // Check browser language
    const browserLang = navigator.language?.split("-")[0];
    if (browserLang && translations[browserLang]) return browserLang;
    
    // Default to Spanish
    return "es";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language);
    
    // Set RTL direction for Arabic
    document.documentElement.dir = isRtl(language) ? "rtl" : "ltr";
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = (lang) => {
    if (translations[lang]) {
      setLanguageState(lang);
    }
  };

  const t = (key) => {
    const keys = key.split(".");
    let value = translations[language];
    
    for (const k of keys) {
      value = value?.[k];
    }
    
    // Fallback to Spanish if key not found
    if (value === undefined) {
      value = translations.es;
      for (const k of keys) {
        value = value?.[k];
      }
    }
    
    return value || key;
  };

  // Helper for time formatting with number replacement
  const tTime = (key, n) => {
    const template = t(key);
    return template.replace("{n}", n);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, tTime, isRtl: isRtl(language) }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
