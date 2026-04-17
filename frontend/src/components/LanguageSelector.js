import { Globe } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { useLanguage } from "../contexts/LanguageContext";

function FlagIcon({ code, className = "w-5 h-3.5" }) {
  const flags = {
    es: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#c60b1e"/>
        <rect width="640" height="160" fill="#c60b1e"/>
        <rect y="160" width="640" height="160" fill="#ffc400"/>
        <rect y="320" width="640" height="160" fill="#c60b1e"/>
      </svg>
    ),
    en: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#012169"/>
        <path d="M75 0l244 181L562 0h78v62L400 241l240 178v61h-80L320 301 81 480H0v-60l239-178L0 64V0z" fill="#fff"/>
        <path d="M424 281l216 159v40L369 281zm-184 20l6 35L54 480H0zM640 0v3L391 191l2-44L590 0zM0 0l239 176h-60L0 42z" fill="#C8102E"/>
        <path d="M241 0v480h160V0zM0 160v160h640V160z" fill="#fff"/>
        <path d="M0 193v96h640v-96zM273 0v480h96V0z" fill="#C8102E"/>
      </svg>
    ),
    de: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="160" fill="#000"/>
        <rect y="160" width="640" height="160" fill="#D00"/>
        <rect y="320" width="640" height="160" fill="#FFCE00"/>
      </svg>
    ),
    nl: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="160" fill="#AE1C28"/>
        <rect y="160" width="640" height="160" fill="#FFF"/>
        <rect y="320" width="640" height="160" fill="#21468B"/>
      </svg>
    ),
    pl: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="240" fill="#FFF"/>
        <rect y="240" width="640" height="240" fill="#DC143C"/>
      </svg>
    ),
    ar: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#006C35"/>
        <rect width="640" height="160" fill="#006C35"/>
        <rect y="160" width="640" height="160" fill="#FFF"/>
        <rect y="320" width="640" height="160" fill="#000"/>
      </svg>
    ),
    uk: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="240" fill="#005BBB"/>
        <rect y="240" width="640" height="240" fill="#FFD500"/>
      </svg>
    ),
    ru: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="160" fill="#FFF"/>
        <rect y="160" width="640" height="160" fill="#0039A6"/>
        <rect y="320" width="640" height="160" fill="#D52B1E"/>
      </svg>
    ),
    eu: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#D52B1E"/>
        <rect width="640" height="240" fill="#009B48"/>
        <path d="M0 0h320v480H0z" fill="#fff" opacity="0"/>
        <line x1="0" y1="0" x2="640" y2="480" stroke="#fff" strokeWidth="40"/>
        <line x1="640" y1="0" x2="0" y2="480" stroke="#fff" strokeWidth="40"/>
      </svg>
    ),
    ca: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#FCDD09"/>
        <path stroke="#DA121A" strokeWidth="53.3" d="M0 53.3h640M0 160h640M0 266.7h640M0 373.3h640"/>
      </svg>
    ),
    val: (
      <svg viewBox="0 0 640 480" className={className}>
        <rect width="640" height="480" fill="#FCDD09"/>
        <path stroke="#DA121A" strokeWidth="53.3" d="M0 53.3h640M0 160h640M0 266.7h640M0 373.3h640"/>
        <rect width="213" height="240" fill="#0039A6"/>
      </svg>
    ),
  };
  return flags[code] || <Globe className="w-4 h-4" />;
}

const languages = [
  { code: "es", name: "Español" },
  { code: "en", name: "English" },
  { code: "de", name: "Deutsch" },
  { code: "nl", name: "Nederlands" },
  { code: "pl", name: "Polski" },
  { code: "ar", name: "العربية" },
  { code: "uk", name: "Українська" },
  { code: "ru", name: "Русский" },
  { code: "eu", name: "Euskara" },
  { code: "ca", name: "Català" },
  { code: "val", name: "Valencià" },
];

export function LanguageSelector() {
  const { language, setLanguage } = useLanguage();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="bg-white/95 backdrop-blur-sm shadow-lg border-0 gap-2"
          data-testid="language-selector"
        >
          <FlagIcon code={language} className="w-5 h-3.5 rounded-[1px]" />
          <span className="text-xs font-medium">{languages.find(l => l.code === language)?.name}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`cursor-pointer ${language === lang.code ? "bg-[#FF6B6B]/10 text-[#FF6B6B]" : ""}`}
            data-testid={`lang-${lang.code}`}
          >
            <FlagIcon code={lang.code} className="w-5 h-3.5 rounded-[1px] mr-2 shrink-0" />
            {lang.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
