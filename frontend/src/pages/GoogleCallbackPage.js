import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { API } from "../config";
import { setTokens, isCapacitorNative } from "../tokenManager";
import axios from "axios";
import { toast } from "sonner";

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { checkAuth } = useAuth();
  const { t } = useLanguage();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      const sessionId = searchParams.get("session_id");
      if (!sessionId) {
        setError("No session ID received from Google");
        setTimeout(() => navigate("/login"), 2000);
        return;
      }

      try {
        const { data } = await axios.post(
          `${API}/auth/google`,
          { session_id: sessionId },
          { withCredentials: !isCapacitorNative() }
        );

        if (data.access_token) {
          setTokens(data.access_token, data.refresh_token);
        }

        await checkAuth();
        toast.success(t("loginUi.googleSuccess"));
        navigate("/");
      } catch (err) {
        const detail = err.response?.data?.detail || t("loginUi.googleError");
        setError(detail);
        toast.error(detail);
        setTimeout(() => navigate("/login"), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, checkAuth]);

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col items-center justify-center" data-testid="google-callback-page">
      {error ? (
        <div className="text-center">
          <p className="text-red-500 text-sm mb-2">{error}</p>
          <p className="text-[#8D99AE] text-xs">{t("loginUi.redirecting")}</p>
        </div>
      ) : (
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B] mx-auto mb-3" />
          <p className="text-[#2B2D42] font-medium">{t("loginUi.connectingGoogle")}</p>
        </div>
      )}
    </div>
  );
}
