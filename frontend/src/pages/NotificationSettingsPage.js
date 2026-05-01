import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Bell, Loader2, MapPin, Navigation, Shield, Star, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { API } from "../config";
import { getPushPermissionState, getPushUnavailableReasonKey, isPushSupported, subscribeToPush, unsubscribeFromPush } from "../utils/pushManager";
import { isCapacitorNative } from "../tokenManager";

const RADIUS_OPTIONS = [
  { value: "250", labelEs: "250 m", labelEn: "250 m" },
  { value: "500", labelEs: "500 m", labelEn: "500 m" },
  { value: "1000", labelEs: "1 km", labelEn: "1 km" },
  { value: "2000", labelEs: "2 km", labelEn: "2 km" },
];

const SAVED_LOCATION_BASES = ["/users/saved-locations", "/push/saved-locations"];

export default function NotificationSettingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { language, isRtl, t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [notificationsOn, setNotificationsOn] = useState(false);
  const [permissionState, setPermissionState] = useState("prompt");
  const [radiusMeters, setRadiusMeters] = useState("500");
  const [alertLocation, setAlertLocation] = useState(null);
  const [savedLocations, setSavedLocations] = useState([]);
  const [locationLabel, setLocationLabel] = useState("");
  const [busyAction, setBusyAction] = useState("");

  const copy = useMemo(() => {
    if (language === "en") {
      return {
        title: "Notification settings",
        subtitle: "Control nearby poop alerts on this device.",
        statusOn: "Alerts enabled",
        statusOff: "Alerts disabled",
        permissionGranted: "System permission granted",
        permissionPrompt: "System permission not decided yet",
        permissionDenied: "Notifications are blocked in system settings",
        currentLocation: "Current alert location",
        noLocation: "No alert location saved yet",
        refreshLocation: "Use my current location",
        radius: "Alert radius",
        manageSaved: "Saved alert places",
        manageSavedDesc: "Premium users can save favorite places and switch alerts between them.",
        saveCurrent: "Save current location",
        savePlaceholder: "Label this place",
        useForAlerts: "Use for alerts",
        deleteLocation: "Delete",
        premiumNeeded: "Premium required to save multiple places",
        permissionHelp: "If permission is blocked, re-enable notifications from your phone settings for Caca Radar.",
        emptySaved: "No saved places yet",
        quickToggle: "Notifications",
        openSubscribe: "Get Premium",
      };
    }
    return {
      title: "Ajustes de notificaciones",
      subtitle: "Controla las alertas de caca cercanas en este dispositivo.",
      statusOn: "Alertas activadas",
      statusOff: "Alertas desactivadas",
      permissionGranted: "Permiso del sistema concedido",
      permissionPrompt: "El sistema aún no ha decidido el permiso",
      permissionDenied: "Las notificaciones están bloqueadas en los ajustes del sistema",
      currentLocation: "Ubicación actual de alertas",
      noLocation: "Todavía no hay una ubicación de alertas guardada",
      refreshLocation: "Usar mi ubicación actual",
      radius: "Radio de alertas",
      manageSaved: "Lugares guardados para alertas",
      manageSavedDesc: "Los usuarios premium pueden guardar sitios favoritos y mover las alertas entre ellos.",
      saveCurrent: "Guardar ubicación actual",
      savePlaceholder: "Ponle un nombre a este sitio",
      useForAlerts: "Usar para alertas",
      deleteLocation: "Eliminar",
      premiumNeeded: "Hace falta Premium para guardar varios sitios",
      permissionHelp: "Si el permiso está bloqueado, vuelve a activar las notificaciones desde los ajustes del teléfono para Caca Radar.",
      emptySaved: "Todavía no hay lugares guardados",
      quickToggle: "Notificaciones",
      openSubscribe: "Hazte Premium",
    };
  }, [language]);

  const getFreshLocation = useCallback(() => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("No geolocation"));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
      );
    });
  }, []);

  const requestSavedLocations = useCallback(async (method, pathSuffix = "", payload = null) => {
    let lastError = null;
    for (const base of SAVED_LOCATION_BASES) {
      try {
        const config = {
          method,
          url: `${API}${base}${pathSuffix}`,
          withCredentials: true,
        };
        if (payload != null) {
          config.data = payload;
        }
        return await axios(config);
      } catch (err) {
        lastError = err;
        if (err?.response?.status !== 404) {
          throw err;
        }
      }
    }
    throw lastError || new Error("saved_locations_unavailable");
  }, []);

  const syncPushPreferences = useCallback(async ({ latitude, longitude, radius }) => {
    try {
      return await axios.put(
        `${API}/push/preferences`,
        {
          latitude,
          longitude,
          radius_meters: radius,
        },
        { withCredentials: true }
      );
    } catch (err) {
      if (err?.response?.status !== 404) {
        throw err;
      }

      return subscribeToPush({
        lat: latitude ?? alertLocation?.lat ?? null,
        lng: longitude ?? alertLocation?.lng ?? null,
        radiusMeters: radius ?? Number(radiusMeters || 500),
      });
    }
  }, [alertLocation?.lat, alertLocation?.lng, radiusMeters]);

  const refreshState = useCallback(async () => {
    if (!user) {
      navigate("/login");
      return;
    }

    setLoading(true);
    try {
      const [{ data: pushStatus }, permission] = await Promise.all([
        axios.get(`${API}/push/status`, { withCredentials: true }),
        getPushPermissionState().catch(() => "prompt"),
      ]);

      setNotificationsOn(Boolean(pushStatus.subscribed));
      setRadiusMeters(String(pushStatus.radius_meters || 500));
      setAlertLocation(
        pushStatus.latitude != null && pushStatus.longitude != null
          ? { lat: pushStatus.latitude, lng: pushStatus.longitude }
          : null
      );
      setPermissionState(permission);

      if (user.subscription_active) {
        const { data } = await requestSavedLocations("get");
        setSavedLocations(Array.isArray(data) ? data : []);
      } else {
        setSavedLocations([]);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login");
      } else {
        toast.error(err.response?.data?.detail || "Error");
      }
    } finally {
      setLoading(false);
    }
  }, [navigate, requestSavedLocations, user]);

  useEffect(() => {
    refreshState();
  }, [refreshState]);

  const handleToggleNotifications = async () => {
    const supported = await isPushSupported();
    if (!supported) {
      toast.error(t(getPushUnavailableReasonKey()));
      return;
    }

    setBusyAction("toggle");
    try {
      if (notificationsOn) {
        await unsubscribeFromPush();
        setNotificationsOn(false);
        toast.success(t("mapUi.pushDisabled"));
        await refreshState();
        return;
      }

      let userLocation = null;
      try {
        userLocation = await getFreshLocation();
      } catch {
        // Location is nice to have for nearby alerts, but not required for subscription creation.
      }
      await subscribeToPush(userLocation);
      toast.success(t("mapUi.pushEnabledNearby"));
      await refreshState();
    } catch (err) {
      if (err.message === "permission_denied") {
        toast.error(t("profileUi.browserPermissionDenied"));
      } else {
        toast.error(t("mapUi.pushError"));
      }
    } finally {
      setBusyAction("");
    }
  };

  const handleUpdateRadius = async (nextRadius) => {
    setRadiusMeters(nextRadius);
    if (!notificationsOn) return;
    setBusyAction("radius");
    try {
      await syncPushPreferences({ radius: Number(nextRadius) });
      toast.success(copy.statusOn);
      await refreshState();
    } catch (err) {
      toast.error(err.response?.data?.detail || t("mapUi.pushError"));
      await refreshState();
    } finally {
      setBusyAction("");
    }
  };

  const handleUseCurrentLocation = async () => {
    setBusyAction("current-location");
    try {
      const loc = await getFreshLocation();
      if (notificationsOn) {
        await syncPushPreferences({ latitude: loc.lat, longitude: loc.lng });
      } else {
        await subscribeToPush({ ...loc, radiusMeters: Number(radiusMeters || 500) });
        setNotificationsOn(true);
      }
      setAlertLocation(loc);
      toast.success(copy.currentLocation);
      await refreshState();
    } catch (err) {
      if (err.message === "permission_denied") {
        toast.error(t("profileUi.browserPermissionDenied"));
      } else {
        toast.error(err.response?.data?.detail || t("mapUi.pushError"));
      }
    } finally {
      setBusyAction("");
    }
  };

  const handleSaveCurrentLocation = async () => {
    if (!user.subscription_active) {
      navigate("/subscribe");
      return;
    }
    if (!locationLabel.trim()) {
      toast.error(copy.savePlaceholder);
      return;
    }
    setBusyAction("save-location");
    try {
      const loc = alertLocation || await getFreshLocation();
      await requestSavedLocations("post", "", {
        name: locationLabel.trim(),
        label: locationLabel.trim(),
        latitude: loc.lat,
        longitude: loc.lng,
      });
      setLocationLabel("");
      toast.success(copy.saveCurrent);
      await refreshState();
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || "Error");
    } finally {
      setBusyAction("");
    }
  };

  const handleApplySavedLocation = async (loc) => {
    setBusyAction(`apply-${loc.id || loc.name}`);
    try {
      if (notificationsOn) {
        await syncPushPreferences({ latitude: loc.latitude, longitude: loc.longitude });
      } else {
        await subscribeToPush({ lat: loc.latitude, lng: loc.longitude, radiusMeters: Number(radiusMeters || 500) });
        setNotificationsOn(true);
      }
      toast.success(copy.currentLocation);
      await refreshState();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    } finally {
      setBusyAction("");
    }
  };

  const handleDeleteSavedLocation = async (loc) => {
    setBusyAction(`delete-${loc.id || loc.name}`);
    try {
      await requestSavedLocations("delete", `/${encodeURIComponent(loc.name)}`);
      toast.success(copy.deleteLocation);
      await refreshState();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    } finally {
      setBusyAction("");
    }
  };

  const permissionBadge = permissionState === "granted"
    ? { text: copy.permissionGranted, className: "bg-[#66BB6A]/10 text-[#2E7D32]" }
    : permissionState === "denied"
      ? { text: copy.permissionDenied, className: "bg-[#FF6B6B]/10 text-[#C62828]" }
      : { text: copy.permissionPrompt, className: "bg-[#42A5F5]/10 text-[#1565C0]" };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" />
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="notification-settings-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/profile")} className="text-[#8D99AE]">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8 space-y-4">
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-[#42A5F5]" />
                <h1 className="text-xl font-black text-[#2B2D42]">{copy.title}</h1>
              </div>
              <p className="text-sm text-[#8D99AE] mt-2">{copy.subtitle}</p>
            </div>
            <button
              onClick={handleToggleNotifications}
              disabled={busyAction === "toggle"}
              className={`relative mt-1 w-12 h-6 rounded-full transition-colors ${notificationsOn ? "bg-[#66BB6A]" : "bg-[#8D99AE]/30"}`}
              data-testid="notification-settings-toggle"
            >
              <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${notificationsOn ? "translate-x-6" : "translate-x-0.5"}`} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-4">
            <Badge className={notificationsOn ? "bg-[#66BB6A]/10 text-[#2E7D32]" : "bg-[#8D99AE]/10 text-[#5C677D]"}>
              {notificationsOn ? copy.statusOn : copy.statusOff}
            </Badge>
            <Badge className={permissionBadge.className}>{permissionBadge.text}</Badge>
            {isCapacitorNative() && (
              <Badge className="bg-[#2B2D42]/10 text-[#2B2D42]">Native app</Badge>
            )}
          </div>

          {permissionState === "denied" && (
            <p className="text-xs text-[#8D99AE] mt-3">{copy.permissionHelp}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <Navigation className="w-5 h-5 text-[#FF6B6B]" />
            <h2 className="font-bold text-[#2B2D42]">{copy.currentLocation}</h2>
          </div>
          <div className="rounded-xl bg-[#F8F9FA] px-4 py-3 mb-4">
            {alertLocation ? (
              <div className="text-sm text-[#2B2D42]">
                <div className="font-semibold">{alertLocation.lat.toFixed(5)}, {alertLocation.lng.toFixed(5)}</div>
                <div className="text-xs text-[#8D99AE] mt-1">{copy.radius}: {Number(radiusMeters) >= 1000 ? `${Number(radiusMeters) / 1000} km` : `${radiusMeters} m`}</div>
              </div>
            ) : (
              <div className="text-sm text-[#8D99AE]">{copy.noLocation}</div>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-[1fr_auto] items-end">
            <div>
              <label className="block text-sm font-medium text-[#2B2D42] mb-2">{copy.radius}</label>
              <Select value={radiusMeters} onValueChange={handleUpdateRadius}>
                <SelectTrigger className="bg-[#F8F9FA] border-0 h-11 rounded-xl">
                  <SelectValue placeholder={copy.radius} />
                </SelectTrigger>
                <SelectContent>
                  {RADIUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {language === "en" ? option.labelEn : option.labelEs}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={handleUseCurrentLocation}
              disabled={busyAction === "current-location"}
              className="h-11 rounded-xl bg-[#FF6B6B] hover:bg-[#ff5a5a]"
            >
              {busyAction === "current-location" ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <MapPin className="w-4 h-4 mr-2" />}
              {copy.refreshLocation}
            </Button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <div className="flex items-start gap-2">
                <Star className="w-5 h-5 text-[#FFA726]" />
                <h2 className="font-bold text-[#2B2D42]">{copy.manageSaved}</h2>
              </div>
              <p className="text-xs text-[#8D99AE] mt-2">{copy.manageSavedDesc}</p>
            </div>
            {!user.subscription_active && (
              <Button variant="outline" className="rounded-xl border-[#FF6B6B] text-[#FF6B6B]" onClick={() => navigate("/subscribe")}>
                {copy.openSubscribe}
              </Button>
            )}
          </div>

          {user.subscription_active ? (
            <>
              <div className="grid gap-3 mb-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
                <div className="min-w-0">
                  <label className="block text-sm font-medium text-[#2B2D42] mb-2">
                    {copy.savePlaceholder}
                  </label>
                <Input
                  value={locationLabel}
                  onChange={(e) => setLocationLabel(e.target.value)}
                  placeholder={copy.savePlaceholder}
                  className="bg-[#F8F9FA] border-0 rounded-xl h-12 text-base px-4"
                  maxLength={40}
                />
                </div>
                <Button onClick={handleSaveCurrentLocation} disabled={busyAction === "save-location"} className="rounded-xl bg-[#42A5F5] hover:bg-[#3793dc]">
                  {busyAction === "save-location" ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  <span className="whitespace-normal text-center leading-tight">{copy.saveCurrent}</span>
                </Button>
              </div>

              <div className="space-y-3">
                {savedLocations.length === 0 && (
                  <div className="rounded-xl bg-[#F8F9FA] px-4 py-3 text-sm text-[#8D99AE]">{copy.emptySaved}</div>
                )}
                {savedLocations.map((loc) => (
                  <div key={loc.id || loc.name} className="rounded-xl bg-[#F8F9FA] px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-[#2B2D42]">{loc.label || loc.name}</div>
                        <div className="text-xs text-[#8D99AE] mt-1">
                          {Number(loc.latitude).toFixed(5)}, {Number(loc.longitude).toFixed(5)}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-lg border-[#42A5F5] text-[#42A5F5]"
                          onClick={() => handleApplySavedLocation(loc)}
                          disabled={busyAction === `apply-${loc.id || loc.name}`}
                        >
                          {copy.useForAlerts}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="text-[#FF5252]"
                          onClick={() => handleDeleteSavedLocation(loc)}
                          disabled={busyAction === `delete-${loc.id || loc.name}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="rounded-xl bg-[#FFF6E8] px-4 py-3 text-sm text-[#8A5A00] flex items-start gap-2">
              <Shield className="w-4 h-4 mt-0.5" />
              <span>{copy.premiumNeeded}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
