import { useState, useEffect } from "react";
import { Flame, AlertTriangle, Trophy } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation } from "../utils/ranks";
import { API } from "../config";
import axios from "axios";

export default function ActivityBanner({ userLocation, userCity }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [idx, setIdx] = useState(0);
  const [hideActiveZones, setHideActiveZones] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const params = userLocation
          ? `?lat=${userLocation.lat}&lng=${userLocation.lng}&radius=5000`
          : "";
        const { data } = await axios.get(`${API}/stats/activity${params}`, { withCredentials: true });
        setStats(data);
      } catch (err) {
        console.error("Activity stats error:", err);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, [userLocation]);

  const items = [];
  if (stats) {
    if (stats.nearby_today > 0) {
      items.push({ key: "nearby_today", icon: Flame, text: formatTranslation(t, "activityUi.nearbyReportsToday", { count: stats.nearby_today }), color: "#FF6B6B" });
    } else if (stats.total_today > 0) {
      items.push({ key: "total_today", icon: Flame, text: formatTranslation(t, "activityUi.spainReportsToday", { count: stats.total_today }), color: "#FF6B6B" });
    }
    if (!hideActiveZones && stats.active_zones > 0) {
      items.push({
        key: "active_zones",
        icon: AlertTriangle,
        text: formatTranslation(t, userCity ? "activityUi.activeZonesInCity" : "activityUi.activeZones", {
          count: stats.active_zones,
          city: userCity,
        }),
        color: "#FFA726",
      });
    }
    if (user && stats.user_rank) {
      items.push({
        key: "user_rank",
        icon: Trophy,
        text: formatTranslation(t, "rankUi.cityPosition", {
          rank: stats.user_rank,
          city: userCity || t("rankUi.cityFallback"),
        }),
        color: "#66BB6A"
      });
    }
  }

  useEffect(() => {
    if (items.length <= 1) return;
    const timer = setInterval(() => setIdx((i) => (i + 1) % items.length), 4000);
    return () => clearInterval(timer);
  }, [items.length]);

  if (!stats || items.length === 0) return null;

  const current = items[idx % items.length];
  const Icon = current.icon;
  const handleBannerClick = () => {
    if (current.key === "active_zones") {
      setHideActiveZones(true);
      setIdx(0);
      return;
    }
    if (items.length > 1) {
      setIdx((i) => (i + 1) % items.length);
    }
  };

  return (
    <div
      className="absolute left-4 right-4 z-[999] bg-[#2B2D42]/90 backdrop-blur-sm rounded-xl px-4 py-2.5 flex items-center gap-2.5 shadow-lg transition-all duration-500 cursor-pointer"
      style={{ top: "calc(env(safe-area-inset-top, 0px) + 68px)" }}
      data-testid="activity-banner"
      onClick={handleBannerClick}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handleBannerClick();
        }
      }}
    >
      <Icon className="w-4 h-4 shrink-0" style={{ color: current.color }} />
      <span className="text-white text-xs font-medium flex-1">{current.text}</span>
      {items.length > 1 && (
        <div className="flex gap-1">
          {items.map((_, i) => (
            <div key={i} className={`w-1.5 h-1.5 rounded-full ${i === idx % items.length ? "bg-white" : "bg-white/30"}`} />
          ))}
        </div>
      )}
    </div>
  );
}
