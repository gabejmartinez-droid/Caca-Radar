import { useState, useEffect, useRef, useCallback } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import { toast } from "sonner";
import { MapPin, Plus, User, LogIn, X, Camera, Flag, ThumbsUp, ThumbsDown, Clock, CheckCircle, Loader2, Trophy, AlertTriangle, Shield, Star, Flame, LogOut, BarChart3, Building2, Layers, Share2, Bell, BellOff, Filter, Lock, ChevronDown, Crosshair, MessageSquare, Heart, Cookie, FileText } from "lucide-react";
import { Button } from "../components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger
} from "../components/ui/dropdown-menu";
import {
  Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter, DrawerClose
} from "../components/ui/drawer";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation, getRankLabel } from "../utils/ranks";
import { LanguageSelector } from "../components/LanguageSelector";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import { HeatmapLayer } from "../components/HeatmapLayer";
import { API } from "../config";
import FeedbackDrawer from "../components/FeedbackDrawer";
import ActivityBanner from "../components/ActivityBanner";
import PointsPopup from "../components/PointsPopup";
import StreakFlame from "../components/StreakFlame";
import { subscribeToPush, unsubscribeFromPush, isPushSupported, getPushUnavailableReasonKey } from "../utils/pushManager";
import { compressReportPhoto, REPORT_PHOTO_MAX_BYTES } from "../utils/reportPhoto";
import { isCapacitorNative } from "../tokenManager";
import { getCurrentPlatform, getVersionSummary } from "../versionInfo";
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
    html: `<div class="custom-marker ${pulseClass}" style="width:16px;height:16px;background-color:${color};${border}"><svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="3"/></svg></div>`,
    iconSize: [16, 16], iconAnchor: [8, 8]
  });
}

function MapMarkers({ reports, onMarkerClick }) {
  const map = useMap();
  const markersRef = useRef([]);
  useEffect(() => {
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];
    reports.forEach(report => {
      const icon = createMarkerIcon(getMarkerCategory(report.refreshed_at || report.created_at), report.is_premium_report);
      const marker = L.marker([report.latitude, report.longitude], { icon }).addTo(map).on("click", () => onMarkerClick(report));
      markersRef.current.push(marker);
    });
    return () => { markersRef.current.forEach(m => map.removeLayer(m)); };
  }, [reports, map, onMarkerClick]);
  return null;
}

function LocationFinder({ onLocationFound, mapRef }) {
  const map = useMapEvents({
    locationfound(e) {
      map.setView(e.latlng, 16, { animate: false });
      onLocationFound(e.latlng);
    },
    locationerror() { /* handled by caller */ },
  });
  useEffect(() => {
    mapRef.current = map;
    map.locate({
      enableHighAccuracy: false,
      maximumAge: 60000,
      timeout: 8000,
    });
  }, [map, mapRef]);
  return null;
}

const FLAG_REASON_KEYS = ["licensePlate", "face", "name", "personalInfo", "inappropriate", "spam", "other"];
const FLAG_REASON_VALUES = ["license_plate", "face", "name", "personal_info", "inappropriate", "spam", "other"];
const FRESHNESS_FILTERS = [
  { value: null, labelKey: "mapUi.filters.all" },
  { value: "Fresca", labelKey: "mapUi.filters.fresh" },
  { value: "En proceso", labelKey: "mapUi.filters.moderate" },
  { value: "Fósil", labelKey: "mapUi.filters.old" },
  { value: "verified", labelKey: "mapUi.filters.verified" },
];
const FRESHNESS_LABEL_KEYS = {
  "Fresca": "mapUi.filters.fresh",
  "En proceso": "mapUi.filters.moderate",
  "Fósil": "mapUi.filters.old",
};
const ACTION_PROXIMITY_METERS = 5;
const MAP_MODES = {
  REPORTS: "reports",
  HEATMAP: "heatmap",
};

function scheduleAfterFirstPaint(callback, delay = 0) {
  if (typeof window === "undefined") {
    callback();
    return () => {};
  }

  let timeoutId = null;
  let idleId = null;

  const run = () => {
    timeoutId = window.setTimeout(callback, delay);
  };

  if (typeof window.requestIdleCallback === "function") {
    idleId = window.requestIdleCallback(run, { timeout: 1500 });
  } else {
    run();
  }

  return () => {
    if (idleId !== null && typeof window.cancelIdleCallback === "function") {
      window.cancelIdleCallback(idleId);
    }
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  };
}

export default function MapPage() {
  const { user, logout } = useAuth();
  const { t, tTime, isRtl, language } = useLanguage();
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
  const [mapMode, setMapMode] = useState(MAP_MODES.REPORTS);
  const [pushEnabled, setPushEnabled] = useState(false);
  const [activeFilter, setActiveFilter] = useState(null); // null | "Fresca" | "En proceso" | "Fósil" | "verified"
  const [showFilterBar, setShowFilterBar] = useState(false);
  const [showMainMenu, setShowMainMenu] = useState(false);
  const [userCity, setUserCity] = useState(null);
  const [userBarrio, setUserBarrio] = useState(null);
  const [viewportWidth, setViewportWidth] = useState(() => (typeof window !== "undefined" ? window.innerWidth : 1024));
  const [viewportHeight, setViewportHeight] = useState(() => (typeof window !== "undefined" ? window.innerHeight : 768));
  const fileInputRef = useRef(null);
  const mapRef = useRef(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [pointsEarned, setPointsEarned] = useState(null);
  const [showNotifPrompt, setShowNotifPrompt] = useState(false);
  const [showAmbientUi, setShowAmbientUi] = useState(false);
  const [showMapSurface, setShowMapSurface] = useState(() => !isCapacitorNative());
  const [backendVersion, setBackendVersion] = useState("unknown");
  const tf = useCallback((key, values = {}) => formatTranslation(t, key, values), [t]);
  const freshnessLabel = (freshness) => t(FRESHNESS_LABEL_KEYS[freshness || "Fósil"] || "mapUi.filters.old");
  const statusLabel = (status) => t(`mapUi.status.${status || "pending"}`);
  const isHeatmapMode = mapMode === MAP_MODES.HEATMAP;
  const isNativeApp = isCapacitorNative();
  const currentPlatform = getCurrentPlatform();
  const versionSummary = getVersionSummary();
  const shouldHideMapControls = showMainMenu || showReportDrawer || showFlagDrawer;

  useEffect(() => {
    if (!isNativeApp) return undefined;

    let timeoutId = null;
    let idleId = null;
    let cancelled = false;

    const revealMap = () => {
      if (!cancelled) {
        setShowMapSurface(true);
      }
    };

    if (typeof window.requestIdleCallback === "function") {
      idleId = window.requestIdleCallback(revealMap, { timeout: 1800 });
    } else {
      timeoutId = window.setTimeout(revealMap, 350);
    }

    return () => {
      cancelled = true;
      if (idleId) window.cancelIdleCallback?.(idleId);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [isNativeApp]);

  const setHeatmapMode = useCallback((nextMode) => {
    if (nextMode === MAP_MODES.HEATMAP && !user?.subscription_active) {
      navigate("/subscribe");
      return;
    }
    setMapMode(nextMode);
  }, [navigate, user?.subscription_active]);

  // Re-center map on current GPS location
  const recenterMap = useCallback(() => {
    if (mapRef.current) {
      mapRef.current.locate({ enableHighAccuracy: true });
    }
  }, []);

  // Get fresh GPS position (returns a promise)
  const getFreshLocation = useCallback(() => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) { reject(new Error("No geolocation")); return; }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setUserLocation(loc);
          resolve(loc);
        },
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
      );
    });
  }, []);

  const getActionLocation = useCallback(async () => {
    try {
      return await getFreshLocation();
    } catch (error) {
      if (userLocation) {
        return userLocation;
      }
      throw error;
    }
  }, [getFreshLocation, userLocation]);

  const getActionErrorMessage = useCallback((error, fallbackKey) => {
    const detail = error?.response?.data?.detail;
    if (detail && typeof detail === "object") {
      if (detail.code === "outside_proximity") {
        return tf("mapUi.tooFarFromReport", {
          distance: Math.round(detail.distance_meters || 0),
          meters: detail.max_meters || ACTION_PROXIMITY_METERS,
        });
      }
      if (detail.code === "still_there_removed") {
        return t("mapUi.useValidationToConfirm");
      }
    }
    if (typeof detail === "string") {
      return detail;
    }
    return t(fallbackKey);
  }, [t, tf]);

  // Check push notification status from backend
  useEffect(() => {
    return scheduleAfterFirstPaint(() => setShowAmbientUi(true), 1400);
  }, []);

  useEffect(() => {
    if (!user) return;

    const checkPush = async () => {
      try {
        const { data } = await axios.get(`${API}/push/status`, { withCredentials: true });
        setPushEnabled(data.subscribed);
      } catch { /* ignore */ }
    };

    return scheduleAfterFirstPaint(checkPush, 1200);
  }, [user]);

  const fetchReports = useCallback(async () => {
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
      setReports(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); setReports([]); }
  }, [activeFilter]);

  useEffect(() => {
    if (!showMapSurface) return undefined;
    return scheduleAfterFirstPaint(fetchReports, 250);
  }, [fetchReports, showMapSurface]);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const { data } = await axios.get(`${API}/version`, { withCredentials: !isNativeApp });
        setBackendVersion(data.backend_version || "unknown");
      } catch {
        setBackendVersion("unknown");
      }
    };
    return scheduleAfterFirstPaint(fetchVersion, 600);
  }, [isNativeApp]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const handleResize = () => {
      setViewportWidth(window.innerWidth);
      setViewportHeight(window.innerHeight);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Detect user's city and barrio from location
  useEffect(() => {
    if (!userLocation) return;

    const detectArea = async () => {
      try {
        const resp = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${userLocation.lat}&lon=${userLocation.lng}&format=json&addressdetails=1&zoom=16`, { headers: { "User-Agent": "CacaRadar/1.0" } });
        const data = await resp.json();
        const addr = data.address || {};
        const city = addr.city || addr.town || addr.village || addr.municipality || "";
        const barrio = addr.suburb || addr.neighbourhood || addr.neighborhood || addr.quarter || addr.city_district || addr.borough || addr.hamlet || "";
        if (city) setUserCity(city);
        if (barrio) setUserBarrio(barrio);
      } catch (err) { console.error("Area detection failed:", err); }
    };

    return scheduleAfterFirstPaint(detectArea, 1800);
  }, [userLocation]);

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
    } catch (err) {
      console.error("Failed to load report details:", err);
      setMyVote(null);
      setMyValidation(null);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (photoPreview) {
        URL.revokeObjectURL(photoPreview);
      }
    };
  }, [photoPreview]);

  const clearSelectedPhoto = useCallback(() => {
    setPhotoFile(null);
    setPhotoPreview((currentPreview) => {
      if (currentPreview) {
        URL.revokeObjectURL(currentPreview);
      }
      return null;
    });
  }, []);

  const handlePhotoSelect = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) {
      return;
    }

    try {
      const compressedFile = await compressReportPhoto(file);
      clearSelectedPhoto();
      setPhotoFile(compressedFile);
      setPhotoPreview(URL.createObjectURL(compressedFile));
      if (compressedFile.size > REPORT_PHOTO_MAX_BYTES) {
        toast.message(t("mapUi.photoCompressedWarning"));
      }
    } catch (error) {
      console.error("Report photo compression failed:", error);
      clearSelectedPhoto();
      toast.error(t("mapUi.photoCompressionError"));
    }
  };

  const handleSubmitReport = useCallback(async () => {
    if (!user) { toast.error(t("mapUi.registerToReport")); navigate("/register"); return; }
    setLoading(true);
    try {
      // Always get fresh GPS for the report
      let loc;
      try {
        loc = await getFreshLocation();
      } catch {
        loc = userLocation;
      }
      if (!loc) { toast.error(t("locationError")); setLoading(false); return; }

      const { data: report } = await axios.post(`${API}/reports`, { latitude: loc.lat, longitude: loc.lng, description: description || null }, { withCredentials: true });
      if (photoFile) {
        const formData = new FormData();
        formData.append("file", photoFile);
        await axios.post(`${API}/reports/${report.id}/photo`, formData, { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } });
      }
      toast.success(report.converted_to_confirmation ? t("reportConfirmed") : t("reportSuccess"));
      if (report.points_earned) {
        setPointsEarned({ points: report.points_earned, breakdown: report.points_breakdown });
      }
      // Smart notification prompt — after first successful report
      if ("Notification" in window && Notification.permission === "default" && !localStorage.getItem("notif_prompted")) {
        setTimeout(() => setShowNotifPrompt(true), 2000);
      }
      setShowReportDrawer(false);
      clearSelectedPhoto();
      setDescription("");
      fetchReports();
    } catch (error) { toast.error(error.response?.data?.detail || t("reportError")); }
    finally { setLoading(false); }
  }, [user, navigate, getFreshLocation, userLocation, description, photoFile, fetchReports, t, clearSelectedPhoto]);

  const handleVote = async (voteType) => {
    if (!user) { toast.error(t("mapUi.registerToVote")); navigate("/register"); return; }
    if (!selectedReport) return;
    setLoading(true);
    try {
      const location = await getActionLocation();
      await axios.post(
        `${API}/reports/${selectedReport.id}/vote`,
        { vote_type: voteType, latitude: location.lat, longitude: location.lng },
        { withCredentials: true }
      );
      setMyVote(voteType);
      toast.success(t("mapUi.voteSuccess.noLongerHere"));
      fetchReports();
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) {
      if (!error?.response && !userLocation) {
        toast.error(tf("mapUi.locationRequiredForAction", { meters: ACTION_PROXIMITY_METERS }));
      } else {
        toast.error(getActionErrorMessage(error, "mapUi.voteError"));
      }
    }
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
    if (!user) { toast.error(t("mapUi.registerToValidate")); navigate("/register"); return; }
    if (!selectedReport) return;
    setLoading(true);
    try {
      const location = await getActionLocation();
      await axios.post(
        `${API}/reports/${selectedReport.id}/validate`,
        { vote, latitude: location.lat, longitude: location.lng },
        { withCredentials: true }
      );
      setMyValidation(vote);
      toast.success(vote === "confirm" ? t("mapUi.confirmed") : t("mapUi.rejected"));
      fetchReports();
      const { data } = await axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true });
      setSelectedReport(data);
    } catch (error) {
      if (!error?.response && !userLocation) {
        toast.error(tf("mapUi.locationRequiredForAction", { meters: ACTION_PROXIMITY_METERS }));
      } else {
        toast.error(getActionErrorMessage(error, "mapUi.validationError"));
      }
    }
    finally { setLoading(false); }
  };

  const handleReportVote = async (voteType) => {
    if (!selectedReport) return;
    try {
      if (voteType === "downvote") {
        const gonePrompt = language === "es" ? "¿Ya no está esta caca?" : "Is this mess already gone?";
        const shouldMarkGone = window.confirm(t("mapUi.downvoteGoneQuestion") === "mapUi.downvoteGoneQuestion" ? gonePrompt : t("mapUi.downvoteGoneQuestion"));
        if (shouldMarkGone) {
          await handleVote("cleaned");
          return;
        }
      }
      const endpoint = voteType === "upvote" ? "upvote" : "downvote";
      await axios.post(`${API}/reports/${selectedReport.id}/${endpoint}`, {}, { withCredentials: true });
      toast.success(voteType === "upvote" ? t("mapUi.voteSuccess.upvote") : t("mapUi.voteSuccess.downvote"));
      const [detailRes, valRes] = await Promise.all([
        axios.get(`${API}/reports/${selectedReport.id}`, { withCredentials: true }),
        axios.get(`${API}/reports/${selectedReport.id}/my-validation`, { withCredentials: true }),
      ]);
      const data = detailRes.data;
      setSelectedReport(data);
      setMyValidation(valRes.data.validation?.vote || null);
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
        toast.success(t("mapUi.linkCopied"));
      }
    } catch (err) {
      if (err.name !== "AbortError") toast.error(t("mapUi.shareError"));
    }
  };

  const togglePush = async () => {
    if (!user) { navigate("/login"); return; }
    const supported = await isPushSupported();
    if (!supported) {
      toast.error(t(getPushUnavailableReasonKey()));
      return;
    }
    if (pushEnabled) {
      const ok = await unsubscribeFromPush();
      if (ok) {
        setPushEnabled(false);
        toast.success(t("mapUi.pushDisabled"));
      }
      return;
    }
    try {
      await subscribeToPush(userLocation);
      setPushEnabled(true);
      toast.success(t("mapUi.pushEnabledNearby"));
    } catch (err) {
      if (err.message === "permission_denied") {
        toast.error(t("mapUi.pushPermissionDenied"));
      } else if (err.message === "native_push_disabled_for_build") {
        toast.error(t(getPushUnavailableReasonKey()));
      } else {
        toast.error(t("mapUi.pushError"));
      }
    }
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

  const locationLabel = (() => {
    if (isNativeApp) {
      return userBarrio || userCity || "";
    }
    if (userCity && userBarrio && userBarrio.toLowerCase() !== userCity.toLowerCase()) {
      return `${userCity} · ${userBarrio}`;
    }
    return userBarrio || userCity || "";
  })();

  const shouldShowLanguageLabel = (() => {
    if (viewportWidth < 420) return false;
    if (isNativeApp) {
      return viewportWidth >= 430 && locationLabel.length < 18;
    }
    if (viewportWidth < 720) return false;
    if (locationLabel.length > 24 && viewportWidth < 980) return false;
    return true;
  })();

  const shouldShowAppName = viewportWidth >= 640;
  const headerMenuMaxHeight = Math.max(
    280,
    viewportHeight - (viewportWidth < 640 ? 240 : 180)
  );
  const detailsCardBottomPx = user?.subscription_active ? 226 : 158;
  const detailsCardMaxHeightPx = (() => {
    if (viewportWidth < 768) {
      return Math.min(Math.max(Math.round(viewportHeight * 0.2), 176), 208);
    }
    return Math.min(Math.max(Math.round(viewportHeight * 0.17), 168), 200);
  })();

  const versionEntries = [
    { key: "web", label: "Web", value: versionSummary.web },
    { key: "ios", label: "iOS", value: versionSummary.ios },
    { key: "android", label: "Android", value: versionSummary.android },
    { key: "backend", label: "Backend", value: backendVersion || versionSummary.backend },
  ];

  return (
    <div className={`h-screen w-full relative overflow-hidden ${isRtl ? 'rtl' : 'ltr'}`} data-testid="map-page">
      {showMapSurface ? (
        <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} className="h-full w-full" zoomControl={false}>
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <LocationFinder onLocationFound={setUserLocation} mapRef={mapRef} />
          {mapMode === MAP_MODES.REPORTS && <MapMarkers reports={reports} onMarkerClick={handleMarkerClick} />}
          <HeatmapLayer reports={reports} visible={isHeatmapMode} />
        </MapContainer>
      ) : (
        <div className="h-full w-full bg-[#F8F9FA]">
          <div className="h-full w-full opacity-70" style={{
            backgroundImage: "radial-gradient(circle at 20% 20%, rgba(255,107,107,0.08), transparent 28%), radial-gradient(circle at 80% 30%, rgba(66,165,245,0.08), transparent 24%), linear-gradient(135deg, #f8f9fa 0%, #eef2f7 100%)",
          }} />
        </div>
      )}

      {/* Header */}
      <div
        className="absolute left-4 right-4 z-[1100]"
        style={{ top: "calc(env(safe-area-inset-top, 0px) + 12px)" }}
      >
        <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg px-3 py-2 flex items-center gap-2 min-h-[56px]">
          <DropdownMenu open={showMainMenu} onOpenChange={setShowMainMenu}>
            <DropdownMenuTrigger asChild>
              <button className="min-w-0 flex-1 flex items-center gap-2 hover:opacity-90 transition-opacity" data-testid="app-menu-btn">
                <img src="/icon-32x32.png" alt="Caca Radar" className="w-8 h-8 rounded-lg shrink-0" />
                <div className="min-w-0 flex-1 text-left">
                  <div className="flex items-center gap-2 min-w-0">
                    {shouldShowAppName && (
                      <span className="font-bold text-[#2B2D42] truncate" style={{ fontFamily: 'Nunito, sans-serif' }}>
                        {t("appName")}
                      </span>
                    )}
                    {locationLabel && (
                      <span className="text-[11px] font-medium text-[#8D99AE] truncate">
                        {locationLabel}
                      </span>
                    )}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-[#8D99AE] shrink-0" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="start"
              className="w-[min(19rem,calc(100vw-2rem))] rounded-xl shadow-xl p-1 overflow-y-auto"
              style={{ maxHeight: `${headerMenuMaxHeight}px` }}
            >
              {(userCity || userBarrio) && (
                <>
                  <div className="px-3 py-2 flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-[#FF6B6B]" />
                    <span className="text-sm font-bold text-[#2B2D42]">{locationLabel}</span>
                  </div>
                  <DropdownMenuSeparator />
                </>
              )}
              <DropdownMenuItem
                onClick={() => user?.subscription_active ? navigate("/rankings") : navigate("/subscribe")}
                className="cursor-pointer gap-2"
                data-testid="menu-city-rankings"
              >
                <Building2 className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("cityRankings")}</span>
                {!user?.subscription_active && <Lock className="w-3.5 h-3.5 text-[#8D99AE]" />}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => user?.subscription_active ? navigate(`/rankings?tab=barrios&city=${encodeURIComponent(userCity || "Madrid")}`) : navigate("/subscribe")}
                className="cursor-pointer gap-2"
                data-testid="menu-barrio-rankings"
              >
                <MapPin className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("barrioRankings")}</span>
                {!user?.subscription_active && <Lock className="w-3.5 h-3.5 text-[#8D99AE]" />}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => user?.subscription_active ? navigate(`/city-report${userCity ? `?city=${encodeURIComponent(userCity)}` : ""}`) : navigate("/subscribe")}
                className="cursor-pointer gap-2"
                data-testid="menu-city-report"
              >
                <BarChart3 className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("cityReportUi.menuLabel")}</span>
                {!user?.subscription_active && <Lock className="w-3.5 h-3.5 text-[#8D99AE]" />}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setHeatmapMode(isHeatmapMode ? MAP_MODES.REPORTS : MAP_MODES.HEATMAP);
                }}
                className="cursor-pointer gap-2"
                data-testid="menu-heatmap"
              >
                <Flame className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("heatmap")}</span>
                {user?.subscription_active && isHeatmapMode && <CheckCircle className="w-3.5 h-3.5 text-[#66BB6A]" />}
                {!user?.subscription_active && <Lock className="w-3.5 h-3.5 text-[#8D99AE]" />}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  if (user?.subscription_active) { setShowFilterBar(f => !f); }
                  else { navigate("/subscribe"); }
                }}
                className="cursor-pointer gap-2"
                data-testid="menu-filters"
              >
                <Filter className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("advancedFilters")}</span>
                {!user?.subscription_active && <Lock className="w-3.5 h-3.5 text-[#8D99AE]" />}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/subscribe")} className="cursor-pointer gap-2" data-testid="menu-premium-link">
                <Star className="w-4 h-4 text-amber-500" />
                <span className="flex-1 font-bold text-amber-600">{t("goPremium")}</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setShowFeedback(true)} className="cursor-pointer gap-2" data-testid="menu-feedback">
                <MessageSquare className="w-4 h-4 text-[#8D99AE]" />
                <span className="flex-1">{t("mapUi.feedback")}</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/help")} className="cursor-pointer gap-2" data-testid="menu-help">
                <Heart className="w-4 h-4 text-[#42A5F5]" />
                <span className="flex-1">{t("legalUi.help")}</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/terms")} className="cursor-pointer gap-2" data-testid="menu-terms">
                <FileText className="w-4 h-4 text-[#FFA726]" />
                <span className="flex-1">{t("legalUi.termsOfUse")}</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/privacy")} className="cursor-pointer gap-2" data-testid="menu-privacy">
                <Shield className="w-4 h-4 text-[#66BB6A]" />
                <span className="flex-1">{t("legalUi.privacyPolicy")}</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/cookies")} className="cursor-pointer gap-2" data-testid="menu-cookies">
                <Cookie className="w-4 h-4 text-[#42A5F5]" />
                <span className="flex-1">{t("legalUi.cookiesPolicy")}</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/community")} className="cursor-pointer gap-2" data-testid="menu-community">
                <Flag className="w-4 h-4 text-[#FF6B6B]" />
                <span className="flex-1">{t("legalUi.communityGuidelines")}</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <div className="px-3 py-2 rounded-lg bg-[#F8F9FA] text-[11px] leading-5 text-[#5C677D]">
                {t("legalUi.mainMenuAdvisory")}
              </div>
              <DropdownMenuSeparator />
              <div className="px-3 py-2 space-y-1" data-testid="menu-versions">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-[#8D99AE]">{t("legalUi.versions")}</div>
                {versionEntries.map((entry) => (
                  <div key={entry.key} className={`flex items-center justify-between gap-3 text-xs ${entry.key === currentPlatform ? "text-[#2B2D42] font-semibold" : "text-[#8D99AE]"}`}>
                    <span className="shrink-0">{entry.label}</span>
                    <span className="max-w-[9rem] truncate text-right">{entry.value}</span>
                  </div>
                ))}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex items-center gap-1 shrink-0">
            <LanguageSelector showLabel={shouldShowLanguageLabel} />
            {user && (
              <Button
                variant="outline"
                size="sm"
                onClick={togglePush}
                className={`h-10 w-10 p-0 backdrop-blur-sm shadow-none border-0 ${pushEnabled ? 'bg-[#FF6B6B] text-white' : 'bg-transparent text-[#2B2D42]'}`}
                data-testid="push-toggle"
              >
                {pushEnabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
              </Button>
            )}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="h-10 px-3 bg-transparent shadow-none border-0 gap-2" data-testid="user-menu-btn">
                    <User className="w-4 h-4" />
                    {user.total_score > 0 && <span className="text-xs text-[#FF6B6B] font-bold hidden sm:inline">{user.total_score}</span>}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-[min(14rem,calc(100vw-2rem))] overflow-y-auto"
                  style={{ maxHeight: `${headerMenuMaxHeight}px` }}
                >
                  <div className="px-3 py-2">
                    <p className="font-bold text-[#2B2D42] text-sm">{user.username || user.name}</p>
                    <p className="text-xs text-[#FF6B6B] font-medium leading-tight">{getRankLabel(user.rank_key || user.rank, t)}</p>
                    <div className="flex gap-3 mt-1 text-xs text-[#8D99AE]">
                      <span>{user.total_score || 0} {t("mapUi.pointsShort")}</span>
                      <span className="flex items-center gap-0.5"><Flame className="w-3 h-3 text-orange-500" />{user.streak_days || 0}{t("mapUi.dayShort")}</span>
                      <span className="flex items-center gap-0.5"><Shield className="w-3 h-3" />{user.trust_score || 50}</span>
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer" data-testid="menu-profile">
                    <User className="w-4 h-4 mr-2" />{t("mapUi.myProfile")}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/impact")} className="cursor-pointer" data-testid="menu-impact">
                    <Heart className="w-4 h-4 mr-2 text-[#66BB6A]" />{t("mapUi.myImpact")}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/help")} className="cursor-pointer" data-testid="menu-user-help">
                    <MessageSquare className="w-4 h-4 mr-2 text-[#42A5F5]" />{t("legalUi.help")}
                  </DropdownMenuItem>
                  {user.subscription_active && (
                    <DropdownMenuItem onClick={() => navigate("/leaderboard")} className="cursor-pointer" data-testid="menu-leaderboard">
                      <Trophy className="w-4 h-4 mr-2 text-[#FF6B6B]" />{t("rankingUi.leaderboardTitle")}
                    </DropdownMenuItem>
                  )}
                  {!user.subscription_active && (
                    <DropdownMenuItem onClick={() => navigate("/subscribe")} className="cursor-pointer" data-testid="menu-subscribe">
                      <Star className="w-4 h-4 mr-2 text-[#FF6B6B]" />{t("goPremium")}
                    </DropdownMenuItem>
                  )}
                  {(user.role === "municipality" || user.role === "admin") && (
                    <DropdownMenuItem onClick={() => navigate("/dashboard")} className="cursor-pointer" data-testid="menu-dashboard">
                      <Building2 className="w-4 h-4 mr-2" />{t("municipalityUi.dashboardLabel")}
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-500" data-testid="menu-logout">
                    <LogOut className="w-4 h-4 mr-2" />{t("logout")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button variant="outline" size="sm" onClick={() => navigate("/login")} className="h-10 px-3 bg-transparent shadow-none border-0" data-testid="login-btn">
                <LogIn className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {showMainMenu && (
        <button
          type="button"
          className="fixed inset-0 z-[1050] bg-transparent cursor-default"
          onClick={() => setShowMainMenu(false)}
          aria-label="Close main menu"
        />
      )}

      {/* Filter Bar */}
      {showFilterBar && !showMainMenu && (
        <div className="absolute left-4 right-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-3" style={{ top: "calc(env(safe-area-inset-top, 0px) + 88px)" }}>
          <div className="flex gap-2 flex-wrap">
            {FRESHNESS_FILTERS.map(({ value, labelKey }) => (
              <button key={value || "all"} onClick={() => { setActiveFilter(value); if (!user?.subscription_active && value) { navigate("/subscribe"); return; } }}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${activeFilter === value ? 'bg-[#FF6B6B] text-white' : 'bg-[#F8F9FA] text-[#8D99AE] hover:bg-[#FF6B6B]/10'}`}
                data-testid={`filter-${value || 'all'}`}>
                {t(labelKey)}
                {value && !user?.subscription_active && <Lock className="w-3 h-3 ml-1 inline" />}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Legend - hide when drawers open */}
      {!shouldHideMapControls && (
        <div
          className="fixed left-1/2 -translate-x-1/2 z-[999] bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg px-3 py-2"
          style={{ bottom: "calc(env(safe-area-inset-bottom, 0px) + 4px)" }}
        >
          {isHeatmapMode ? (
            <div className="flex items-center gap-3 text-xs min-w-[210px]">
              <span className="font-semibold text-[#2B2D42]">{t("heatmap")}</span>
              <div className="h-2 flex-1 rounded-full bg-gradient-to-r from-transparent via-[#42A5F5] via-[#66BB6A] via-[#FFA726] to-[#FF5252]" />
              <div className="flex items-center gap-2 text-[#8D99AE] shrink-0">
                <span>0</span>
                <span>1</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-xs whitespace-nowrap">
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-[#FF5252]"></div><span className="text-[#2B2D42]">{t("legend.recent")}</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-[#FFA726]"></div><span className="text-[#2B2D42]">{t("legend.moderate")}</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-[#66BB6A]"></div><span className="text-[#2B2D42]">{t("legend.old")}</span></div>
            </div>
          )}
        </div>
      )}

      {/* Activity Banner */}
      {showAmbientUi && !showMainMenu && <ActivityBanner userLocation={userLocation} userCity={userCity} />}

      {/* Streak Flame Animation */}
      {showAmbientUi && !showMainMenu && <StreakFlame />}

      {/* Lower-right map controls */}
      <div
        className="fixed right-4 z-[1000] flex flex-col items-end gap-3"
        style={{ bottom: "calc(env(safe-area-inset-bottom, 0px) + 150px)" }}
      >
        {user?.subscription_active && !shouldHideMapControls && (
          <>
            <button
              onClick={() => setShowFilterBar(!showFilterBar)}
              className={`w-12 h-12 rounded-2xl shadow-lg flex items-center justify-center transition-all ${showFilterBar ? 'bg-[#FF6B6B] text-white' : 'bg-white/95 backdrop-blur-sm text-[#8D99AE]'}`}
              data-testid="filter-toggle"
              title={t("advancedFilters")}
            >
              <Filter className="w-5 h-5" />
            </button>
          </>
        )}

        {!shouldHideMapControls && (
          <button
            onClick={recenterMap}
            className="w-12 h-12 bg-white shadow-lg rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors"
            data-testid="recenter-btn"
            title={t("mapUi.recenterMap")}
          >
            <Crosshair className="w-5 h-5 text-[#2B2D42]" />
          </button>
        )}
      </div>

      {!shouldHideMapControls && (
        <button
          onClick={() => setShowReportDrawer(true)}
          className="fixed left-1/2 -translate-x-1/2 px-8 py-4 bg-[#FF6B6B] text-white rounded-full shadow-lg font-bold text-lg flex items-center gap-2 z-[1000] hover:bg-[#FF5252] hover:-translate-y-1 transition-all duration-200"
          style={{ fontFamily: 'Nunito, sans-serif', bottom: "calc(env(safe-area-inset-bottom, 0px) + 88px)" }}
          data-testid="report-btn"
        >
          <Plus className="w-5 h-5" />{t("report")}
        </button>
      )}

      {user?.subscription_active && !shouldHideMapControls && (
        <div
          className="fixed left-1/2 -translate-x-1/2 z-[1000] bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg p-1 flex items-center gap-1"
          style={{ bottom: "calc(env(safe-area-inset-bottom, 0px) + 28px)" }}
        >
          <button
            onClick={() => setHeatmapMode(MAP_MODES.REPORTS)}
            className={`min-w-[88px] h-11 px-3 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition-all ${mapMode === MAP_MODES.REPORTS ? 'bg-[#2B2D42] text-white shadow-sm' : 'text-[#8D99AE]'}`}
            data-testid="reports-mode-toggle"
            title={t("profileUi.reports")}
          >
            <MapPin className="w-4 h-4" />
            <span className="truncate">{t("profileUi.reports")}</span>
          </button>
          <button
            onClick={() => setHeatmapMode(MAP_MODES.HEATMAP)}
            className={`min-w-[104px] h-11 px-3 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition-all ${isHeatmapMode ? 'bg-[#FF6B6B] text-white shadow-sm' : 'text-[#8D99AE]'}`}
            data-testid="heatmap-toggle"
            title={t("heatmap")}
          >
            <Layers className="w-4 h-4" />
            <span className="truncate">{t("heatmap")}</span>
          </button>
        </div>
      )}

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
                <p className="text-xs text-amber-700 mt-2">
                  No subas datos personales innecesarios de terceros. Evita rostros identificables, menores, matrículas u otra información personal salvo que sea estrictamente necesario y lícito.
                </p>
              </div>
            </div>

            <input type="file" accept="image/*" capture="environment" ref={fileInputRef} onChange={handlePhotoSelect} className="hidden" data-testid="photo-input" />

            {/* Description (optional) */}
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t("mapUi.descriptionPlaceholder")}
              className="w-full p-3 border border-[#8D99AE]/20 rounded-xl text-sm resize-none bg-[#F8F9FA] text-[#2B2D42] placeholder-[#8D99AE] mb-4 focus:outline-none focus:border-[#FF6B6B]"
              rows={2}
              maxLength={200}
              data-testid="description-input"
            />
            {photoPreview ? (
              <div className="relative mb-4 max-w-[220px] mx-auto">
                <img src={photoPreview} alt="Preview" className="w-full aspect-square object-cover object-center rounded-2xl shadow-sm" />
                <button onClick={clearSelectedPhoto} className="absolute top-2 right-2 p-1 bg-black/50 rounded-full text-white"><X className="w-4 h-4" /></button>
              </div>
            ) : (
              <button onClick={() => fileInputRef.current?.click()} className="w-full p-8 border-2 border-dashed border-[#8D99AE]/30 rounded-xl flex flex-col items-center gap-2 text-[#8D99AE] hover:border-[#FF6B6B] hover:text-[#FF6B6B] transition-colors mb-4" data-testid="add-photo-btn">
                <Camera className="w-8 h-8" /><span>{t("addPhoto")}</span>
              </button>
            )}
          </div>
          <DrawerFooter className="pt-0">
            <Button onClick={handleSubmitReport} disabled={loading} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-6 rounded-xl text-lg font-bold" style={{ fontFamily: 'Nunito, sans-serif' }} data-testid="submit-report-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t("submitReport")}
            </Button>
            <DrawerClose asChild><Button variant="ghost" className="text-[#8D99AE]">{t("cancel")}</Button></DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>

      {/* Details Popup */}
      {showDetailsDrawer && selectedReport && (
        <>
          <div
            className="fixed inset-0 z-[1600] bg-black/20"
            onClick={() => setShowDetailsDrawer(false)}
            aria-hidden="true"
          />
          <div
            className="fixed left-1/2 -translate-x-1/2 z-[1601] w-[min(calc(100vw-1rem),21rem)] rounded-3xl bg-white border border-black/5 shadow-2xl overflow-hidden"
            style={{
              bottom: `calc(env(safe-area-inset-bottom, 0px) + ${detailsCardBottomPx}px)`,
              maxHeight: `${detailsCardMaxHeightPx}px`,
            }}
            data-testid="details-drawer"
          >
            <div className="mx-auto mt-3 h-1.5 w-16 rounded-full bg-[#E9ECF2]" />
            <div className="px-3 pt-2 pb-3 overflow-y-auto">
              <div className="flex items-center justify-between gap-3 mb-2">
                <h2 className="text-lg font-bold text-[#2B2D42] truncate" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("detailsTitle")}</h2>
                <Button variant="ghost" className="text-[#8D99AE] h-7 px-2 shrink-0" onClick={() => setShowDetailsDrawer(false)}>
                  {t("close")}
                </Button>
              </div>

              <div className="flex items-start gap-3">
                {selectedReport.photo_url && (
                  <div className="w-24 shrink-0 rounded-2xl overflow-hidden shadow-sm bg-[#F8F9FA]">
                    <img src={`${API}/files/${selectedReport.photo_url}`} alt={t("mapUi.photoAlt")} className="w-full aspect-square object-cover object-center" data-testid="report-photo" />
                  </div>
                )}

                <div className="min-w-0 flex-1">
                  {selectedReport.description && (
                    <p className="text-sm text-[#2B2D42] mb-2 italic line-clamp-2">"{selectedReport.description}"</p>
                  )}

                  <div className="flex items-center gap-2 mb-2 min-w-0">
                    <User className="w-4 h-4 text-[#8D99AE] shrink-0" />
                    <span className="text-sm text-[#2B2D42] font-medium truncate">{selectedReport.contributor_name || t("mapUi.anonymous")}</span>
                  </div>

                  <div className="flex items-center gap-2 text-[#8D99AE] mb-2 min-w-0">
                    <Clock className="w-4 h-4 shrink-0" />
                    <span className="text-xs truncate">{formatDate(selectedReport.refreshed_at || selectedReport.created_at)}</span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {selectedReport.status !== "pending" && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${selectedReport.status === 'verified' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                        {statusLabel(selectedReport.status)}
                      </span>
                    )}
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${selectedReport.freshness === 'Fresca' ? 'bg-red-100 text-red-700' : selectedReport.freshness === 'En proceso' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}>
                      {freshnessLabel(selectedReport.freshness)}
                    </span>
                    {selectedReport.municipality && (
                      <span className="text-[10px] bg-[#FF6B6B]/10 text-[#FF6B6B] px-2 py-0.5 rounded-full truncate max-w-full">
                        {selectedReport.municipality}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3 text-xs text-[#8D99AE]">
                    <div className="flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5 text-[#66BB6A]" /><span>{selectedReport.upvotes || 0}</span></div>
                    <div className="flex items-center gap-1"><ThumbsDown className="w-3.5 h-3.5 text-[#FF5252]" /><span>{selectedReport.downvotes || 0}</span></div>
                    <div className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-[#66BB6A]" /><span>{selectedReport.cleaned_count || 0}</span></div>
                    <div>{tf("mapUi.validations", { count: selectedReport.validation_count || 0 })}</div>
                    {selectedReport.confidence !== undefined && (
                      <div>{tf("mapUi.confidence", { value: selectedReport.confidence })}</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-3 rounded-2xl bg-[#F8F9FA] px-3 py-2 text-[11px] leading-5 text-[#5C677D]">
                {t("mapUi.communityReportsAdvisory")}
              </div>

              {selectedReport.contributor_rank && (
                <div className="mt-2 mb-2">
                  <span className="inline-flex text-[10px] text-[#FF6B6B] bg-[#FF6B6B]/10 px-2 py-1 rounded-full max-w-full truncate">
                    {getRankLabel(selectedReport.contributor_rank_key || selectedReport.contributor_rank, t)}
                  </span>
                </div>
              )}

              <div className="bg-[#F8F9FA] rounded-xl p-2.5 mb-2 text-center text-xs text-[#8D99AE]">
                {tf("mapUi.proximityRequired", { meters: ACTION_PROXIMITY_METERS })}
              </div>

              <div className="grid grid-cols-2 gap-2 mb-2">
                <Button size="sm" variant="outline" onClick={() => handleReportVote("upvote")} className="h-9 text-[#66BB6A] border-[#66BB6A]/30 hover:bg-[#66BB6A]/10" data-testid="upvote-btn">
                  <ThumbsUp className="w-4 h-4 mr-1" /> {t("mapUi.helpful")}
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleReportVote("downvote")} className="h-9 text-[#FF5252] border-[#FF5252]/30 hover:bg-[#FF5252]/10" data-testid="downvote-btn">
                  <ThumbsDown className="w-4 h-4 mr-1" /> {t("mapUi.notHelpful")}
                </Button>
              </div>

              {myValidation ? (
                <div className="bg-[#F8F9FA] rounded-xl p-2.5 mb-2 text-center text-xs text-[#8D99AE]">
                  {tf("mapUi.yourValidation", { value: myValidation === "confirm" ? t("mapUi.confirmed") : t("mapUi.rejected") })}
                </div>
              ) : null}

              {!myVote ? (
                <Button onClick={() => handleVote("cleaned")} disabled={loading} className="w-full mb-2 bg-[#66BB6A] hover:bg-[#4CAF50] text-white py-3 rounded-xl" data-testid="vote-cleaned-btn"><CheckCircle className="w-4 h-4 mr-2" />{t("mapUi.noLongerHere")}</Button>
              ) : (
                <div className="bg-[#F8F9FA] rounded-xl p-2.5 mb-2 text-center text-xs text-[#8D99AE]">{t("mapUi.alreadyMarkedResolved")}: {myVote === "still_there" ? t("stillThere") : t("mapUi.noLongerHere")}</div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <Button variant="ghost" onClick={handleShare} className="h-9 text-[#42A5F5] hover:text-[#1E88E5]" data-testid="share-btn">
                  <Share2 className="w-4 h-4 mr-2" />{t("mapUi.share")}
                </Button>
                <Button variant="ghost" onClick={() => { setShowFlagDrawer(true); setShowDetailsDrawer(false); }} className="h-9 text-[#8D99AE] hover:text-[#FF5252]" data-testid="flag-report-btn">
                  <Flag className="w-4 h-4 mr-2" />{t("flagReport")}
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

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

      {/* Feedback Drawer */}
      <FeedbackDrawer open={showFeedback} onClose={() => setShowFeedback(false)} />

      {/* Points Popup */}
      {pointsEarned && (
        <PointsPopup points={pointsEarned.points} breakdown={pointsEarned.breakdown} onDone={() => setPointsEarned(null)} />
      )}

      {/* Smart Notification Prompt */}
      {showNotifPrompt && (
        <div className="fixed bottom-24 left-4 right-4 z-[2000] bg-[#2B2D42] rounded-xl p-4 shadow-xl flex items-center gap-3" data-testid="notif-prompt">
          <Bell className="w-5 h-5 text-[#FF6B6B] shrink-0" />
          <div className="flex-1">
            <p className="text-white text-sm font-bold">{t("mapUi.notificationTitle")}</p>
            <p className="text-white/60 text-xs">{t("mapUi.notificationBody")}</p>
          </div>
          <button onClick={async () => {
            localStorage.setItem("notif_prompted", "1");
            setShowNotifPrompt(false);
            try {
              await subscribeToPush(userLocation);
              setPushEnabled(true);
              toast.success(t("mapUi.pushEnabled"));
            } catch (err) {
              if (err?.message === "native_push_disabled_for_build") {
                toast.error(t(getPushUnavailableReasonKey()));
              }
            }
          }} className="bg-[#FF6B6B] text-white text-xs font-bold px-3 py-1.5 rounded-lg" data-testid="notif-enable">OK</button>
          <button onClick={() => { localStorage.setItem("notif_prompted", "1"); setShowNotifPrompt(false); }} className="text-white/40 text-xs" data-testid="notif-dismiss">{t("mapUi.notificationNo")}</button>
        </div>
      )}
    </div>
  );
}
