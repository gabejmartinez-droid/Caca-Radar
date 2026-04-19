import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useLanguage } from "../contexts/LanguageContext";
import { API } from "../config";
import { setTokens, isCapacitorNative } from "../tokenManager";

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("Waiting for Google session");

  const updateStatus = (message) => {
    setStatus(message);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("google_callback_status", message);
    }
  };

  useEffect(() => {
    const handleCallback = async () => {
      updateStatus("Reading callback URL");
      const hash = typeof window !== "undefined" ? window.location.hash.replace(/^#/, "") : "";
      const hashParams = new URLSearchParams(hash);
      const sessionId = searchParams.get("session_id") || hashParams.get("session_id");
      if (!sessionId) {
        updateStatus("No session_id found in callback URL");
        setError("No session ID received from Google");
        setTimeout(() => navigate("/login"), 2000);
        return;
      }

      if (typeof window !== "undefined" && window.location.hash) {
        updateStatus("Cleaning callback URL");
        window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
      }

      try {
        updateStatus("Exchanging Google session with backend");
        const response = await fetch(`${API}/auth/google`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: isCapacitorNative() ? "omit" : "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw {
            response: {
              data,
            },
          };
        }

        if (data.access_token) {
          updateStatus("Saving auth tokens");
          setTokens(data.access_token, data.refresh_token);
        }

        if (typeof window !== "undefined") {
          updateStatus("Login succeeded, redirecting to map");
          const destination = "/?google_login=1";
          window.location.replace(destination);
          window.setTimeout(() => {
            if (window.location.pathname.includes("/auth/google/callback")) {
              window.location.assign(destination);
            }
          }, 250);
          return;
        }
        navigate("/");
      } catch (err) {
        const detail = err.response?.data?.detail || t("loginUi.googleError");
        updateStatus("Google callback failed");
        setError(detail);
        toast.error(detail);
        setTimeout(() => navigate("/login"), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, t]);

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
          <p className="text-[#8D99AE] text-xs mt-2">{status}</p>
        </div>
      )}
    </div>
  );
}
