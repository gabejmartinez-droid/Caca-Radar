import { useLanguage } from "../contexts/LanguageContext";
import { Link } from "react-router-dom";

export default function LegalLinksFooter({ className = "" }) {
  const { t } = useLanguage();
  const links = [
    { to: "/privacy", label: t("legalUi.privacyPolicy") },
    { to: "/terms", label: t("legalUi.termsOfUse") },
    { to: "/cookies", label: t("legalUi.cookiesPolicy") },
    { to: "/status", label: t("legalUi.statusPage") },
    { to: "/delete-account", label: t("helpUi.deleteAccountLink") },
    { to: "/community", label: t("legalUi.communityGuidelines") },
  ];

  return (
    <div className={`flex flex-wrap gap-x-4 gap-y-2 text-sm text-[#8D99AE] ${className}`.trim()}>
      {links.map((link) => (
        <Link
          key={link.to}
          to={link.to}
          className="hover:text-[#FF6B6B] transition-colors"
        >
          {link.label}
        </Link>
      ))}
    </div>
  );
}
