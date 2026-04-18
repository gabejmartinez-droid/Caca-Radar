import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { compareRanks, formatTranslation, getRankLabel } from "../utils/ranks";
import axios from "axios";

import { API } from "../config";

export default function NotificationChecker() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const checked = useRef(false);

  useEffect(() => {
    if (!user || checked.current) return;
    checked.current = true;

    const checkNotifications = async () => {
      try {
        const { data } = await axios.get(`${API}/notifications`, { withCredentials: true });
        for (const n of data) {
          if (n.type === "rank_change") {
            const rank = getRankLabel(n.new_rank_key || n.new_rank, t);
            const isPromotion = compareRanks(n.new_rank_key || n.new_rank, n.old_rank_key || n.old_rank) < 0;
            if (isPromotion) {
              toast.success(formatTranslation(t, "rankUi.rankPromotion", { rank }), { duration: 6000 });
            } else {
              toast.info(formatTranslation(t, "rankUi.rankChanged", { rank }), { duration: 6000 });
            }
          }
        }
        if (data.length > 0) {
          await axios.post(`${API}/notifications/read`, {}, { withCredentials: true });
        }
      } catch (err) {
        console.error("Failed to check notifications:", err);
      }
    };

    checkNotifications();
  }, [user, t]);

  return null;
}
