import { useState, useEffect, useMemo, useRef } from "react";
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
  const [dismissedItems, setDismissedItems] = useState({});
  const touchStartRef = useRef({});

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

  const primaryBanner = useMemo(() => {
    if (!stats) return null;
    if (stats.nearby_today > 0) {
      return {
        key: "nearby_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.nearbyReportsToday", { count: stats.nearby_today }),
        color: "#FF6B6B",
      };
    }
    if (stats.total_today > 0) {
      return {
        key: "total_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.spainReportsToday", { count: stats.total_today }),
        color: "#FF6B6B",
      };
    }
    return null;
  }, [stats, t]);

  const dismissibleBanners = useMemo(() => {
    if (!stats) return [];

    const banners = [];

    if (!dismissedItems.active_zones && stats.active_zones > 0) {
      banners.push({
        key: "active_zones",
        icon: AlertTriangle,
        text: formatTranslation(t, userCity ? "activityUi.activeZonesInCity" : "activityUi.activeZones", {
          count: stats.active_zones,
          city: userCity,
        }),
        color: "#FFA726",
      });
    }

    if (!dismissedItems.user_rank && user && stats.user_rank) {
      banners.push({
        key: "user_rank",
        icon: Trophy,
        text: formatTranslation(t, "rankUi.cityPosition", {
          rank: stats.user_rank,
          city: userCity || t("rankUi.cityFallback"),
        }),
        color: "#66BB6A",
      });
    }

    return banners;
  }, [dismissedItems.active_zones, dismissedItems.user_rank, stats, t, user, userCity]);

  if (!primaryBanner && dismissibleBanners.length === 0) return null;

  const dismissBanner = (key) => {
    if (key !== "active_zones" && key !== "user_rank") return;
    setDismissedItems((prev) => ({ ...prev, [key]: true }));
  };

  const handleTouchStart = (key, event) => {
    const touch = event.touches[0];
    touchStartRef.current[key] = { x: touch.clientX, y: touch.clientY };
  };

  const handleTouchEnd = (key, event) => {
    const start = touchStartRef.current[key];
    if (!start) return;

    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - start.x;
    const deltaY = touch.clientY - start.y;
    delete touchStartRef.current[key];

    if (Math.abs(deltaX) > 40 && Math.abs(deltaX) > Math.abs(deltaY)) {
      dismissBanner(key);
    }
  };

  const renderBanner = (item, { dismissOnTap = false } = {}) => {
    const Icon = item.icon;

    return (
      <div
        key={item.key}
        className={`bg-[#2B2D42]/90 backdrop-blur-sm rounded-xl px-4 py-2.5 flex items-center gap-2.5 shadow-lg transition-all duration-300 ${dismissOnTap ? "cursor-pointer" : ""}`}
        data-testid={`activity-banner-${item.key}`}
        onClick={dismissOnTap ? () => dismissBanner(item.key) : undefined}
        role={dismissOnTap ? "button" : undefined}
        tabIndex={dismissOnTap ? 0 : undefined}
        onKeyDown={
          dismissOnTap
            ? (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  dismissBanner(item.key);
                }
              }
            : undefined
        }
        onTouchStart={dismissOnTap ? (event) => handleTouchStart(item.key, event) : undefined}
        onTouchEnd={dismissOnTap ? (event) => handleTouchEnd(item.key, event) : undefined}
      >
        <Icon className="w-4 h-4 shrink-0" style={{ color: item.color }} />
        <span className="text-white text-xs font-medium flex-1">{item.text}</span>
      </div>
    );
  };

  return (
    <div
      className="absolute left-4 right-4 z-[999] flex flex-col gap-2"
      style={{ top: "calc(env(safe-area-inset-top, 0px) + 68px)" }}
      data-testid="activity-banner"
    >
      {primaryBanner && renderBanner(primaryBanner)}
      {dismissibleBanners.map((item) => renderBanner(item, { dismissOnTap: true }))}
    </div>
  );
}
