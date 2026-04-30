import { useCallback, useEffect, useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { MapPin, Mail, Lock, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import LegalLinksFooter from "../components/LegalLinksFooter";
import { isAppleSignInSupported } from "../utils/appleIdentity";

function formatApiErrorDetail(detail, t) {
  if (detail == null) return t("genericError");
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default function LoginPage() {
  const { user, login, googleLogin, appleLogin } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const showAppleSignIn = isAppleSignInSupported();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      navigate("/");
    }
  }, [navigate, user]);

  useEffect(() => {
    const appleError = searchParams.get("apple_error");
    if (!appleError) return;
    setError(appleError);
    const next = new URLSearchParams(searchParams);
    next.delete("apple_error");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email.trim().toLowerCase(), password);
      toast.success(t("loginSuccess"));
      navigate("/");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail, t) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = useCallback(async (credential) => {
    try {
      await googleLogin(credential);
      toast.success(t("loginUi.googleSuccess"));
      navigate("/");
    } catch (err) {
      const detail = formatApiErrorDetail(err.response?.data?.detail?.message || err.response?.data?.detail, t) || err.message;
      setError(detail);
      throw err;
    }
  }, [googleLogin, navigate, t]);

  const handleGoogleError = useCallback((err) => {
    const detail = formatApiErrorDetail(err.response?.data?.detail?.message || err.response?.data?.detail, t) || t("loginUi.googleError");
    setError(detail);
  }, [t]);

  const handleAppleLogin = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const result = await appleLogin(window.location.pathname);
      if (result?.redirected) {
        return;
      }
      toast.success(t("loginUi.appleSuccess"));
      navigate("/");
    } catch (err) {
      if (err?.message === "Apple sign-in was cancelled") {
        return;
      }
      const detail = formatApiErrorDetail(err.response?.data?.detail?.message || err.response?.data?.detail, t) || t("loginUi.appleError");
      setError(detail);
    } finally {
      setLoading(false);
    }
  }, [appleLogin, navigate, t]);

  return (
    <div className={`min-h-screen bg-[#F8F9FA] flex flex-col ${isRtl ? 'rtl' : 'ltr'}`} data-testid="login-page">
      {/* Header */}
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="text-[#8D99AE]"
          data-testid="back-btn"
        >
          <ArrowLeft className={`w-4 h-4 ${isRtl ? 'ml-2' : 'mr-2'}`} />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <img src="/icon-64x64.png" alt="Caca Radar" className="w-12 h-12 rounded-xl" />
          <span className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>
            {t("appName")}
          </span>
        </div>

        {/* Form */}
        <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-6">
          <h1 className="text-2xl font-bold text-[#2B2D42] text-center mb-6" style={{ fontFamily: 'Nunito, sans-serif' }}>
            {t("login")}
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-[#2B2D42]">{t("email")}</Label>
              <div className="relative mt-1">
                <Mail className={`absolute ${isRtl ? 'right-3' : 'left-3'} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t("emailPlaceholder")}
                  className={isRtl ? 'pr-10' : 'pl-10'}
                  autoCapitalize="none"
                  autoCorrect="off"
                  autoComplete="email"
                  spellCheck={false}
                  required
                  data-testid="email-input"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password" className="text-[#2B2D42]">{t("password")}</Label>
              <div className="relative mt-1">
                <Lock className={`absolute ${isRtl ? 'right-3' : 'left-3'} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={isRtl ? 'pr-10' : 'pl-10'}
                  autoCapitalize="none"
                  autoCorrect="off"
                  autoComplete="current-password"
                  spellCheck={false}
                  required
                  data-testid="password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold"
              style={{ fontFamily: 'Nunito, sans-serif' }}
              data-testid="submit-btn"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                t("enter")
              )}
            </Button>
          </form>

          <div className="text-center mt-3">
            <Link to="/forgot-password" className="text-sm text-[#8D99AE] hover:text-[#FF6B6B] transition-colors" data-testid="forgot-password-link">
              {t("loginUi.forgotPassword")}
            </Link>
          </div>

          {/* Social Sign-In */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 my-3">
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
              <span className="text-xs text-[#8D99AE]">{t("loginUi.or")}</span>
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
            </div>
            <GoogleSignInButton
              onCredential={handleGoogleLogin}
              onError={handleGoogleError}
              text="continue_with"
              context="signin"
              testId="google-login-btn"
            />
            {showAppleSignIn && (
              <button type="button" onClick={handleAppleLogin} disabled={loading} className="w-full flex items-center justify-center gap-2 border border-[#8D99AE]/20 rounded-xl py-3 bg-black text-white hover:bg-gray-900 transition-colors disabled:opacity-60" data-testid="apple-login-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
                <span className="text-sm font-medium">{loading ? t("loginUi.connectingApple") : t("loginUi.appleSignIn")}</span>
              </button>
            )}
          </div>

          <p className="text-center text-[#8D99AE] text-sm mt-4">
            {t("noAccount")}{" "}
            <Link to="/register" className="text-[#FF6B6B] font-medium hover:underline" data-testid="register-link">
              {t("registerLink")}
            </Link>
          </p>

          <p className="text-center text-xs text-[#8D99AE] mt-4 leading-5">
            {t("legalUi.loginNoticePrefix")}{" "}
            <Link to="/privacy" className="text-[#FF6B6B] font-medium hover:underline" data-testid="login-privacy-link">
              {t("legalUi.privacyPolicy")}
            </Link>
            {" "}{t("legalUi.andTerms")}{" "}
            <Link to="/terms" className="text-[#FF6B6B] font-medium hover:underline" data-testid="login-terms-link">
              {t("legalUi.termsOfUse")}
            </Link>.
          </p>
        </div>

        <p className="text-center text-[#8D99AE] text-sm mt-6 mb-20">
          {t("useWithoutAccount")}
        </p>
        <div className="w-full max-w-sm mb-10">
          <LegalLinksFooter className="justify-center" />
        </div>
      </div>
    </div>
  );
}
