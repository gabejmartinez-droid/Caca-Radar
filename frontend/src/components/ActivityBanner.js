import { useState, useEffect, useMemo, useRef } from "react";
import { Flame, Trophy } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation } from "../utils/ranks";
import { API } from "../config";
import axios from "axios";

const SESSION_KEY_PREFIX = "activity_banner_dismissals";
const DAILY_KEY_PREFIX = "activity_banner_daily";

export default function ActivityBanner({ userLocation, userCity }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const storageKey = `${SESSION_KEY_PREFIX}:${user?._id || user?.email || "guest"}`;
  const dailyKey = `${DAILY_KEY_PREFIX}:${user?._id || user?.email || "guest"}`;
  const [dismissedItems, setDismissedItems] = useState({});
  const [dailySeen, setDailySeen] = useState({});
  const touchStartRef = useRef({});
  const today = new Date().toISOString().slice(0, 10);

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
    try {
      setDailySeen(JSON.parse(window.localStorage.getItem(dailyKey) || "{}"));
    } catch {
      setDailySeen({});
    }
  }, [dailyKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(storageKey, JSON.stringify(dismissedItems));
  }, [dismissedItems, storageKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(dailyKey, JSON.stringify(dailySeen));
  }, [dailyKey, dailySeen]);

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

  const banners = useMemo(() => {
    if (!stats) return [];
    const nextBanners = [];

    const nearbySignature = String(stats.nearby_today || 0);
    const nearbySeenToday = dailySeen.nearby_today === today;
    if (stats.nearby_today > 0 && dismissedItems.nearby_today !== nearbySignature && !nearbySeenToday) {
      nextBanners.push({
        key: "nearby_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.nearbyReportsToday", { count: stats.nearby_today }),
        color: "#FF6B6B",
        signature: nearbySignature,
      });
    }

    const totalSignature = String(stats.total_today || 0);
    if (stats.total_today > 0 && dismissedItems.total_today !== totalSignature) {
      nextBanners.push({
        key: "total_today",
        icon: Flame,
        text: formatTranslation(t, "activityUi.spainReportsToday", { count: stats.total_today }),
        color: "#FF6B6B",
        signature: totalSignature,
      });
    }

    if (stats.user_rank && user) {
      const cityName = userCity || t("rankUi.cityFallback");
      const rankSignature = `${stats.user_rank}:${cityName}`;

      if (dismissedItems.user_rank !== rankSignature) {
        nextBanners.push({
          key: "user_rank",
          icon: Trophy,
          text: formatTranslation(t, "rankUi.cityPosition", {
            rank: stats.user_rank,
            city: cityName,
          }),
          color: "#66BB6A",
          signature: rankSignature,
        });
      }
    }

    return nextBanners;
  }, [dailySeen.nearby_today, dismissedItems.nearby_today, dismissedItems.total_today, dismissedItems.user_rank, stats, t, today, user, userCity]);

  useEffect(() => {
    if (!banners.some((item) => item.key === "nearby_today")) return;
    if (dailySeen.nearby_today === today) return;
    setDailySeen((prev) => ({ ...prev, nearby_today: today }));
  }, [banners, dailySeen.nearby_today, today]);

  if (banners.length === 0) return null;

  const dismissBanner = (item) => {
    if (!item?.key || item.signature === undefined) return;
    setDismissedItems((prev) => ({ ...prev, [item.key]: item.signature }));
  };

  const findBannerByKey = (key) => {
    return banners.find((item) => item.key === key) || null;
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
    const handleDismiss = (event) => {
      event?.preventDefault?.();
      event?.stopPropagation?.();
      dismissBanner(item);
    };

    return (
      <div
        key={item.key}
        className="bg-[#2B2D42]/90 backdrop-blur-sm rounded-xl px-4 py-2.5 flex items-center gap-2.5 shadow-lg transition-all duration-300 cursor-pointer"
        data-testid={`activity-banner-${item.key}`}
        onClick={handleDismiss}
        onMouseDown={(event) => event.stopPropagation()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleDismiss(event);
          }
        }}
        onTouchStart={(event) => {
          event.stopPropagation();
          handleTouchStart(item.key, event);
        }}
        onTouchEnd={(event) => {
          event.stopPropagation();
          handleTouchEnd(item.key, event);
        }}
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
      {banners.map((item) => renderBanner(item))}
    </div>
  );
}
