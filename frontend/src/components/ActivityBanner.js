import { useState, useEffect, useMemo, useRef } from "react";
import { Flame, Trophy } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation } from "../utils/ranks";
import { API } from "../config";
import axios from "axios";

const SESSION_KEY_PREFIX = "activity_banner_dismissals";

export default function ActivityBanner({ userLocation, userCity }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const storageKey = `${SESSION_KEY_PREFIX}:${user?._id || user?.email || "guest"}`;
  const [dismissedItems, setDismissedItems] = useState({});
  const touchStartRef = useRef({});

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      setDismissedItems(JSON.parse(window.sessionStorage.getItem(storageKey) || "{}"));
    } catch {
      setDismissedItems({});
    }
  }, [storageKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(storageKey, JSON.stringify(dismissedItems));
  }, [dismissedItems, storageKey]);

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

    const nearbySignature = String(stats.nearby_today || 0);
    if (stats.nearby_today > 0 && dismissedItems.nearby_today !== nearbySignature) {
      return {
        key: "nearby_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.nearbyReportsToday", { count: stats.nearby_today }),
        color: "#FF6B6B",
        signature: nearbySignature,
      };
    }

    const totalSignature = String(stats.total_today || 0);
    if (stats.total_today > 0 && dismissedItems.total_today !== totalSignature) {
      return {
        key: "total_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.spainReportsToday", { count: stats.total_today }),
        color: "#FF6B6B",
        signature: totalSignature,
      };
    }

    return null;
  }, [dismissedItems.nearby_today, dismissedItems.total_today, stats, t]);

  const dismissibleBanners = useMemo(() => {
    if (!stats || !user || !stats.user_rank) return [];

    const cityName = userCity || t("rankUi.cityFallback");
    const rankSignature = `${stats.user_rank}:${cityName}`;

    if (dismissedItems.user_rank === rankSignature) {
      return [];
    }

    return [{
      key: "user_rank",
      icon: Trophy,
      text: formatTranslation(t, "rankUi.cityPosition", {
        rank: stats.user_rank,
        city: cityName,
      }),
      color: "#66BB6A",
      signature: rankSignature,
    }];
  }, [dismissedItems.user_rank, stats, t, user, userCity]);

  if (!primaryBanner && dismissibleBanners.length === 0) return null;

  const dismissBanner = (item) => {
    if (!item?.key || item.signature === undefined) return;
    setDismissedItems((prev) => ({ ...prev, [item.key]: item.signature }));
  };

  const findBannerByKey = (key) => {
    if (primaryBanner?.key === key) return primaryBanner;
    return dismissibleBanners.find((item) => item.key === key) || null;
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
      dismissBanner(findBannerByKey(key));
    }
  };

  const renderBanner = (item) => {
    const Icon = item.icon;

    return (
      <div
        key={item.key}
        className="bg-[#2B2D42]/90 backdrop-blur-sm rounded-xl px-4 py-2.5 flex items-center gap-2.5 shadow-lg transition-all duration-300 cursor-pointer"
        data-testid={`activity-banner-${item.key}`}
        onClick={() => dismissBanner(item)}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            dismissBanner(item);
          }
        }}
        onTouchStart={(event) => handleTouchStart(item.key, event)}
        onTouchEnd={(event) => handleTouchEnd(item.key, event)}
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
      {dismissibleBanners.map((item) => renderBanner(item))}
    </div>
  );
}
