import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { User, MapPin, Trophy, Star, Shield, Flame, ArrowLeft, Loader2, Edit3, Check, X, Crown, BarChart3, Share2, Bell, Heart } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { subscribeToPush, unsubscribeFromPush, isPushSupported, getPushPermissionState } from "../utils/pushManager";

import { API } from "../config";

function TrustBar({ score }) {
  const color = score >= 80 ? "#66BB6A" : score >= 50 ? "#42A5F5" : score >= 20 ? "#FFA726" : "#FF5252";
  return (
    <div className="w-full bg-[#F8F9FA] rounded-full h-2.5">
      <div className="h-2.5 rounded-full transition-all duration-500" style={{ width: `${score}%`, backgroundColor: color }} />
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-[#F8F9FA] rounded-xl p-4 text-center">
      <Icon className="w-5 h-5 mx-auto mb-1" style={{ color }} />
      <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
      <p className="text-xs text-[#8D99AE]">{label}</p>
    </div>
  );
}

export default function ProfilePage() {
  const { user, checkAuth } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingUsername, setEditingUsername] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [saving, setSaving] = useState(false);
  const [notificationsOn, setNotificationsOn] = useState(() => localStorage.getItem("caca_notifications") !== "off");

  useEffect(() => {
    if (!user) { navigate("/login"); return; }
    fetchProfile();
  }, [user, navigate]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/users/profile`, { withCredentials: true });
      setProfile(data);
      setNewUsername(data.username || "");
      // Check actual push subscription status
      try {
        const { data: pushStatus } = await axios.get(`${API}/push/status`, { withCredentials: true });
        setNotificationsOn(pushStatus.subscribed);
      } catch { /* ignore */ }
    } catch { navigate("/login"); }
    finally { setLoading(false); }
  };

  const handleSaveUsername = async () => {
    if (!newUsername.trim() || newUsername.length < 3) { toast.error("Mínimo 3 caracteres"); return; }
    setSaving(true);
    try {
      await axios.put(`${API}/users/username`, { username: newUsername.trim() }, { withCredentials: true });
      toast.success("Nombre de usuario actualizado");
      setEditingUsername(false);
      await checkAuth();
      fetchProfile();
    } catch (err) { toast.error(err.response?.data?.detail || "Error"); }
    finally { setSaving(false); }
  };

  const handleToggleNotifications = async () => {
    const supported = await isPushSupported();
    if (!supported) {
      toast.error("Tu navegador no soporta notificaciones push");
      return;
    }
    if (notificationsOn) {
      await unsubscribeFromPush();
      setNotificationsOn(false);
      toast.success("Notificaciones desactivadas");
    } else {
      try {
        await subscribeToPush(null);
        setNotificationsOn(true);
        toast.success("Notificaciones activadas");
      } catch (err) {
        if (err.message === "permission_denied") {
          toast.error("Permiso de notificaciones denegado en el navegador");
        } else {
          toast.error("Error activando notificaciones");
        }
      }
    }
  };

  const handleShareProfile = async () => {
    try {
      const { data } = await axios.get(`${API}/users/${user._id || user.id}/share`, { withCredentials: true });
      const shareText = `${data.text}\n\n${data.download_text}`;
      if (navigator.share) {
        await navigator.share({ title: data.title, text: shareText, url: data.url });
      } else {
        await navigator.clipboard.writeText(shareText);
        toast.success("Perfil copiado al portapapeles");
      }
    } catch (err) {
      if (err.name !== "AbortError") toast.error("Error al compartir");
    }
  };

  if (loading) return <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" /></div>;

  const trustTier = (profile?.trust_score || 50) >= 80 ? "Confiable" : (profile?.trust_score || 50) >= 50 ? "Normal" : (profile?.trust_score || 50) >= 20 ? "Bajo" : "Restringido";

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? 'rtl' : 'ltr'}`} data-testid="profile-page">
      <div className="p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        {/* Profile Header */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-4 text-center">
          <div className="w-20 h-20 bg-[#FF6B6B] rounded-full flex items-center justify-center mx-auto mb-3">
            <User className="w-10 h-10 text-white" />
          </div>

          {/* Username */}
          {editingUsername ? (
            <div className="flex items-center gap-2 justify-center mb-2">
              <Input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} className="max-w-[200px] text-center" maxLength={20} data-testid="username-edit-input" />
              <Button size="sm" variant="ghost" onClick={handleSaveUsername} disabled={saving} className="text-[#66BB6A]"><Check className="w-4 h-4" /></Button>
              <Button size="sm" variant="ghost" onClick={() => setEditingUsername(false)} className="text-[#FF5252]"><X className="w-4 h-4" /></Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 justify-center mb-1">
              <h1 className="text-xl font-black text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{profile?.username || profile?.name || "Usuario"}</h1>
              <button onClick={() => setEditingUsername(true)} className="text-[#8D99AE] hover:text-[#FF6B6B]" data-testid="edit-username-btn"><Edit3 className="w-4 h-4" /></button>
            </div>
          )}

          {/* Rank */}
          <div className="flex items-center justify-center gap-2 mb-1">
            <Crown className="w-4 h-4 text-[#FF6B6B]" />
            <span className="text-sm font-bold text-[#FF6B6B]">{profile?.rank || "Aspirante Cagón"}</span>
          </div>
          <p className="text-xs text-[#8D99AE]">Nivel {profile?.level || 1} — Percentil {profile?.rank_percentile || 0}%</p>

          {/* Subscription badge */}
          {user?.subscription_active ? (
            <Badge className="mt-2 bg-[#FF6B6B]"><Star className="w-3 h-3 mr-1 fill-white" />Premium</Badge>
          ) : (
            <Button size="sm" variant="outline" onClick={() => navigate("/subscribe")} className="mt-2 text-[#FF6B6B] border-[#FF6B6B]" data-testid="upgrade-btn">
              <Star className="w-3 h-3 mr-1" />Hazte Premium
            </Button>
          )}

          <Button size="sm" variant="ghost" onClick={handleShareProfile} className="mt-2 text-[#42A5F5]" data-testid="share-profile-btn">
            <Share2 className="w-4 h-4 mr-1" />Compartir perfil
          </Button>
          <Button size="sm" variant="ghost" onClick={() => navigate("/impact")} className="mt-1 text-[#66BB6A]" data-testid="view-impact-btn">
            <Heart className="w-4 h-4 mr-1" />Mi Impacto Comunitario
          </Button>
        </div>

        {/* Score Card */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
          <div className="text-center mb-4">
            <p className="text-5xl font-black text-[#2B2D42]">{profile?.total_score || 0}</p>
            <p className="text-sm text-[#8D99AE]">Puntos totales</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <StatCard icon={MapPin} label="Reportes" value={profile?.report_count || 0} color="#FF6B6B" />
            <StatCard icon={BarChart3} label="Votos" value={profile?.vote_count || 0} color="#42A5F5" />
            <StatCard icon={Flame} label="Racha" value={`${profile?.streak_days || 0}d`} color="#FFA726" />
          </div>
          {profile?.accuracy_rate !== undefined && (
            <div className="flex gap-3 mt-3">
              <div className="flex-1 bg-[#F8F9FA] rounded-lg p-2 text-center">
                <p className="text-lg font-bold text-[#66BB6A]">{profile.accuracy_rate}%</p>
                <p className="text-xs text-[#8D99AE]">Precisión</p>
              </div>
              <div className="flex-1 bg-[#F8F9FA] rounded-lg p-2 text-center">
                <p className="text-lg font-bold text-[#42A5F5]">{profile.impact_score || 0}</p>
                <p className="text-xs text-[#8D99AE]">Impacto</p>
              </div>
            </div>
          )}
        </div>

        {/* Badges */}
        {profile?.badges && profile.badges.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
            <h3 className="font-bold text-[#2B2D42] mb-3 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-[#FFA726]" />Insignias ({profile.badges_count || 0})
            </h3>
            <div className="grid grid-cols-3 gap-3">
              {profile.badges.map((badge) => (
                <div key={badge.id} className="bg-[#FFA726]/10 rounded-xl p-3 text-center">
                  <div className="w-8 h-8 bg-[#FFA726] rounded-full flex items-center justify-center mx-auto mb-1">
                    <Star className="w-4 h-4 text-white" />
                  </div>
                  <p className="text-xs font-bold text-[#2B2D42]">{badge.name}</p>
                  <p className="text-xs text-[#8D99AE]">{badge.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trust Score */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#42A5F5]" />
              <span className="font-bold text-[#2B2D42]">Nivel de Confianza</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-[#2B2D42]">{profile?.trust_score || 50}</span>
              <span className="text-xs text-[#8D99AE]"> / 100</span>
            </div>
          </div>
          <TrustBar score={profile?.trust_score || 50} />
          <p className="text-xs text-[#8D99AE] mt-2">Estado: <span className="font-medium">{trustTier}</span></p>
          <div className="grid grid-cols-4 gap-1 mt-3">
            {[
              { label: "Restringido", min: 0, max: 19 },
              { label: "Bajo", min: 20, max: 49 },
              { label: "Normal", min: 50, max: 79 },
              { label: "Confiable", min: 80, max: 100 },
            ].map((tier) => (
              <div key={tier.label} className={`text-center py-1 rounded text-xs ${(profile?.trust_score || 50) >= tier.min && (profile?.trust_score || 50) <= tier.max ? 'bg-[#FF6B6B]/10 text-[#FF6B6B] font-bold' : 'text-[#8D99AE]'}`}>
                {tier.label}
              </div>
            ))}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-[#42A5F5]" />
              <span className="font-bold text-[#2B2D42]">Notificaciones</span>
            </div>
            <button
              onClick={handleToggleNotifications}
              className={`relative w-12 h-6 rounded-full transition-colors ${notificationsOn ? "bg-[#66BB6A]" : "bg-[#8D99AE]/30"}`}
              data-testid="notification-toggle"
            >
              <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${notificationsOn ? "translate-x-6" : "translate-x-0.5"}`} />
            </button>
          </div>
          <p className="text-xs text-[#8D99AE] mt-2">Recibe avisos cuando se reporten cacas cerca de tus ubicaciones guardadas.</p>
        </div>

        {/* How scoring works */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h3 className="font-bold text-[#2B2D42] mb-3">Cómo ganar puntos</h3>
          <div className="space-y-2 text-sm">
            {[
              { action: "Reportar", pts: "+10", extra: "+5 foto, +3 descripción" },
              { action: "Validación correcta", pts: "+4", extra: "+5 bonus primeros 5" },
              { action: "Reporte verificado", pts: "+5", extra: "" },
              { action: "Voto positivo recibido", pts: "+2", extra: "" },
              { action: "Racha 3 / 7 / 30 días", pts: "+5 / +15 / +50", extra: "" },
            ].map(({ action, pts, extra }) => (
              <div key={action} className="flex justify-between items-center py-1.5 border-b border-[#F8F9FA] last:border-0">
                <span className="text-[#2B2D42]">{action}</span>
                <div className="text-right">
                  <span className="font-bold text-[#66BB6A]">{pts}</span>
                  {extra && <span className="text-xs text-[#8D99AE] block">{extra}</span>}
                </div>
              </div>
            ))}
            {user?.subscription_active && (
              <div className="bg-[#FF6B6B]/5 rounded-lg p-2 mt-2 text-center">
                <Star className="w-4 h-4 text-[#FF6B6B] inline mr-1" />
                <span className="text-xs text-[#FF6B6B] font-medium">Premium: multiplicador 1.5x en todos los puntos</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
