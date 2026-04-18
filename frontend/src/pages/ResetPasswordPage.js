import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { toast } from "sonner";
import { Lock, Loader2, ArrowLeft, CheckCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { API } from "../config";
import axios from "axios";

export default function ResetPasswordPage() {
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError(t("passwordTooShort"));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("authRecovery.passwordsDoNotMatch"));
      return;
    }
    if (!token) {
      setError(t("authRecovery.invalidLink"));
      return;
    }

    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/auth/reset-password`, { token, password });
      setDone(true);
      toast.success(data.message || t("authRecovery.passwordUpdated"));
    } catch (err) {
      setError(err.response?.data?.detail || t("authRecovery.resetError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#F8F9FA] flex flex-col ${isRtl ? "rtl" : "ltr"}`} data-testid="reset-password-page">
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
          {done ? (
            <div className="text-center py-4" data-testid="reset-success">
              <CheckCircle className="w-12 h-12 text-[#66BB6A] mx-auto mb-3" />
              <h2 className="text-lg font-bold text-[#2B2D42] mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
                {t("authRecovery.resetSuccessTitle")}
              </h2>
              <p className="text-sm text-[#8D99AE] mb-4">
                {t("authRecovery.resetSuccessBody")}
              </p>
              <Button onClick={() => navigate("/login")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold" data-testid="go-to-login">
                {t("login")}
              </Button>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-[#2B2D42] text-center mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
                {t("authRecovery.newPasswordTitle")}
              </h1>
              <p className="text-sm text-[#8D99AE] text-center mb-6">
                {t("authRecovery.newPasswordDescription")}
              </p>

              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="password" className="text-[#2B2D42]">{t("authRecovery.newPasswordLabel")}</Label>
                  <div className="relative mt-1">
                    <Lock className={`absolute ${isRtl ? "right-3" : "left-3"} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t("passwordPlaceholder")}
                      className={isRtl ? "pr-10" : "pl-10"}
                      required
                      data-testid="password-input"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="confirm" className="text-[#2B2D42]">{t("authRecovery.confirmPasswordLabel")}</Label>
                  <div className="relative mt-1">
                    <Lock className={`absolute ${isRtl ? "right-3" : "left-3"} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                    <Input
                      id="confirm"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder={t("authRecovery.repeatPasswordPlaceholder")}
                      className={isRtl ? "pr-10" : "pl-10"}
                      required
                      data-testid="confirm-password-input"
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
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("authRecovery.resetPassword")}
                </Button>
              </form>
            </>
          )}

          {!done && (
            <p className="text-center text-[#8D99AE] text-sm mt-4">
              <Link to="/forgot-password" className="text-[#FF6B6B] font-medium hover:underline">
                {t("authRecovery.requestNewLink")}
              </Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
