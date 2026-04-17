import { useState, useEffect } from "react";
import { Flame, AlertTriangle, Trophy } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { API } from "../config";
import axios from "axios";

export default function ActivityBanner({ userLocation, userCity }) {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [idx, setIdx] = useState(0);

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
      items.push({ icon: Flame, text: `${stats.nearby_today} reportes nuevos cerca de ti hoy`, color: "#FF6B6B" });
    } else if (stats.total_today > 0) {
      items.push({ icon: Flame, text: `${stats.total_today} reportes nuevos en España hoy`, color: "#FF6B6B" });
    }
    if (stats.active_zones > 0) {
      items.push({ icon: AlertTriangle, text: `${stats.active_zones} zonas activas${userCity ? ` en ${userCity}` : ""}`, color: "#FFA726" });
    }
    if (user && stats.user_rank) {
      items.push({ icon: Trophy, text: `Eres #${stats.user_rank} en ${userCity || "tu ciudad"}`, color: "#66BB6A" });
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

  return (
    <div
      className="absolute left-4 right-4 z-[999] bg-[#2B2D42]/90 backdrop-blur-sm rounded-xl px-4 py-2.5 flex items-center gap-2.5 shadow-lg transition-all duration-500"
      style={{ top: "calc(env(safe-area-inset-top, 0px) + 68px)" }}
      data-testid="activity-banner"
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
