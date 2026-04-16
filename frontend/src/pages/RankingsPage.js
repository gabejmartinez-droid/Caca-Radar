import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Trophy, MapPin, Share2, Building2, ChevronDown, Lock, Loader2, BarChart3 } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { toast } from "sonner";
import axios from "axios";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

function CityRankingCard({ city, index, type }) {
  const isClean = type === "cleanest";
  const bgColor = isClean ? "bg-emerald-50" : "bg-red-50";
  const accentColor = isClean ? "text-emerald-600" : "text-red-500";
  const badgeColor = isClean ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700";

  return (
    <div className={`${bgColor} rounded-xl p-4 flex items-center gap-3`} data-testid={`city-rank-${index}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-sm ${badgeColor}`}>
        {city.rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-bold text-[#2B2D42] text-sm truncate">{city.city}</p>
        <p className="text-xs text-[#8D99AE]">{city.province}</p>
      </div>
      <div className="text-right shrink-0">
        <p className={`font-black text-lg ${accentColor}`}>{city.reports_per_10k}</p>
        <p className="text-[10px] text-[#8D99AE]">/ 10.000 hab.</p>
      </div>
    </div>
  );
}

function BarrioCard({ barrio, index }) {
  const intensity = Math.min(barrio.active_reports * 15, 100);
  return (
    <div className="bg-white rounded-xl p-4 flex items-center gap-3 border border-[#8D99AE]/10" data-testid={`barrio-rank-${index}`}>
      <div className="w-8 h-8 rounded-full flex items-center justify-center font-black text-sm bg-[#FF6B6B]/10 text-[#FF6B6B]">
        {barrio.rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-bold text-[#2B2D42] text-sm truncate">{barrio.barrio}</p>
        <p className="text-xs text-[#8D99AE]">{barrio.verified_reports} verificados</p>
      </div>
      <div className="text-right shrink-0">
        <p className="font-black text-lg text-[#FF6B6B]">{barrio.active_reports}</p>
        <p className="text-[10px] text-[#8D99AE]">reportes</p>
      </div>
      <div className="w-12 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full bg-[#FF6B6B] rounded-full" style={{ width: `${intensity}%` }} />
      </div>
    </div>
  );
}

export default function RankingsPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [tab, setTab] = useState("cities");
  const [listType, setListType] = useState("dirtiest");
  const [cityData, setCityData] = useState(null);
  const [barrioData, setBarrioData] = useState(null);
  const [selectedCity, setSelectedCity] = useState("Madrid");
  const [loading, setLoading] = useState(true);
  const [cities, setCities] = useState([]);

  const isPremium = user?.subscription_active;

  useEffect(() => {
    if (!isPremium) { setLoading(false); return; }
    const fetchCities = async () => {
      try {
        const { data } = await axios.get(`${API}/rankings/cities`, { withCredentials: true });
        setCityData(data);
        const uniqueCities = [...new Set(data.dirtiest.map(c => c.city))];
        setCities(uniqueCities);
      } catch { toast.error("Error loading rankings"); }
      finally { setLoading(false); }
    };
    fetchCities();
  }, [isPremium]);

  useEffect(() => {
    if (!isPremium || tab !== "barrios") return;
    const fetchBarrios = async () => {
      setLoading(true);
      try {
        const { data } = await axios.get(`${API}/rankings/barrios?city=${encodeURIComponent(selectedCity)}`, { withCredentials: true });
        setBarrioData(data);
      } catch { toast.error("Error loading barrio data"); }
      finally { setLoading(false); }
    };
    fetchBarrios();
  }, [isPremium, tab, selectedCity]);

  const handleShare = async (type) => {
    try {
      const { data } = await axios.get(`${API}/rankings/cities/share?list_type=${type}`);
      if (navigator.share) {
        await navigator.share({ title: data.title, text: data.share_text, url: data.app_url });
      } else {
        await navigator.clipboard.writeText(data.share_text);
        toast.success("Copiado al portapapeles");
      }
    } catch (err) {
      if (err.name !== "AbortError") toast.error("Error al compartir");
    }
  };

  if (!isPremium) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col" data-testid="rankings-page">
        <div className="p-4 flex justify-between items-center">
          <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
            <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
          </Button>
          <LanguageSelector />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <Lock className="w-12 h-12 text-[#8D99AE] mb-4" />
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Rankings Premium</h2>
          <p className="text-[#8D99AE] text-sm mb-6">Accede a los rankings de ciudades y barrios con Caca Radar Premium</p>
          <Button onClick={() => navigate("/subscribe")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-8 py-5" data-testid="upgrade-btn">
            Ver planes Premium
          </Button>
        </div>
      </div>
    );
  }

  const currentList = cityData ? (listType === "dirtiest" ? cityData.dirtiest : cityData.cleanest) : [];

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="rankings-page">
      <div className="p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-20">
        <div className="text-center mb-5">
          <BarChart3 className="w-10 h-10 text-[#FF6B6B] mx-auto mb-2" />
          <h1 className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>Rankings</h1>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2 mb-5">
          <button
            onClick={() => setTab("cities")}
            className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-colors ${tab === "cities" ? "bg-[#FF6B6B] text-white" : "bg-white text-[#8D99AE] border border-[#8D99AE]/20"}`}
            data-testid="tab-cities"
          >
            <Building2 className="w-4 h-4 inline mr-1" /> Ciudades
          </button>
          <button
            onClick={() => setTab("barrios")}
            className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-colors ${tab === "barrios" ? "bg-[#FF6B6B] text-white" : "bg-white text-[#8D99AE] border border-[#8D99AE]/20"}`}
            data-testid="tab-barrios"
          >
            <MapPin className="w-4 h-4 inline mr-1" /> Barrios
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" /></div>
        ) : tab === "cities" ? (
          <>
            {/* Cleanest / Dirtiest toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setListType("dirtiest")}
                className={`flex-1 py-2 rounded-lg text-xs font-bold transition-colors ${listType === "dirtiest" ? "bg-red-100 text-red-700" : "bg-white text-[#8D99AE]"}`}
                data-testid="toggle-dirtiest"
              >
                Más sucias
              </button>
              <button
                onClick={() => setListType("cleanest")}
                className={`flex-1 py-2 rounded-lg text-xs font-bold transition-colors ${listType === "cleanest" ? "bg-emerald-100 text-emerald-700" : "bg-white text-[#8D99AE]"}`}
                data-testid="toggle-cleanest"
              >
                Más limpias
              </button>
            </div>

            <p className="text-xs text-[#8D99AE] mb-3 text-center">
              {cityData?.total_cities || 0} ciudades con reportes activos. Ordenadas por reportes / 10.000 hab.
            </p>

            <div className="space-y-2 mb-4">
              {currentList.map((city, i) => (
                <CityRankingCard key={city.city} city={city} index={i} type={listType} />
              ))}
              {currentList.length === 0 && (
                <p className="text-center text-[#8D99AE] py-8">No hay datos suficientes</p>
              )}
            </div>

            {/* Share button */}
            <Button onClick={() => handleShare(listType)} variant="outline" className="w-full border-[#FF6B6B]/30 text-[#FF6B6B] hover:bg-[#FF6B6B]/10 rounded-xl" data-testid="share-rankings-btn">
              <Share2 className="w-4 h-4 mr-2" /> Compartir ranking
            </Button>
          </>
        ) : (
          <>
            {/* City selector */}
            <div className="mb-4">
              <label className="text-xs font-bold text-[#2B2D42] mb-1 block">Ciudad</label>
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full p-3 bg-white border border-[#8D99AE]/20 rounded-xl text-sm text-[#2B2D42]"
                data-testid="city-selector"
              >
                {cities.map(c => <option key={c} value={c}>{c}</option>)}
                {!cities.includes(selectedCity) && <option value={selectedCity}>{selectedCity}</option>}
              </select>
            </div>

            <p className="text-xs text-[#8D99AE] mb-3 text-center">
              {barrioData?.total_reports || 0} reportes activos en {selectedCity}
            </p>

            <div className="space-y-2">
              {barrioData?.barrios?.map((b, i) => (
                <BarrioCard key={b.barrio} barrio={b} index={i} />
              ))}
              {(!barrioData?.barrios || barrioData.barrios.length === 0) && (
                <p className="text-center text-[#8D99AE] py-8">No hay datos de barrios para esta ciudad</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
