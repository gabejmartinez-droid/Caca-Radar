import { useCallback, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { Mail, Lock, User, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import LegalLinksFooter from "../components/LegalLinksFooter";

function formatApiErrorDetail(detail, t) {
  if (detail == null) return t("genericError");
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default function RegisterPage() {
  const { register, googleLogin } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    
    const trimmed = username.trim().toLowerCase();
    if (trimmed.length < 3 || trimmed.length > 20) {
      setError(t("usernameLength"));
      return;
    }
    if (!/^[a-z0-9_]+$/.test(trimmed)) {
      setError(t("usernameChars"));
      return;
    }
    if (password.length < 6) {
      setError(t("passwordTooShort"));
      return;
    }
    
    setLoading(true);

    try {
      await register(email.trim().toLowerCase(), password, trimmed);
      toast.success(t("registerSuccess"));
      navigate("/");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail, t) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#F8F9FA] flex flex-col ${isRtl ? 'rtl' : 'ltr'}`} data-testid="register-page">
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
            {t("register")}
          </h1>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username" className="text-[#2B2D42]">{t("username")}</Label>
              <div className="relative mt-1">
                <User className={`absolute ${isRtl ? 'right-3' : 'left-3'} top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]`} />
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))}
                  placeholder={t("usernamePlaceholder")}
                  className={isRtl ? 'pr-10' : 'pl-10'}
                  autoCapitalize="none"
                  autoCorrect="off"
                  autoComplete="username"
                  spellCheck={false}
                  maxLength={20}
                  required
                  data-testid="username-input"
                />
              </div>
              <p className="text-xs text-[#8D99AE] mt-1">{t("usernameHint")}</p>
            </div>

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
                  placeholder={t("passwordPlaceholder")}
                  className={isRtl ? 'pr-10' : 'pl-10'}
                  autoCapitalize="none"
                  autoCorrect="off"
                  autoComplete="new-password"
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
                t("register")
              )}
            </Button>
          </form>

          <p className="text-center text-xs text-[#8D99AE] mt-3 leading-5">
            {t("legalUi.signupNotice")}{" "}
            <Link to="/privacy" className="text-[#FF6B6B] font-medium hover:underline" data-testid="register-privacy-link">
              {t("legalUi.privacyPolicy")}
            </Link>
            {" "}{t("legalUi.andTerms")}{" "}
            <Link to="/terms" className="text-[#FF6B6B] font-medium hover:underline" data-testid="register-terms-link">
              {t("legalUi.termsOfUse")}
            </Link>
          </p>

          {/* Social Sign-Up */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 my-3">
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
              <span className="text-xs text-[#8D99AE]">{t("loginUi.or")}</span>
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
            </div>
            <GoogleSignInButton
              onCredential={handleGoogleLogin}
              onError={handleGoogleError}
              text="signup_with"
              context="signup"
              testId="google-register-btn"
            />
          </div>

          <p className="text-center text-[#8D99AE] text-sm mt-4">
            {t("hasAccount")}{" "}
            <Link to="/login" className="text-[#FF6B6B] font-medium hover:underline" data-testid="login-link">
              {t("loginLink")}
            </Link>
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
