import { Link } from "react-router-dom";

const LINKS = [
  { to: "/privacy", label: "Privacidad" },
  { to: "/terms", label: "Términos" },
  { to: "/cookies", label: "Cookies" },
  { to: "/status", label: "Estado" },
  { to: "/delete-account", label: "Eliminar cuenta" },
  { to: "/community", label: "Normas de la comunidad" },
];

export default function LegalLinksFooter({ className = "" }) {
  return (
    <div className={`flex flex-wrap gap-x-4 gap-y-2 text-sm text-[#8D99AE] ${className}`.trim()}>
      {LINKS.map((link) => (
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
