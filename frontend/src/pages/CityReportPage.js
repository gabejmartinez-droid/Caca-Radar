import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import axios from "axios";
import { ArrowLeft, Building2, Loader2, Lock, MapPin, Search, Share2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import SocialShareButtons from "../components/SocialShareButtons";
import { formatTranslation } from "../utils/ranks";
import { shareWithNativeOrCopy } from "../utils/socialShare";
import { API, HOSTED_WEB_URL } from "../config";
import "leaflet/dist/leaflet.css";

const POINT_STYLES = {
  fresh: { color: "#FF5252", fillOpacity: 0.7, radius: 7 },
  older: { color: "#FFA726", fillOpacity: 0.55, radius: 6 },
  fossil: { color: "#66BB6A", fillOpacity: 0.45, radius: 5 },
};

function CityPreviewMap({ summary, t }) {
  if (!summary?.preview_points?.length || !summary?.map_bounds) return null;

  const bounds = [
    [summary.map_bounds.south, summary.map_bounds.west],
    [summary.map_bounds.north, summary.map_bounds.east],
  ];
  const isSinglePoint =
    summary.map_bounds.south === summary.map_bounds.north &&
    summary.map_bounds.west === summary.map_bounds.east;
  const center = [summary.map_bounds.center_lat, summary.map_bounds.center_lng];

  return (
    <div className="h-[220px] rounded-2xl overflow-hidden shadow-sm border border-[#8D99AE]/10" data-testid="city-report-map">
      <MapContainer
        {...(isSinglePoint ? { center, zoom: 14 } : { bounds, boundsOptions: { padding: [20, 20] } })}
        className="h-full w-full"
        zoomControl={false}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {summary.preview_points.map((point, index) => {
          const style = POINT_STYLES[point.bucket] || POINT_STYLES.fossil;
          return (
            <CircleMarker
              key={`${point.id || "point"}-${index}`}
              center={[point.lat, point.lng]}
              radius={style.radius}
              pathOptions={{
                color: style.color,
                fillColor: style.color,
                fillOpacity: style.fillOpacity,
                weight: 2,
              }}
            />
          );
        })}
      </MapContainer>
      <div className="grid grid-cols-3 gap-2 px-3 py-2 bg-white border-t border-[#8D99AE]/10 text-[11px] text-[#5C677D]">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#FF5252]" />
          <span>{t("cityReportUi.freshLabel")}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#FFA726]" />
          <span>{t("cityReportUi.olderLabel")}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#66BB6A]" />
          <span>{t("cityReportUi.fossilLabel")}</span>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-xl border border-[#8D99AE]/10 p-4 shadow-sm">
      <p className="text-xs text-[#8D99AE] mb-1">{label}</p>
      <p className="text-2xl font-black" style={{ color }}>{value}</p>
    </div>
  );
}

export default function CityReportPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cityOptions, setCityOptions] = useState([]);
  const [barrioOptions, setBarrioOptions] = useState([]);
  const [searchValue, setSearchValue] = useState(searchParams.get("city") || "");
  const [barrioSearchValue, setBarrioSearchValue] = useState(searchParams.get("barrio") || "");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [citiesLoading, setCitiesLoading] = useState(false);
  const [barriosLoading, setBarriosLoading] = useState(false);
  const [loadError, setLoadError] = useState("");

  const requestedCity = searchParams.get("city") || "";
  const requestedBarrio = searchParams.get("barrio") || "";
  const isPremium = !!user?.subscription_active;
  const canUseSearch = isPremium;

  useEffect(() => {
    setSearchValue(requestedCity);
  }, [requestedCity]);

  useEffect(() => {
    setBarrioSearchValue(requestedBarrio);
  }, [requestedBarrio]);

  useEffect(() => {
    if (!canUseSearch) return;
    let ignore = false;
    const fetchCities = async () => {
      setCitiesLoading(true);
      try {
        const { data } = await axios.get(`${API}/city-reports/cities`, { withCredentials: true });
        if (!ignore) setCityOptions(data.cities || []);
      } catch {
        if (!ignore) toast.error(t("cityReportUi.cityListError"));
      } finally {
        if (!ignore) setCitiesLoading(false);
      }
    };
    fetchCities();
    return () => { ignore = true; };
  }, [canUseSearch, t]);

  useEffect(() => {
    if (!canUseSearch || !requestedCity) {
      setBarrioOptions([]);
      setBarriosLoading(false);
      return;
    }
    let ignore = false;
    const fetchBarrios = async () => {
      setBarriosLoading(true);
      try {
        const { data } = await axios.get(`${API}/city-reports/barrios?city=${encodeURIComponent(requestedCity)}`, { withCredentials: true });
        if (!ignore) setBarrioOptions(data.barrios || []);
      } catch {
        if (!ignore) toast.error(t("cityReportUi.barrioListError"));
      } finally {
        if (!ignore) setBarriosLoading(false);
      }
    };
    fetchBarrios();
    return () => { ignore = true; };
  }, [canUseSearch, requestedCity, t]);

  useEffect(() => {
    if (!requestedCity) {
      setSummary(null);
      setLoadError("");
      return;
    }

    let ignore = false;
    const fetchSummary = async () => {
      setLoading(true);
      setLoadError("");
      try {
        const query = new URLSearchParams({ city: requestedCity });
        if (requestedBarrio) query.set("barrio", requestedBarrio);
        const endpoint = canUseSearch
          ? `${API}/city-reports?${query.toString()}`
          : `${API}/city-reports/share?${query.toString()}`;
        const { data } = await axios.get(endpoint, canUseSearch ? { withCredentials: true } : undefined);
        if (!ignore) setSummary(data);
      } catch (error) {
        if (ignore) return;
        setSummary(null);
        setLoadError(t("cityReportUi.loadError"));
        if (error?.response?.status !== 404) {
          toast.error(t("cityReportUi.loadError"));
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    fetchSummary();
    return () => { ignore = true; };
  }, [requestedCity, requestedBarrio, canUseSearch, t]);

  const filteredCities = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    if (!query) return cityOptions.slice(0, 12);
    return cityOptions
      .filter((option) => option.city.toLowerCase().includes(query))
      .slice(0, 12);
  }, [cityOptions, searchValue]);

  const selectCity = (city) => {
    setSearchValue(city);
    setBarrioSearchValue("");
    setSearchParams({ city });
  };

  const selectBarrio = (barrio) => {
    setBarrioSearchValue(barrio);
    const next = { city: requestedCity };
    if (barrio) next.barrio = barrio;
    setSearchParams(next);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    const exact = cityOptions.find((option) => option.city.toLowerCase() === searchValue.trim().toLowerCase());
    const fallback = filteredCities[0];
    const target = exact?.city || fallback?.city;
    if (!target) {
      toast.error(t("cityReportUi.noMatches"));
      return;
    }
    selectCity(target);
  };

  const filteredBarrios = useMemo(() => {
    const query = barrioSearchValue.trim().toLowerCase();
    if (!query) return barrioOptions.slice(0, 12);
    return barrioOptions
      .filter((option) => option.barrio.toLowerCase().includes(query))
      .slice(0, 12);
  }, [barrioOptions, barrioSearchValue]);

  const handleBarrioSubmit = (event) => {
    event.preventDefault();
    const exact = barrioOptions.find((option) => option.barrio.toLowerCase() === barrioSearchValue.trim().toLowerCase());
    const fallback = filteredBarrios[0];
    const target = exact?.barrio || fallback?.barrio;
    if (!target) {
      toast.error(t("cityReportUi.noBarrioMatches"));
      return;
    }
    selectBarrio(target);
  };

  const getSharePayload = async () => {
    if (!summary?.city) return null;
    const query = new URLSearchParams({ city: summary.city });
    if (summary.barrio) query.set("barrio", summary.barrio);
    const { data } = await axios.get(`${API}/city-reports/share?${query.toString()}`);
    return {
      title: data.title || formatTranslation(t, "cityReportUi.shareTitle", {
        location: summary.barrio
          ? formatTranslation(t, "cityReportUi.locationWithBarrio", { city: summary.city, barrio: summary.barrio })
          : summary.city,
      }),
      text: data.share_text || formatTranslation(t, "cityReportUi.shareText", {
        location: summary.barrio
          ? formatTranslation(t, "cityReportUi.locationWithBarrio", { city: summary.city, barrio: summary.barrio })
          : summary.city,
        fresh: summary.fresh_reports,
        older: summary.older_reports,
        fossils: summary.fossil_reports,
      }),
      url: data.app_url || `${HOSTED_WEB_URL}/download?kind=city-report&${query.toString()}`,
      imageUrl: data.image_url,
    };
  };

  const handleShare = async () => {
    if (!summary?.city) return;
    try {
      await shareWithNativeOrCopy({
        ...(await getSharePayload()),
        onCopied: () => toast.success(t("cityReportUi.copied")),
      });
    } catch (error) {
      if (error?.name !== "AbortError") {
        toast.error(t("cityReportUi.shareError"));
      }
    }
  };

  const summaryLine = summary ? formatTranslation(t, "cityReportUi.summaryLine", {
      location: summary.barrio
        ? formatTranslation(t, "cityReportUi.locationWithBarrio", { city: summary.city, barrio: summary.barrio })
        : summary.city,
      fresh: summary.fresh_reports,
      older: summary.older_reports,
      fossils: summary.fossil_reports,
    }) : "";

  if (!isPremium && !requestedCity) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col" data-testid="city-report-page">
        <div className="ios-safe-header p-4 flex justify-between items-center">
          <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]">
            <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
          </Button>
          <LanguageSelector />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <Lock className="w-12 h-12 text-[#8D99AE] mb-4" />
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">{t("cityReportUi.premiumTitle")}</h2>
          <p className="text-[#8D99AE] text-sm mb-6">{t("cityReportUi.premiumBody")}</p>
          <Button onClick={() => navigate("/subscribe")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-8 py-5">
            {t("cityReportUi.viewPremiumPlans")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="city-report-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-20">
        <div className="text-center mb-5">
          <Building2 className="w-10 h-10 text-[#FF6B6B] mx-auto mb-2" />
          <h1 className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>{t("cityReportUi.pageTitle")}</h1>
          <p className="text-sm text-[#8D99AE] mt-2">{t("cityReportUi.pageIntro")}</p>
        </div>

        {canUseSearch && (
          <div className="bg-white rounded-2xl border border-[#8D99AE]/10 shadow-sm p-4 mb-4 space-y-4">
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-[#8D99AE] absolute left-3 top-1/2 -translate-y-1/2" />
                <Input
                  value={searchValue}
                  onChange={(event) => setSearchValue(event.target.value)}
                  placeholder={t("cityReportUi.searchPlaceholder")}
                  className="pl-9 h-11 rounded-xl border-[#8D99AE]/20 bg-white"
                  data-testid="city-report-search"
                />
              </div>
              <Button type="submit" className="h-11 rounded-xl bg-[#FF6B6B] hover:bg-[#FF5252] text-white">
                {t("cityReportUi.searchAction")}
              </Button>
            </form>
            <p className="text-[11px] text-[#8D99AE] mt-2">{t("cityReportUi.searchHint")}</p>

            <div className="mt-3 space-y-2">
              {citiesLoading ? (
                <div className="flex items-center gap-2 text-sm text-[#8D99AE] py-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t("cityReportUi.loadingCities")}</span>
                </div>
              ) : filteredCities.length > 0 ? (
                filteredCities.map((option) => (
                  <button
                    key={option.city}
                    type="button"
                    onClick={() => selectCity(option.city)}
                    className="w-full flex items-center justify-between rounded-xl border border-[#8D99AE]/10 px-3 py-2.5 text-left hover:bg-[#F8F9FA]"
                    data-testid={`city-option-${option.city}`}
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-[#2B2D42] truncate">{option.city}</p>
                      {option.province && <p className="text-xs text-[#8D99AE] truncate">{option.province}</p>}
                    </div>
                    <span className="text-xs text-[#8D99AE] shrink-0">
                      {formatTranslation(t, "cityReportUi.activeCountShort", { count: option.active_reports })}
                    </span>
                  </button>
                ))
              ) : (
                <p className="text-sm text-[#8D99AE] py-2">{t("cityReportUi.noMatches")}</p>
              )}
            </div>

            {requestedCity && (
              <div className="pt-2 border-t border-[#8D99AE]/10">
                <form onSubmit={handleBarrioSubmit} className="flex gap-2">
                  <div className="relative flex-1">
                    <MapPin className="w-4 h-4 text-[#8D99AE] absolute left-3 top-1/2 -translate-y-1/2" />
                    <Input
                      value={barrioSearchValue}
                      onChange={(event) => setBarrioSearchValue(event.target.value)}
                      placeholder={t("cityReportUi.barrioSearchPlaceholder")}
                      className="pl-9 h-11 rounded-xl border-[#8D99AE]/20 bg-white"
                      data-testid="city-report-barrio-search"
                    />
                  </div>
                  <Button type="submit" variant="outline" className="h-11 rounded-xl border-[#8D99AE]/20">
                    {t("cityReportUi.barrioSearchAction")}
                  </Button>
                </form>
                <p className="text-[11px] text-[#8D99AE] mt-2">{t("cityReportUi.barrioSearchHint")}</p>

                <div className="mt-3 space-y-2">
                  {barriosLoading ? (
                    <div className="flex items-center gap-2 text-sm text-[#8D99AE] py-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{t("cityReportUi.loadingBarrios")}</span>
                    </div>
                  ) : filteredBarrios.length > 0 ? (
                    filteredBarrios.map((option) => (
                      <button
                        key={option.barrio}
                        type="button"
                        onClick={() => selectBarrio(option.barrio)}
                        className="w-full flex items-center justify-between rounded-xl border border-[#8D99AE]/10 px-3 py-2.5 text-left hover:bg-[#F8F9FA]"
                        data-testid={`barrio-option-${option.barrio}`}
                      >
                        <p className="font-semibold text-[#2B2D42] truncate">{option.barrio}</p>
                        <span className="text-xs text-[#8D99AE] shrink-0">
                          {formatTranslation(t, "cityReportUi.activeCountShort", { count: option.active_reports })}
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="text-sm text-[#8D99AE] py-2">{t("cityReportUi.noBarrioMatches")}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" /></div>
        ) : summary ? (
          <div className="space-y-4">
            <p className="text-center text-sm font-semibold text-[#5C677D] px-4">
              {t("shareUi.tagline")}
            </p>
            <div className="bg-white rounded-2xl border border-[#8D99AE]/10 shadow-sm p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-2xl font-black text-[#2B2D42] truncate">
                    {summary.barrio
                      ? formatTranslation(t, "cityReportUi.locationWithBarrio", { city: summary.city, barrio: summary.barrio })
                      : summary.city}
                  </h2>
                  {summary.province && <p className="text-sm text-[#8D99AE]">{summary.province}</p>}
                </div>
                <Button onClick={handleShare} variant="outline" className="rounded-xl border-[#FF6B6B]/30 text-[#FF6B6B] hover:bg-[#FF6B6B]/10 shrink-0" data-testid="share-city-report-btn">
                  <Share2 className="w-4 h-4 mr-2" />
                  {t("cityReportUi.shareButton")}
                </Button>
              </div>
              <SocialShareButtons
                className="mt-3"
                prefix="city-report-share"
                loadShareData={getSharePayload}
                onCopied={() => toast.success(t("cityReportUi.copied"))}
                onError={() => toast.error(t("cityReportUi.shareError"))}
              />

              <p className="mt-4 text-base font-semibold text-[#2B2D42] leading-7">
                {summaryLine}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <StatCard label={t("cityReportUi.totalActiveLabel")} value={summary.total_active_reports} color="#2B2D42" />
              <StatCard label={t("cityReportUi.freshLabel")} value={summary.fresh_reports} color="#FF5252" />
              <StatCard label={t("cityReportUi.olderLabel")} value={summary.older_reports} color="#FFA726" />
              <StatCard label={t("cityReportUi.fossilLabel")} value={summary.fossil_reports} color="#66BB6A" />
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2 text-[#2B2D42]">
                <MapPin className="w-4 h-4 text-[#FF6B6B]" />
                <h3 className="font-bold">
                  {summary.barrio ? t("cityReportUi.barrioMapTitle") : t("cityReportUi.mapTitle")}
                </h3>
              </div>
              <CityPreviewMap summary={summary} t={t} />
            </div>

            {!canUseSearch && (
              <div className="rounded-xl bg-white border border-[#8D99AE]/10 p-4 text-sm text-[#5C677D]">
                {t("cityReportUi.publicViewNote")}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-[#8D99AE]/10 shadow-sm p-6 text-center">
            <p className="text-[#8D99AE]">
              {requestedCity ? loadError || t("cityReportUi.emptyState") : t("cityReportUi.chooseCity")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
