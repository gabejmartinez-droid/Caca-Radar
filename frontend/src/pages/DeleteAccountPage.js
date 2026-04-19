import { useMemo, useState } from "react";
import { ArrowLeft, AlertTriangle, Trash2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";

export default function DeleteAccountPage() {
  const navigate = useNavigate();
  const { user, deleteAccount, loading } = useAuth();
  const { isRtl, t } = useLanguage();
  const [confirmed, setConfirmed] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const email = useMemo(() => user?.email || t("deleteAccountUi.yourAccount"), [t, user]);

  const handleDelete = async () => {
    if (!confirmed || deleting) return;
    setDeleting(true);
    try {
      await deleteAccount();
      toast.success(t("deleteAccountUi.success"));
      navigate("/", { replace: true });
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("deleteAccountUi.error"));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="delete-account-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-2xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#FF6B6B]/10 flex items-center justify-center">
              <Trash2 className="w-6 h-6 text-[#FF6B6B]" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                {t("deleteAccountUi.title")}
              </h1>
              <p className="text-[#8D99AE] mt-1">{t("deleteAccountUi.subtitle")}</p>
            </div>
          </div>

          {!loading && !user ? (
            <div className="rounded-2xl border border-[#8D99AE]/20 bg-[#F8F9FA] p-5 space-y-3">
              <p className="text-[#5C677D] leading-7">
                {t("deleteAccountUi.signInFirst")}
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to="/login" className="inline-flex items-center rounded-xl bg-[#FF6B6B] px-4 py-2.5 text-white font-semibold">
                  {t("deleteAccountUi.goToLogin")}
                </Link>
                <a href="mailto:jefe@cacaradar.es" className="inline-flex items-center rounded-xl border border-[#8D99AE]/20 px-4 py-2.5 text-[#2B2D42] font-semibold">
                  {t("deleteAccountUi.emailDeletionRequest")}
                </a>
              </div>
            </div>
          ) : (
            <>
              <div className="rounded-2xl border border-[#FF6B6B]/20 bg-[#FFF5F5] p-5 space-y-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[#FF6B6B] mt-0.5 flex-shrink-0" />
                  <div className="space-y-3 text-[#5C677D] leading-7">
                    <p>
                      {t("deleteAccountUi.warningLead")} <span className="font-semibold text-[#2B2D42]">{email}</span>.
                    </p>
                    <p>
                      {t("deleteAccountUi.warningBody1")}
                    </p>
                    <p>
                      {t("deleteAccountUi.warningBody2")}
                    </p>
                  </div>
                </div>
              </div>

              <label className="mt-6 flex items-start gap-3 rounded-2xl border border-[#8D99AE]/20 bg-white p-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-[#8D99AE]"
                />
                <span className="text-sm text-[#2B2D42] leading-6">
                  {t("deleteAccountUi.confirmLabel")}
                </span>
              </label>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button
                  type="button"
                  onClick={handleDelete}
                  disabled={!confirmed || deleting}
                  className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl px-5"
                  data-testid="confirm-delete-account"
                >
                  {deleting ? t("deleteAccountUi.deleting") : t("deleteAccountUi.deleteCta")}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/profile")}
                  className="rounded-xl"
                >
                  {t("deleteAccountUi.keepAccount")}
                </Button>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
