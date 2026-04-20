import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import axios from "axios";
import { toast } from "sonner";
import { ArrowLeft, MapPin, CheckCircle, ThumbsUp, Flame, Share2, Trophy, Loader2, TrendingUp, Building2, Heart } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { formatTranslation } from "../utils/ranks";
import { API } from "../config";
import "leaflet/dist/leaflet.css";

const TYPE_STYLES = {
  cleaned: { color: "#66BB6A", labelKey: "impactUi.cleanedLegend", fill: true },
  active: { color: "#FF6B6B", labelKey: "impactUi.activeLegend", fill: true },
  confirmed: { color: "#42A5F5", labelKey: "impactUi.confirmedLegend", fill: false },
};

function ImpactMap({ points, t }) {
  if (!points || points.length === 0) return null;
  const center = [
    points.reduce((s, p) => s + p.lat, 0) / points.length,
    points.reduce((s, p) => s + p.lng, 0) / points.length,
  ];

  return (
    <div className="h-[300px] rounded-2xl overflow-hidden shadow-sm" data-testid="impact-map">
      <MapContainer center={center} zoom={13} className="h-full w-full" zoomControl={false} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {points.map((p, i) => {
          const style = TYPE_STYLES[p.type] || TYPE_STYLES.active;
          return (
            <CircleMarker
              key={`${p.id}-${i}`}
              center={[p.lat, p.lng]}
              radius={p.type === "cleaned" ? 10 : 7}
              pathOptions={{
                color: style.color,
                fillColor: style.color,
                fillOpacity: style.fill ? 0.6 : 0.2,
                weight: p.type === "cleaned" ? 3 : 2,
              }}
            >
              <Tooltip>{t(style.labelKey)} — {p.municipality || ""}</Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div className="bg-white rounded-xl p-4 text-center shadow-sm">
      <Icon className="w-5 h-5 mx-auto mb-1" style={{ color }} />
      <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
      <p className="text-xs text-[#8D99AE]">{label}</p>
      {sub && <p className="text-[10px] text-[#8D99AE]/70 mt-0.5">{sub}</p>}
    </div>
  );
}

function Timeline({ data, t }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5" data-testid="impact-timeline">
      <h3 className="font-bold text-[#2B2D42] text-sm mb-3 flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-[#42A5F5]" />
        {t("impactUi.monthlyActivity")}
      </h3>
      <div className="flex items-end gap-1.5 h-24">
        {data.slice(-12).map((d) => (
          <div key={d.month} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full rounded-t-md transition-all"
              style={{
                height: `${Math.max((d.count / max) * 80, 4)}px`,
                background: d.count > 0 ? "linear-gradient(to top, #FF6B6B, #FF8E8E)" : "#F0F0F0",
              }}
            />
            <span className="text-[8px] text-[#8D99AE] -rotate-45 origin-center whitespace-nowrap">
              {d.month.slice(5)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ImpactPage() {
  const { user } = useAuth();
  const { isRtl, t } = useLanguage();
  const navigate = useNavigate();
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { navigate("/login"); return; }
    const fetchImpact = async () => {
      try {
        const { data } = await axios.get(`${API}/users/impact`, { withCredentials: true });
        setImpact(data);
      } catch {
        toast.error(t("impactUi.loadError"));
        navigate("/profile");
      } finally {
        setLoading(false);
      }
    };
    fetchImpact();
  }, [user, navigate, t]);

  const handleShare = async () => {
    if (!impact) return;
    const s = impact.stats;
    const text = [
      t("impactUi.shareLead"),
      formatTranslation(t, "impactUi.shareStats1", { reports: s.total_reports, cleaned: s.cleaned_reports }),
      formatTranslation(t, "impactUi.shareStats2", { confirmations: s.total_confirmations, municipalities: s.municipalities_helped }),
      formatTranslation(t, "impactUi.shareScore", { score: s.impact_score }),
      t("impactUi.shareFooter"),
    ].join("\n");

    try {
      if (navigator.share) {
        await navigator.share({ title: t("impactUi.shareTitle"), text });
      } else {
        await navigator.clipboard.writeText(text);
        toast.success(t("impactUi.copied"));
      }
    } catch (err) {
      if (err.name !== "AbortError") toast.error(t("impactUi.shareError"));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" />
      </div>
    );
  }

  if (!impact) return null;

  const { stats, map_points, timeline, municipalities, barrios } = impact;
  const cleanedPct = stats.total_reports > 0
    ? Math.round((stats.cleaned_reports / stats.total_reports) * 100)
    : 0;

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="impact-page">
      {/* Header */}
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/profile")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("impactUi.backProfile")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        {/* Hero */}
        <div className="bg-gradient-to-br from-[#2B2D42] to-[#3D3F5C] rounded-2xl p-6 mb-4 text-center shadow-lg relative overflow-hidden">
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: "radial-gradient(circle at 20% 80%, #FF6B6B 0%, transparent 50%), radial-gradient(circle at 80% 20%, #66BB6A 0%, transparent 50%)"
          }} />
          <div className="relative z-10">
            <Heart className="w-8 h-8 text-[#FF6B6B] mx-auto mb-2 impact-pulse" />
            <h1 className="text-2xl font-black text-white mb-1" style={{ fontFamily: "Nunito, sans-serif" }}>
              {t("impactUi.title")}
            </h1>
            <p className="text-white/60 text-xs mb-4">
              {t("impactUi.subtitle")}
            </p>
            <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-4 py-2">
              <Trophy className="w-4 h-4 text-amber-400" />
              <span className="text-white font-bold text-lg">{stats.impact_score}</span>
              <span className="text-white/50 text-xs">{t("impactUi.impactPoints")}</span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4" data-testid="impact-stats">
          <StatCard icon={MapPin} label={t("impactUi.reportsLabel")} value={stats.total_reports} color="#FF6B6B" />
          <StatCard icon={CheckCircle} label={t("impactUi.cleanedZonesLabel")} value={stats.cleaned_reports} color="#66BB6A" sub={formatTranslation(t, "impactUi.cleanedZonesSub", { percent: cleanedPct })} />
          <StatCard icon={ThumbsUp} label={t("impactUi.confirmationsLabel")} value={stats.total_confirmations} color="#42A5F5" />
          <StatCard icon={Building2} label={t("impactUi.municipalitiesLabel")} value={stats.municipalities_helped} color="#FFA726" />
        </div>

        {/* Impact Map */}
        {map_points.length > 0 && (
          <div className="mb-4">
            <h3 className="font-bold text-[#2B2D42] text-sm mb-2 flex items-center gap-2 px-1">
              <MapPin className="w-4 h-4 text-[#FF6B6B]" />
              {t("impactUi.mapTitle")}
            </h3>
            <ImpactMap points={map_points} t={t} />
            <div className="flex gap-4 mt-2 px-1">
              <div className="flex items-center gap-1.5 text-xs text-[#8D99AE]">
                <div className="w-3 h-3 rounded-full bg-[#66BB6A]" /> {t("impactUi.cleanedLegend")}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#8D99AE]">
                <div className="w-3 h-3 rounded-full bg-[#FF6B6B]" /> {t("impactUi.activeLegend")}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#8D99AE]">
                <div className="w-3 h-3 rounded-full border-2 border-[#42A5F5]" /> {t("impactUi.confirmedLegend")}
              </div>
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="mb-4">
        <Timeline data={timeline} t={t} />
        </div>

        {/* Areas helped */}
        {(municipalities.length > 0 || barrios.length > 0) && (
          <div className="bg-white rounded-2xl shadow-sm p-5 mb-4" data-testid="impact-areas">
            <h3 className="font-bold text-[#2B2D42] text-sm mb-3 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#FFA726]" />
              {t("impactUi.areasTitle")}
            </h3>
            {municipalities.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {municipalities.map((m) => (
                  <span key={m} className="bg-[#FFA726]/10 text-[#FFA726] text-xs font-medium px-2.5 py-1 rounded-full">
                    {m}
                  </span>
                ))}
              </div>
            )}
            {barrios.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {barrios.slice(0, 12).map((b) => (
                  <span key={b} className="bg-[#F8F9FA] text-[#8D99AE] text-[10px] px-2 py-0.5 rounded-full">
                    {b}
                  </span>
                ))}
                {barrios.length > 12 && (
                  <span className="text-[#8D99AE] text-[10px] py-0.5">{formatTranslation(t, "impactUi.moreAreas", { count: barrios.length - 12 })}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* No data state */}
        {map_points.length === 0 && (
          <div className="bg-white rounded-2xl shadow-sm p-8 text-center mb-4" data-testid="impact-empty">
            <MapPin className="w-10 h-10 text-[#8D99AE]/30 mx-auto mb-3" />
            <p className="text-[#2B2D42] font-bold mb-1">{t("impactUi.emptyTitle")}</p>
            <p className="text-[#8D99AE] text-sm mb-4">{t("impactUi.emptyBody")}</p>
            <Button onClick={() => navigate("/")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl">
              {t("impactUi.goToMap")}
            </Button>
          </div>
        )}

        {/* Share Impact */}
        <Button
          onClick={handleShare}
          className="w-full bg-[#2B2D42] hover:bg-[#3D3F5C] text-white rounded-xl py-5 font-bold"
          data-testid="share-impact-btn"
        >
          <Share2 className="w-4 h-4 mr-2" />
          {t("impactUi.shareButton")}
        </Button>

        {/* Motivational footer */}
        <p className="text-center text-[#8D99AE] text-xs mt-4 mb-8">
          {t("impactUi.footer")}
        </p>
      </div>

      <style>{`
        @keyframes impactPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        .impact-pulse {
          animation: impactPulse 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
