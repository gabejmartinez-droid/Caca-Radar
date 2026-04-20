import { ArrowLeft, ChevronRight, Mail, LifeBuoy, Shield, Trash2, FileText, Cookie, Flag } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../contexts/LanguageContext";
import LegalLinksFooter from "../components/LegalLinksFooter";

export default function HelpPage() {
  const navigate = useNavigate();
  const { isRtl, t } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="help-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-3xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex items-center gap-3 mb-3">
            <LifeBuoy className="w-6 h-6 text-[#FF6B6B]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              {t("helpUi.title")}
            </h1>
          </div>
          <p className="text-[#5C677D] leading-7">
            {t("helpUi.intro")}
          </p>
          <div className="mt-4 rounded-2xl bg-[#F8F9FA] px-4 py-3 text-sm text-[#5C677D]">
            Caca Radar es una herramienta privada, independiente y no oficial. No representa, sustituye ni está afiliada a ningún ayuntamiento,
            administración pública ni entidad gubernamental.
          </div>
        </section>

        <div className="space-y-6">
          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Mail className="w-5 h-5 text-[#42A5F5]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">{t("helpUi.contactTitle")}</h2>
            </div>
            <p className="text-[#5C677D] leading-7">
              {t("helpUi.contactBody")} <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
            </p>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Shield className="w-5 h-5 text-[#66BB6A]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">{t("helpUi.privacyTitle")}</h2>
            </div>
            <Link
              to="/privacy"
              className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
              data-testid="help-privacy-link"
            >
              <span className="font-medium">{t("legalUi.privacyPolicy")}</span>
              <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
            </Link>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <FileText className="w-5 h-5 text-[#FFA726]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">{t("helpUi.termsTitle")}</h2>
            </div>
            <Link
              to="/terms"
              className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
              data-testid="help-terms-link"
            >
              <span className="font-medium">{t("helpUi.termsTitle")}</span>
              <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
            </Link>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Cookie className="w-5 h-5 text-[#42A5F5]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Cookies y tecnologías similares</h2>
            </div>
            <Link
              to="/cookies"
              className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
              data-testid="help-cookies-link"
            >
              <span className="font-medium">Política de Cookies</span>
              <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
            </Link>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Flag className="w-5 h-5 text-[#FF6B6B]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Normas de la comunidad y moderación</h2>
            </div>
            <Link
              to="/community"
              className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
              data-testid="help-community-link"
            >
              <span className="font-medium">Normas de la comunidad</span>
              <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
            </Link>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Trash2 className="w-5 h-5 text-[#FF6B6B]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">{t("helpUi.deletionTitle")}</h2>
            </div>
            <div className="space-y-3 text-[#5C677D] leading-7">
              <p>
                {t("helpUi.deletionIntro")}
              </p>
              <Link
                to="/delete-account"
                className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
                data-testid="help-delete-account-link"
              >
                <span className="font-medium">{t("helpUi.deleteAccountLink")}</span>
                <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
              </Link>
              <p>
                {t("helpUi.deletionEmailIntro")}{" "}
                <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
              </p>
              <p className="text-sm text-[#8D99AE]">
                Si tienes una suscripción contratada en Apple App Store o Google Play, debes cancelarla también desde tu cuenta de la tienda.
              </p>
            </div>
          </section>

          <LegalLinksFooter className="px-1 pb-2" />
        </div>
      </main>
    </div>
  );
}
