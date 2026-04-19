import { ArrowLeft, ChevronRight, Mail, LifeBuoy, Shield, Trash2, FileText } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../contexts/LanguageContext";

export default function HelpPage() {
  const navigate = useNavigate();
  const { isRtl } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="help-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-3xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex items-center gap-3 mb-3">
            <LifeBuoy className="w-6 h-6 text-[#FF6B6B]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              Help
            </h1>
          </div>
          <p className="text-[#5C677D] leading-7">
            Need support, legal information, or help with your account? This page is the quickest way to reach the right place.
          </p>
        </section>

        <div className="space-y-6">
          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Mail className="w-5 h-5 text-[#42A5F5]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Contact / support</h2>
            </div>
            <p className="text-[#5C677D] leading-7">
              For support, privacy questions, or general contact, email <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
            </p>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Shield className="w-5 h-5 text-[#66BB6A]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Privacy</h2>
            </div>
            <Link
              to="/privacy"
              className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
              data-testid="help-privacy-link"
            >
              <span className="font-medium">Privacy Policy</span>
              <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
            </Link>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <FileText className="w-5 h-5 text-[#FFA726]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Terms of Use</h2>
            </div>
            <div className="rounded-xl border border-dashed border-[#8D99AE]/30 px-4 py-3 text-sm text-[#8D99AE]">
              Terms of Use placeholder. Add the final published terms route or document here when available.
            </div>
          </section>

          <section className="bg-white rounded-2xl shadow-sm p-6">
            <div className="flex items-center gap-3 mb-3">
              <Trash2 className="w-5 h-5 text-[#FF6B6B]" />
              <h2 className="text-xl font-bold text-[#2B2D42]">Account deletion / data deletion</h2>
            </div>
            <div className="space-y-3 text-[#5C677D] leading-7">
              <p>
                You can manage account deletion from the dedicated in-app route below, or contact us directly if you prefer a manual request.
              </p>
              <Link
                to="/delete-account"
                className="flex items-center justify-between rounded-xl border border-[#8D99AE]/20 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
                data-testid="help-delete-account-link"
              >
                <span className="font-medium">Delete Account</span>
                <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
              </Link>
              <p>
                You can also request account or data deletion by emailing{" "}
                <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
