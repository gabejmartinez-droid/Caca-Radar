import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { Mail, Loader2, ArrowLeft, CheckCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { formatTranslation } from "../utils/ranks";
import { API } from "../config";
import axios from "axios";

export default function ForgotPasswordPage() {
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email: email.trim() });
      setSent(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("authRecovery.sendError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#F8F9FA] flex flex-col ${isRtl ? "rtl" : "ltr"}`} data-testid="forgot-password-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/login")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className={`w-4 h-4 ${isRtl ? "ml-2" : "mr-2"}`} />
          {t("login")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6">
        <div className="flex items-center gap-2 mb-8">
          <img src="/icon-64x64.png" alt="Caca Radar" className="w-12 h-12 rounded-xl" />
          <span className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
            {t("appName")}
          </span>
        </div>

        <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-6">
          {sent ? (
            <div className="text-center py-4" data-testid="forgot-success">
              <CheckCircle className="w-12 h-12 text-[#66BB6A] mx-auto mb-3" />
              <h2 className="text-lg font-bold text-[#2B2D42] mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
                {t("authRecovery.checkEmailTitle")}
              </h2>
              <p className="text-sm text-[#8D99AE] mb-4">
                {formatTranslation(t, "authRecovery.checkEmailBody", { email })}
              </p>
              <Button variant="outline" onClick={() => navigate("/login")} className="text-[#FF6B6B] border-[#FF6B6B]" data-testid="back-to-login">
                {t("authRecovery.backToLogin")}
              </Button>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-[#2B2D42] text-center mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
                {t("authRecovery.forgotTitle")}
              </h1>
              <p className="text-sm text-[#8D99AE] text-center mb-6">
                {t("authRecovery.forgotDescription")}
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="email" className="text-[#2B2D42]">{t("email")}</Label>
                  <div className="relative mt-1">
                    <Mail className={`absolute ${isRtl ? "right-3" : "left-3"} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={t("emailPlaceholder")}
                      className={isRtl ? "pr-10" : "pl-10"}
                      autoCapitalize="none"
                      autoCorrect="off"
                      autoComplete="email"
                      spellCheck={false}
                      required
                      data-testid="email-input"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold"
                  style={{ fontFamily: "Nunito, sans-serif" }}
                  data-testid="submit-btn"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("authRecovery.sendLink")}
                </Button>
              </form>
            </>
          )}

          <p className="text-center text-[#8D99AE] text-sm mt-4">
            <Link to="/login" className="text-[#FF6B6B] font-medium hover:underline">
              {t("authRecovery.backToLogin")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
