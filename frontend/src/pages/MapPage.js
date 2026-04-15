import { useState, useEffect, useRef, useCallback } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import { toast } from "sonner";
import { MapPin, Plus, User, LogIn, X, Camera, Flag, ThumbsUp, ThumbsDown, Clock, CheckCircle, Loader2, Trophy, AlertTriangle, Shield, Star, Flame, LogOut, BarChart3, Building2, Layers, Share2, Bell, BellOff, Filter, Lock } from "lucide-react";
import { Button } from "../components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger
} from "../components/ui/dropdown-menu";
import {
  Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter, DrawerClose
} from "../components/ui/drawer";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import { HeatmapLayer } from "../components/HeatmapLayer";

const API = process.env.REACT_APP_BACKEND_URL + "/api";
const DEFAULT_CENTER = [40.4168, -3.7038];
const DEFAULT_ZOOM = 14;

function getMarkerCategory(createdAt) {
  const created = new Date(createdAt);
  const now = new Date();
  const hoursDiff = (now - created) / (1000 * 60 * 60);
  if (hoursDiff < 48) return "recent";
  if (hoursDiff < 144) return "moderate";
  return "old";
}

function createMarkerIcon(category, isPremium) {
  const colors = { recent: "#FF5252", moderate: "#FFA726", old: "#66BB6A" };
  const color = colors[category];
  const pulseClass = category === "recent" ? "marker-recent" : "";
  const border = isPremium ? "border: 3px solid #FFD700;" : "border: 3px solid white;";
  return L.divIcon({
    className: "custom-marker-wrapper",
    html: `<div class="custom-marker ${pulseClass}" style="width:32px;height:32px;background-color:${color};${border}"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="3"/></svg></div>`,
    iconSize: [32, 32], iconAnchor: [16, 16]
  });
}

function MapMarkers({ reports, onMarkerClick }) {
  const map = useMap();
  const markersRef = useRef([]);
  useEffect(() => {
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];
    reports.forEach(report => {
      const icon = createMarkerIcon(getMarkerCategory(report.created_at), report.is_premium_report);
      const marker = L.marker([report.latitude, report.longitude], { icon }).addTo(map).on("click", () => onMarkerClick(report));
      markersRef.current.push(marker);
    });
    return () => { markersRef.current.forEach(m => map.removeLayer(m)); };
  }, [reports, map, onMarkerClick]);
  return null;
}

function LocationFinder({ onLocationFound, allowMapClick, t }) {
  const map = useMapEvents({
    locationfound(e) { map.flyTo(e.latlng, 16); onLocationFound(e.latlng); },
    locationerror() { toast.error(t("locationError")); },
    click(e) { if (allowMapClick) { onLocationFound(e.latlng); toast.success(t("locationSelected")); } }
  });
  useEffect(() => { map.locate({ enableHighAccuracy: true }); }, [map]);
  return null;
}

const FLAG_REASON_KEYS = ["licensePlate", "face", "name", "personalInfo", "inappropriate", "spam", "other"];
const FLAG_REASON_VALUES = ["license_plate", "face", "name", "personal_info", "inappropriate", "spam", "other"];

export default function MapPage() {
  const { user, logout } = useAuth();
  const { t, tTime, isRtl } = useLanguage();
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [showReportDrawer, setShowReportDrawer] = useState(false);
  const [showDetailsDrawer, setShowDetailsDrawer] = useState(false);
  const [showFlagDrawer, setShowFlagDrawer] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [myVote, setMyVote] = useState(null);
  const [selectedFlagReason, setSelectedFlagReason] = useState(null);
  const [myValidation, setMyValidation] = useState(null);
  const [description, setDescription] = useState("");
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);
  const [activeFilter, setActiveFilter] = useState(null); // null | "Fresca" | "En proceso" | "Fósil" | "verified"
  const [showFilterBar, setShowFilterBar] = useState(false);
  const fileInputRef = useRef(null);

  // Check push notification status
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'granted') {
      setPushEnabled(true);
    }
  }, []);

  const fetchReports = async () => {
    try {
      let url = `${API}/reports`;
      const params = [];
      if (activeFilter === "Fresca" || activeFilter === "En proceso" || activeFilter === "Fósil") {
        params.push(`freshness=${encodeURIComponent(activeFilter)}`);
      } else if (activeFilter === "verified") {
        params.push("confirmed_only=true");
      }
      if (params.length) url += "?" + params.join("&");
      const { data } = await axios.get(url, { withCredentials: true });
      setReports(data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchReports(); }, [activeFilter]);

  const handleMarkerClick = useCallback(async (report) => {
    setSelectedReport(report);
    setShowDetailsDrawer(true);
    try {
      const [detailRes, voteRes, valRes] = await Promise.all([
        axios.get(`${API}/reports/${report.id}`, { withCredentials: true }),
        axios.get(`${API}/reports/${report.id}/my-vote`, { withCredentials: true }),
        axios.get(`${API}/reports/${report.id}/my-validation`, { withCredentials: true })
      ]);
      setSelectedReport(detailRes.data);
      setMyVote(voteRes.data.vote?.vote_type || null);
      setMyValidation(valRes.data.validation?.vote || null);
    } catch {
      setMyVote(null);
      setMyValidation(null);
    }
  }, []);

  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { toast.error(t("fileTooLarge")); return; }
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmitReport = async () => {
    if (!user) { toast.error("Regístrate gratis para reportar"); navigate("/register"); return; }
    if (!userLocation) { toast.error(t("locationError")); return; }
    setLoading(true);
    try {
      const { data: report } = await axios.post(`${API}/reports`, { latitude: userLocation.lat, longitude: userLocation.lng, description: description || null }, { withCredentials: true });
      if (photoFile) {
        const formData = new FormData();
        formData.append("file", photoFile);
        await axios.post(`${API}/reports/${report.id}/photo`, formData, { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } });
      }
      toast.success(t("reportSuccess"));
      setShowReportDrawer(false);
      setPhotoFile(null);
      setPhotoPreview(null);
      setDescription("");
      fetchReports();
    } catch (error) { toast.error(error.response?.data?.detail || t("reportError")); }
    finally { setLoading(false); }
  };

  const handleVote = async (voteType) => {
    if (!user) { toast.error("Regístrate gratis para votar"); navigate("/register"); return; }
    if (!selectedReport) return;
    setLoading(true);
    try {
      await axios.post(`${API}/reports/${selectedReport.id}/vote`, { vote_type: voteType }, { withCredentials: true });
      setMyVote(voteType);
      toast.success(voteType === "still_there" ? t("voteSuccess.stillThere") : t("voteSuccess.cleaned"));
      fetchReports();
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) { toast.error(error.response?.data?.detail || t("voteError")); }
    finally { setLoading(false); }
  };

  const handleFlag = async () => {
    if (!selectedReport || !selectedFlagReason) return;
    setLoading(true);
    try {
      await axios.post(`${API}/reports/${selectedReport.id}/flag`, { reason: selectedFlagReason }, { withCredentials: true });
      toast.success(t("flagSuccess"));
      setShowFlagDrawer(false);
      setShowDetailsDrawer(false);
      setSelectedFlagReason(null);
    } catch (error) { toast.error(error.response?.data?.detail || t("flagError")); }
    finally { setLoading(false); }
  };

  const handleValidation = async (vote) => {
    if (!user) { toast.error("Regístrate gratis para validar"); navigate("/register"); return; }
    if (!selectedReport) return;
    setLoading(true);
    try {
      await axios.post(`${API}/reports/${selectedReport.id}/validate`, { vote }, { withCredentials: true });
      setMyValidation(vote);
      toast.success(vote === "confirm" ? "Confirmado" : "Rechazado");
      fetchReports();
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) { toast.error(error.response?.data?.detail || "Error al validar"); }
    finally { setLoading(false); }
  };

  const handleReportVote = async (voteType) => {
    if (!selectedReport) return;
    try {
      const endpoint = voteType === "upvote" ? "upvote" : "downvote";
      await axios.post(`${API}/reports/${selectedReport.id}/${endpoint}`, {}, { withCredentials: true });
      toast.success(voteType === "upvote" ? "+1" : "-1");
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) { toast.error(error.response?.data?.detail || "Error"); }
  };

  const handleShare = async () => {
    if (!selectedReport) return;
    try {
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}/share`, { withCredentials: true });
      if (navigator.share) {
        await navigator.share({ title: data.title, text: data.text, url: data.url });
      } else {
        await navigator.clipboard.writeText(data.url);
        toast.success("Enlace copiado al portapapeles");
      }
    } catch (err) {
      if (err.name !== "AbortError") toast.error("Error al compartir");
    }
  };

  const togglePush = async () => {
    if (!user?.subscription_active) { navigate("/subscribe"); return; }
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      toast.error("Tu navegador no soporta notificaciones push");
      return;
    }
    if (pushEnabled) {
      await axios.post(`${API}/push/unsubscribe`, {}, { withCredentials: true });
      setPushEnabled(false);
      toast.success("Notificaciones desactivadas");
      return;
    }
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') { toast.error("Permiso de notificaciones denegado"); return; }
      const { data: vapidData } = await axios.get(`${API}/push/vapid-key`);
      const reg = await navigator.serviceWorker.ready;
      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidData.vapid_public_key
      });
      await axios.post(`${API}/push/subscribe`, {
        subscription: subscription.toJSON(),
        latitude: userLocation?.lat,
        longitude: userLocation?.lng
      }, { withCredentials: true });
      setPushEnabled(true);
      toast.success("Notificaciones activadas para reportes cercanos");
    } catch (err) { toast.error("Error activando notificaciones"); }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    if (diffHours < 1) return t("lessThanHour");
    if (diffHours < 24) return tTime(diffHours === 1 ? "hoursAgo" : "hoursAgoPlural", diffHours);
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return tTime(diffDays === 1 ? "daysAgo" : "daysAgoPlural", diffDays);
    return date.toLocaleDateString();
  };

  return (
    <div className={`h-full w-full relative ${isRtl ? 'rtl' : 'ltr'}`} data-testid="map-page">
      <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} className="h-full w-full" zoomControl={false}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <LocationFinder onLocationFound={setUserLocation} allowMapClick={true} t={t} />
        <MapMarkers reports={reports} onMarkerClick={handleMarkerClick} />
        {showHeatmap && <HeatmapLayer reports={reports} visible={showHeatmap} />}
      </MapContainer>

      {/* Header */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex justify-between items-center">
        <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg px-4 py-2 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-[#FF6B6B]" />
          <span className="font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("appName")}</span>
        </div>
        <div className="flex gap-2">
          <LanguageSelector />
          {user?.subscription_active && (
            <Button variant="outline" size="sm" onClick={togglePush} className={`backdrop-blur-sm shadow-lg border-0 ${pushEnabled ? 'bg-[#FF6B6B] text-white' : 'bg-white/95'}`} data-testid="push-toggle">
              {pushEnabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
            </Button>
          )}
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="bg-white/95 backdrop-blur-sm shadow-lg border-0 gap-1.5" data-testid="user-menu-btn">
                  <User className="w-4 h-4" />
                  <span className="hidden sm:inline text-xs max-w-[80px] truncate">{user.username || user.name || "Usuario"}</span>
                  {user.total_score > 0 && <span className="text-xs text-[#FF6B6B] font-bold">{user.total_score}</span>}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-3 py-2">
                  <p className="font-bold text-[#2B2D42] text-sm">{user.username || user.name}</p>
                  <p className="text-xs text-[#FF6B6B] font-medium">{user.rank || "Aspirante Cagón"}</p>
                  <div className="flex gap-3 mt-1 text-xs text-[#8D99AE]">
                    <span>{user.total_score || 0} pts</span>
                    <span className="flex items-center gap-0.5"><Flame className="w-3 h-3 text-orange-500" />{user.streak_days || 0}d</span>
                    <span className="flex items-center gap-0.5"><Shield className="w-3 h-3" />{user.trust_score || 50}</span>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer" data-testid="menu-profile">
                  <User className="w-4 h-4 mr-2" />Mi Perfil
                </DropdownMenuItem>
                {user.subscription_active && (
                  <DropdownMenuItem onClick={() => navigate("/leaderboard")} className="cursor-pointer" data-testid="menu-leaderboard">
                    <Trophy className="w-4 h-4 mr-2 text-[#FF6B6B]" />Leaderboard
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => navigate("/rankings")} className="cursor-pointer" data-testid="menu-rankings">
                  <BarChart3 className="w-4 h-4 mr-2 text-[#FF6B6B]" />Rankings
                </DropdownMenuItem>
                {!user.subscription_active && (
                  <DropdownMenuItem onClick={() => navigate("/subscribe")} className="cursor-pointer" data-testid="menu-subscribe">
                    <Star className="w-4 h-4 mr-2 text-[#FF6B6B]" />Premium
                  </DropdownMenuItem>
                )}
                {(user.role === "municipality" || user.role === "admin") && (
                  <DropdownMenuItem onClick={() => navigate("/dashboard")} className="cursor-pointer" data-testid="menu-dashboard">
                    <Building2 className="w-4 h-4 mr-2" />Dashboard
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-500" data-testid="menu-logout">
                  <LogOut className="w-4 h-4 mr-2" />Salir
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="outline" size="sm" onClick={() => navigate("/login")} className="bg-white/95 backdrop-blur-sm shadow-lg border-0" data-testid="login-btn">
              <LogIn className="w-4 h-4 mr-1" />{t("enter")}
            </Button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      {showFilterBar && (
        <div className="absolute top-16 left-4 right-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-3">
          <div className="flex gap-2 flex-wrap">
            {[null, "Fresca", "En proceso", "Fósil", "verified"].map((f) => (
              <button key={f || "all"} onClick={() => { setActiveFilter(f); if (!user?.subscription_active && f) { navigate("/subscribe"); return; } }}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${activeFilter === f ? 'bg-[#FF6B6B] text-white' : 'bg-[#F8F9FA] text-[#8D99AE] hover:bg-[#FF6B6B]/10'}`}
                data-testid={`filter-${f || 'all'}`}>
                {f === null ? "Todos" : f === "verified" ? "Verificados" : f}
                {f && !user?.subscription_active && <Lock className="w-3 h-3 ml-1 inline" />}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Heatmap toggle - subscriber only */}
      {user?.subscription_active && !showReportDrawer && !showDetailsDrawer && !showFlagDrawer && (
        <div className="absolute bottom-28 right-4 z-[999] flex flex-col gap-2">
          <button onClick={() => setShowHeatmap(!showHeatmap)} className={`p-3 rounded-xl shadow-lg transition-all ${showHeatmap ? 'bg-[#FF6B6B] text-white' : 'bg-white/95 backdrop-blur-sm text-[#8D99AE]'}`} data-testid="heatmap-toggle">
            <Layers className="w-5 h-5" />
          </button>
          <button onClick={() => setShowFilterBar(!showFilterBar)} className={`p-3 rounded-xl shadow-lg transition-all ${showFilterBar ? 'bg-[#FF6B6B] text-white' : 'bg-white/95 backdrop-blur-sm text-[#8D99AE]'}`} data-testid="filter-toggle">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Legend - hide when drawers open */}
      {!showReportDrawer && !showDetailsDrawer && !showFlagDrawer && (
        <div className="absolute bottom-28 left-4 z-[999] bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-3">
          <div className="flex flex-col gap-2 text-xs">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#FF5252]"></div><span className="text-[#2B2D42]">{t("legend.recent")}</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#FFA726]"></div><span className="text-[#2B2D42]">{t("legend.moderate")}</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#66BB6A]"></div><span className="text-[#2B2D42]">{t("legend.old")}</span></div>
          </div>
        </div>
      )}

      {/* FAB */}
      <button onClick={() => setShowReportDrawer(true)} className="fixed bottom-8 left-1/2 -translate-x-1/2 px-8 py-4 bg-[#FF6B6B] text-white rounded-full shadow-lg font-bold text-lg flex items-center gap-2 z-[1000] hover:bg-[#FF5252] hover:-translate-y-1 transition-all duration-200" style={{ fontFamily: 'Nunito, sans-serif' }} data-testid="report-btn">
        <Plus className="w-5 h-5" />{t("report")}
      </button>

      {/* Report Drawer */}
      <Drawer open={showReportDrawer} onOpenChange={setShowReportDrawer}>
        <DrawerContent className="rounded-t-3xl" data-testid="report-drawer">
          <DrawerHeader className="text-center">
            <DrawerTitle className="text-xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("reportTitle")}</DrawerTitle>
            <DrawerDescription className="text-[#8D99AE]">{t("reportDesc")}</DrawerDescription>
          </DrawerHeader>
          <div className="px-4 pb-4">
            <div className="flex items-center justify-center gap-2 p-4 bg-[#F8F9FA] rounded-xl mb-4">
              <MapPin className="w-5 h-5 text-[#FF6B6B]" />
              {userLocation ? <span className="text-sm text-[#2B2D42]">{userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}</span> : <span className="text-sm text-[#8D99AE]">{t("gettingLocation")}</span>}
            </div>

            {/* Content Policy Warning */}
            <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-xl mb-4">
              <Shield className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-amber-800 font-medium">{t("photoPolicy")}</p>
                <p className="text-xs text-amber-600 mt-1">{t("policyAgreement")}</p>
              </div>
            </div>

            <input type="file" accept="image/*" capture="environment" ref={fileInputRef} onChange={handlePhotoSelect} className="hidden" data-testid="photo-input" />

            {/* Description (optional) */}
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descripción opcional..."
              className="w-full p-3 border border-[#8D99AE]/20 rounded-xl text-sm resize-none bg-[#F8F9FA] text-[#2B2D42] placeholder-[#8D99AE] mb-4 focus:outline-none focus:border-[#FF6B6B]"
              rows={2}
              maxLength={200}
              data-testid="description-input"
            />
            {photoPreview ? (
              <div className="relative mb-4">
                <img src={photoPreview} alt="Preview" className="w-full h-48 object-cover rounded-xl" />
                <button onClick={() => { setPhotoFile(null); setPhotoPreview(null); }} className="absolute top-2 right-2 p-1 bg-black/50 rounded-full text-white"><X className="w-4 h-4" /></button>
              </div>
            ) : (
              <button onClick={() => fileInputRef.current?.click()} className="w-full p-8 border-2 border-dashed border-[#8D99AE]/30 rounded-xl flex flex-col items-center gap-2 text-[#8D99AE] hover:border-[#FF6B6B] hover:text-[#FF6B6B] transition-colors mb-4" data-testid="add-photo-btn">
                <Camera className="w-8 h-8" /><span>{t("addPhoto")}</span>
              </button>
            )}
          </div>
          <DrawerFooter className="pt-0">
            <Button onClick={handleSubmitReport} disabled={loading || !userLocation} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-6 rounded-xl text-lg font-bold" style={{ fontFamily: 'Nunito, sans-serif' }} data-testid="submit-report-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("submitReport")}
            </Button>
            <DrawerClose asChild><Button variant="ghost" className="text-[#8D99AE]">{t("cancel")}</Button></DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>

      {/* Details Drawer */}
      <Drawer open={showDetailsDrawer} onOpenChange={setShowDetailsDrawer}>
        <DrawerContent className="rounded-t-3xl" data-testid="details-drawer">
          <DrawerHeader>
            <DrawerTitle className="text-xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("detailsTitle")}</DrawerTitle>
          </DrawerHeader>
          {selectedReport && (
            <div className="px-4 pb-4">
              {selectedReport.photo_url && (
                <div className="mb-4 rounded-xl overflow-hidden">
                  <img src={`${API}/files/${selectedReport.photo_url}`} alt="Foto" className="w-full h-48 object-cover" data-testid="report-photo" />
                </div>
              )}
              {selectedReport.description && (
                <p className="text-sm text-[#2B2D42] mb-3 italic">"{selectedReport.description}"</p>
              )}
              {/* Contributor */}
              <div className="flex items-center gap-2 mb-3">
                <User className="w-4 h-4 text-[#8D99AE]" />
                <span className="text-sm text-[#2B2D42] font-medium">{selectedReport.contributor_name || "Anónimo"}</span>
                {selectedReport.contributor_rank && (
                  <span className="text-xs text-[#FF6B6B] bg-[#FF6B6B]/10 px-2 py-0.5 rounded-full">{selectedReport.contributor_rank}</span>
                )}
              </div>
              <div className="bg-[#F8F9FA] rounded-xl p-4 mb-4">
                <div className="flex items-center gap-2 text-[#8D99AE] mb-2">
                  <Clock className="w-4 h-4" /><span className="text-sm">{formatDate(selectedReport.created_at)}</span>
                  {selectedReport.municipality && <span className="text-xs bg-[#FF6B6B]/10 text-[#FF6B6B] px-2 py-0.5 rounded-full ml-auto">{selectedReport.municipality}</span>}
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${selectedReport.status === 'verified' ? 'bg-emerald-100 text-emerald-700' : selectedReport.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                    {selectedReport.status === 'verified' ? 'Verificado' : selectedReport.status === 'rejected' ? 'Rechazado' : 'Pendiente'}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${selectedReport.freshness === 'Fresca' ? 'bg-red-100 text-red-700' : selectedReport.freshness === 'En proceso' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}>
                    {selectedReport.freshness || "Fósil"}
                  </span>
                  {selectedReport.confidence !== undefined && (
                    <span className="text-xs text-[#8D99AE]">Confianza: {selectedReport.confidence}%</span>
                  )}
                  <span className="text-xs text-[#8D99AE]">{selectedReport.validation_count || 0} validaciones</span>
                </div>
                <div className="flex gap-4">
                  <div className="flex items-center gap-1"><ThumbsUp className="w-4 h-4 text-[#66BB6A]" /><span className="text-sm font-medium text-[#2B2D42]">{selectedReport.upvotes || 0}</span></div>
                  <div className="flex items-center gap-1"><ThumbsDown className="w-4 h-4 text-[#FF5252]" /><span className="text-sm font-medium text-[#2B2D42]">{selectedReport.downvotes || 0}</span></div>
                  <div className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-[#66BB6A]" /><span className="text-sm font-medium text-[#2B2D42]">{selectedReport.still_there_count || 0} {t("stillThereCount")}</span></div>
                </div>
              </div>

              {/* Upvote / Downvote */}
              <div className="flex gap-2 mb-4">
                <Button size="sm" variant="outline" onClick={() => handleReportVote("upvote")} className="flex-1 text-[#66BB6A] border-[#66BB6A]/30 hover:bg-[#66BB6A]/10" data-testid="upvote-btn">
                  <ThumbsUp className="w-4 h-4 mr-1" /> Útil
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleReportVote("downvote")} className="flex-1 text-[#FF5252] border-[#FF5252]/30 hover:bg-[#FF5252]/10" data-testid="downvote-btn">
                  <ThumbsDown className="w-4 h-4 mr-1" /> No útil
                </Button>
              </div>

              {/* Validation */}
              {!myValidation && selectedReport.status === 'pending' ? (
                <div className="flex gap-3 mb-4">
                  <Button onClick={() => handleValidation("confirm")} disabled={loading} className="flex-1 bg-[#66BB6A] hover:bg-[#4CAF50] text-white py-5 rounded-xl" data-testid="validate-confirm-btn">
                    <CheckCircle className="w-5 h-5 mr-2" /> Confirmar
                  </Button>
                  <Button onClick={() => handleValidation("reject")} disabled={loading} className="flex-1 bg-[#FF5252] hover:bg-[#E53935] text-white py-5 rounded-xl" data-testid="validate-reject-btn">
                    <X className="w-5 h-5 mr-2" /> Rechazar
                  </Button>
                </div>
              ) : myValidation ? (
                <div className="bg-[#F8F9FA] rounded-xl p-3 mb-4 text-center text-sm text-[#8D99AE]">
                  Tu validación: {myValidation === "confirm" ? "Confirmado" : "Rechazado"}
                </div>
              ) : null}

              {/* Still there / Cleaned (legacy) */}
              {!myVote ? (
                <div className="flex gap-3 mb-4">
                  <Button onClick={() => handleVote("still_there")} disabled={loading} className="flex-1 bg-[#FFA726] hover:bg-[#F57C00] text-white py-5 rounded-xl" data-testid="vote-still-there-btn"><ThumbsUp className="w-5 h-5 mr-2" />{t("stillThere")}</Button>
                  <Button onClick={() => handleVote("cleaned")} disabled={loading} className="flex-1 bg-[#66BB6A] hover:bg-[#4CAF50] text-white py-5 rounded-xl" data-testid="vote-cleaned-btn"><CheckCircle className="w-5 h-5 mr-2" />{t("cleaned")}</Button>
                </div>
              ) : (
                <div className="bg-[#F8F9FA] rounded-xl p-3 mb-4 text-center text-sm text-[#8D99AE]">{t("alreadyVoted")}: {myVote === "still_there" ? t("stillThere") : t("cleaned")}</div>
              )}

              <div className="flex gap-2 mb-2">
                <Button variant="ghost" onClick={handleShare} className="flex-1 text-[#42A5F5] hover:text-[#1E88E5]" data-testid="share-btn">
                  <Share2 className="w-4 h-4 mr-2" />Compartir
                </Button>
                <Button variant="ghost" onClick={() => { setShowFlagDrawer(true); setShowDetailsDrawer(false); }} className="flex-1 text-[#8D99AE] hover:text-[#FF5252]" data-testid="flag-report-btn">
                  <Flag className="w-4 h-4 mr-2" />{t("flagReport")}
                </Button>
              </div>
            </div>
          )}
          <DrawerFooter className="pt-0"><DrawerClose asChild><Button variant="ghost" className="text-[#8D99AE]">{t("close")}</Button></DrawerClose></DrawerFooter>
        </DrawerContent>
      </Drawer>

      {/* Flag Drawer */}
      <Drawer open={showFlagDrawer} onOpenChange={(open) => { setShowFlagDrawer(open); if (!open) setSelectedFlagReason(null); }}>
        <DrawerContent className="rounded-t-3xl" data-testid="flag-drawer">
          <DrawerHeader>
            <DrawerTitle className="text-xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("flagTitle")}</DrawerTitle>
            <DrawerDescription className="text-[#8D99AE]">{t("flagDescription")}</DrawerDescription>
          </DrawerHeader>
          <div className="px-4 pb-4 space-y-2">
            {FLAG_REASON_KEYS.map((key, i) => (
              <button key={key} onClick={() => setSelectedFlagReason(FLAG_REASON_VALUES[i])}
                className={`w-full text-left p-3 rounded-xl border-2 transition-all ${selectedFlagReason === FLAG_REASON_VALUES[i] ? 'border-[#FF6B6B] bg-[#FF6B6B]/5 text-[#FF6B6B]' : 'border-transparent bg-[#F8F9FA] text-[#2B2D42] hover:border-[#8D99AE]/30'}`}
                data-testid={`flag-reason-${FLAG_REASON_VALUES[i]}`}
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className={`w-4 h-4 ${selectedFlagReason === FLAG_REASON_VALUES[i] ? 'text-[#FF6B6B]' : 'text-[#8D99AE]'}`} />
                  <span className="text-sm font-medium">{t(`flagReasons.${key}`)}</span>
                </div>
              </button>
            ))}
          </div>
          <DrawerFooter className="pt-0">
            <Button onClick={handleFlag} disabled={loading || !selectedFlagReason} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold" data-testid="submit-flag-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("flagSubmit")}
            </Button>
            <DrawerClose asChild><Button variant="ghost" className="text-[#8D99AE]">{t("flagCancel")}</Button></DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </div>
  );
}
