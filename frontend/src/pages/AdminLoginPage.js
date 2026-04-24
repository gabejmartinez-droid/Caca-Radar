import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Shield, Mail, Lock, Loader2, KeyRound } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation } from "../utils/ranks";
import axios from "axios";

import { API } from "../config";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [step, setStep] = useState(1); // 1 = credentials, 2 = verify code
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStep1 = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await axios.post(`${API}/admin/login`, { email, password });
      toast.success(t("adminUi.codeSent"));
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || t("municipalityUi.invalidCredentials"));
    } finally {
      setLoading(false);
    }
  };

  const handleStep2 = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await axios.post(`${API}/admin/verify`, { email, code }, { withCredentials: true });
      toast.success(t("adminUi.accessVerified"));
      navigate("/admin");
    } catch (err) {
      setError(err.response?.data?.detail || t("adminUi.wrongCode"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#2B2D42] flex flex-col items-center justify-center px-6" data-testid="admin-login-page">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-14 h-14 bg-[#FF6B6B] rounded-2xl flex items-center justify-center">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-black text-white" style={{ fontFamily: "Nunito, sans-serif" }}>Caca Radar</h1>
          <p className="text-[#FF6B6B] text-sm font-bold">{t("adminUi.panel")}</p>
        </div>
      </div>

      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-6" data-testid="admin-login-form">
        {step === 1 ? (
          <>
            <h2 className="text-lg font-bold text-[#2B2D42] text-center mb-1">{t("adminUi.access")}</h2>
            <p className="text-xs text-[#8D99AE] text-center mb-5">{t("adminUi.stepCredentials")}</p>

            {error && <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">{error}</div>}

            <form onSubmit={handleStep1} className="space-y-4">
              <div>
                <Label className="text-[#2B2D42]">Email</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                  <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="pl-10" required data-testid="admin-email-input" />
                </div>
              </div>
              <div>
                <Label className="text-[#2B2D42]">{t("password")}</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                  <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="pl-10" required data-testid="admin-password-input" />
                </div>
              </div>
              <Button type="submit" disabled={loading} className="w-full bg-[#2B2D42] hover:bg-[#1a1b2e] text-white py-5 rounded-xl font-bold" data-testid="admin-login-submit">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("adminUi.continue")}
              </Button>
            </form>
          </>
        ) : (
          <>
            <h2 className="text-lg font-bold text-[#2B2D42] text-center mb-1">{t("adminUi.verification")}</h2>
            <p className="text-xs text-[#8D99AE] text-center mb-5">{t("adminUi.stepCode")}</p>

            {error && <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">{error}</div>}

            <form onSubmit={handleStep2} className="space-y-4">
              <div>
                <Label className="text-[#2B2D42]">{t("municipalityUi.verificationCode")}</Label>
                <div className="relative mt-1">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                  <Input type="text" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="000000" className="pl-10 text-center text-2xl tracking-[0.3em] font-bold" maxLength={6} autoFocus required data-testid="admin-code-input" />
                </div>
              </div>
              <Button type="submit" disabled={loading || code.length < 6} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold" data-testid="admin-verify-submit">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("adminUi.verifyAccess")}
              </Button>
              <button type="button" onClick={() => { setStep(1); setCode(""); setError(""); }} className="w-full text-sm text-[#8D99AE] hover:text-[#2B2D42]">
                {t("adminUi.backToStep1")}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
