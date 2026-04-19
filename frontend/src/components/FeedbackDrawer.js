import { useState } from "react";
import { X, Send, Loader2, Bug, Lightbulb, MessageSquare } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { API } from "../config";
import axios from "axios";

const CATEGORIES = [
  { id: "bug", labelKey: "feedbackUi.bug", icon: Bug },
  { id: "suggestion", labelKey: "feedbackUi.suggestion", icon: Lightbulb },
  { id: "other", labelKey: "feedbackUi.other", icon: MessageSquare },
];

export default function FeedbackDrawer({ open, onClose }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [category, setCategory] = useState("bug");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const handleSubmit = async () => {
    if (!message.trim()) { toast.error(t("feedbackUi.messageRequired")); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/feedback`, {
        category,
        message: message.trim(),
        user_email: user?.email || null,
        username: user?.username || null,
      }, { withCredentials: true });
      toast.success(t("feedbackUi.thanks"));
      setMessage("");
      onClose();
    } catch (err) {
      console.error("Feedback submit error:", err);
      toast.error(t("feedbackUi.sendError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] bg-black/50 flex items-end justify-center" onClick={onClose} data-testid="feedback-overlay">
      <div className="bg-white w-full max-w-lg rounded-t-2xl p-5 pb-8 animate-in slide-in-from-bottom" onClick={(e) => e.stopPropagation()} data-testid="feedback-drawer">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-[#2B2D42] text-lg" style={{ fontFamily: "Nunito, sans-serif" }}>{t("feedbackUi.title")}</h3>
          <button onClick={onClose} className="text-[#8D99AE]"><X className="w-5 h-5" /></button>
        </div>

        <div className="flex gap-2 mb-4">
          {CATEGORIES.map(({ id, labelKey, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setCategory(id)}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-colors ${
                category === id ? "bg-[#FF6B6B] text-white" : "bg-gray-100 text-[#8D99AE]"
              }`}
              data-testid={`feedback-cat-${id}`}
            >
              <Icon className="w-3.5 h-3.5" /> {t(labelKey)}
            </button>
          ))}
        </div>

        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={category === "bug" ? t("feedbackUi.bugPlaceholder") : t("feedbackUi.ideaPlaceholder")}
          className="w-full border border-[#8D99AE]/20 rounded-xl p-3 text-sm min-h-[100px] resize-none focus:outline-none focus:ring-2 focus:ring-[#FF6B6B]/30 mb-4"
          data-testid="feedback-message"
        />

        <Button
          onClick={handleSubmit}
          disabled={loading || !message.trim()}
          className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold py-5"
          data-testid="feedback-submit"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Send className="w-4 h-4 mr-2" /> {t("feedbackUi.send")}</>}
        </Button>
      </div>
    </div>
  );
}
