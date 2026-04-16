import { useState } from "react";
import { toast } from "sonner";
import { User, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { useLanguage } from "../contexts/LanguageContext";
import axios from "axios";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

export default function UsernamePrompt({ onComplete }) {
  const { t } = useLanguage();
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

    setLoading(true);
    try {
      await axios.put(`${API}/users/username`, { username: trimmed }, { withCredentials: true });
      toast.success(t("usernameSaved"));
      onComplete(trimmed);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : t("genericError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-black/50 flex items-center justify-center p-4" data-testid="username-prompt-overlay">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6" data-testid="username-prompt">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-[#FF6B6B] rounded-full flex items-center justify-center">
            <User className="w-6 h-6 text-white" />
          </div>
        </div>

        <h2 className="text-xl font-bold text-[#2B2D42] text-center mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
          {t("pickUsername")}
        </h2>
        <p className="text-sm text-[#8D99AE] text-center mb-5">
          {t("pickUsernameDesc")}
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="username-prompt-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
            <Input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value.replace(/[^a-zA-Z0-9_]/g, ""))}
              placeholder={t("usernamePlaceholder")}
              className="pl-10"
              maxLength={20}
              autoFocus
              data-testid="username-prompt-input"
            />
          </div>
          <p className="text-xs text-[#8D99AE]">{t("usernameHint")}</p>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold"
            style={{ fontFamily: "Nunito, sans-serif" }}
            data-testid="username-prompt-submit"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("saveUsername")}
          </Button>
        </form>
      </div>
    </div>
  );
}
