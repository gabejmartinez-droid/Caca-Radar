import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { MapPin, Mail, Lock, User, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { API, HOSTED_WEB_URL } from "../config";
import { isCapacitorNative } from "../tokenManager";

function formatApiErrorDetail(detail, t) {
  if (detail == null) return t("genericError");
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default function RegisterPage() {
  const { register } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleLogin = () => {
    const webOrigin = isCapacitorNative() ? HOSTED_WEB_URL : window.location.origin;
    const redirectUrl = encodeURIComponent(webOrigin + "/auth/google/callback");
    window.location.href = `https://demobackend.emergentagent.com/auth/v1/env/oauth/google?redirect_url=${redirectUrl}`;
  };

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
      await register(email, password, trimmed);
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

          {/* Social Sign-Up */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 my-3">
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
              <span className="text-xs text-[#8D99AE]">o</span>
              <div className="flex-1 h-px bg-[#8D99AE]/20" />
            </div>
            <button onClick={handleGoogleLogin} className="w-full flex items-center justify-center gap-2 border border-[#8D99AE]/20 rounded-xl py-3 hover:bg-gray-50 transition-colors" data-testid="google-register-btn">
              <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
              <span className="text-sm font-medium text-[#2B2D42]">{t("continueWithGoogle") || "Registrarse con Google"}</span>
            </button>
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
      </div>
    </div>
  );
}
