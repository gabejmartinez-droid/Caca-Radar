import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Star, Lock, MapPin, Filter, Camera, Bell, Crown, Zap } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import axios from "axios";
import { toast } from "sonner";

const API = "/api";

export default function SubscriptionPage() {
  const { user, checkAuth } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();

  const handleSubscribe = async (plan) => {
    if (!user) { navigate("/login"); return; }
    try {
      const { data } = await axios.post(`${API}/users/subscribe`, { plan }, { withCredentials: true });
      toast.success(data.trial ? "Prueba gratuita de 7 días activada" : "Suscripción activada");
      await checkAuth();
      navigate("/");
    } catch (err) { toast.error(err.response?.data?.detail || "Error"); }
  };

  const freeFeatures = [
    { icon: MapPin, text: "Reportar con foto y descripción" },
    { icon: MapPin, text: "Ver todos los reportes en el mapa" },
    { icon: Check, text: "Confirmar y validar reportes" },
    { icon: Crown, text: "Sistema de rangos y racha" },
    { icon: Bell, text: "Alertas de cambio de rango" },
  ];

  const premiumFeatures = [
    { icon: Zap, text: "Mapa de calor de densidad" },
    { icon: Filter, text: "Filtros avanzados (frescura, estado)" },
    { icon: Bell, text: "Alertas push para reportes cercanos" },
    { icon: Star, text: "Ranking de ciudades más limpias/sucias" },
    { icon: MapPin, text: "Ranking de barrios por limpieza" },
    { icon: Zap, text: "Ruta limpia (evitar zonas sucias)" },
    { icon: Crown, text: "Leaderboard completo + semanal" },
    { icon: Crown, text: "Nombre y rango visible en reportes" },
    { icon: Zap, text: "Multiplicador de puntos 1.5x" },
    { icon: Crown, text: "Insignia Premium en el mapa" },
  ];

  const alreadySubscribed = user?.subscription_active;

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? 'rtl' : 'ltr'}`} data-testid="subscription-page">
      <div className="p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-[#FF6B6B] to-[#FF5252] rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Star className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>Caca Radar Premium</h1>
          <p className="text-[#8D99AE] text-sm mt-1">Herramientas avanzadas para mantener tu ciudad limpia</p>
        </div>

        {/* Free vs Premium */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <h3 className="font-bold text-[#2B2D42] text-sm mb-3">Gratis</h3>
            <div className="space-y-2.5">
              {freeFeatures.map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-start gap-2">
                  <Icon className="w-3.5 h-3.5 text-[#66BB6A] mt-0.5 shrink-0" />
                  <span className="text-xs text-[#8D99AE]">{text}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-sm p-4 border-2 border-[#FF6B6B]">
            <h3 className="font-bold text-[#FF6B6B] text-sm mb-3 flex items-center gap-1"><Star className="w-3.5 h-3.5 fill-[#FF6B6B]" />Premium</h3>
            <div className="space-y-2.5">
              {premiumFeatures.map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-start gap-2">
                  <Icon className="w-3.5 h-3.5 text-[#FF6B6B] mt-0.5 shrink-0" />
                  <span className="text-xs text-[#2B2D42]">{text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {alreadySubscribed ? (
          <div className="bg-[#66BB6A]/10 rounded-2xl p-6 text-center mb-6">
            <Check className="w-8 h-8 text-[#66BB6A] mx-auto mb-2" />
            <p className="font-bold text-[#2B2D42]">Ya eres Premium</p>
            <p className="text-xs text-[#8D99AE] mt-1">Disfruta de todas las funciones</p>
          </div>
        ) : (
          <>
            {/* Free Trial CTA */}
            {!user?.trial_used && (
              <div className="bg-gradient-to-r from-[#FF6B6B] to-[#FF5252] rounded-2xl p-6 text-white text-center mb-4">
                <Zap className="w-8 h-8 mx-auto mb-2" />
                <h2 className="text-xl font-black mb-1">7 días GRATIS</h2>
                <p className="text-white/80 text-sm mb-4">Prueba todas las funciones premium sin compromiso</p>
                <Button onClick={() => handleSubscribe("monthly")} className="bg-white text-[#FF6B6B] hover:bg-white/90 py-5 px-8 rounded-xl font-bold" data-testid="free-trial-btn">
                  Empezar prueba gratuita
                </Button>
              </div>
            )}

            {/* Pricing */}
            <div className="grid gap-3">
              <div className="bg-white rounded-2xl shadow-sm p-5 hover:border-[#FF6B6B] border-2 border-transparent transition-colors">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-[#2B2D42]">Mensual</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-black text-[#2B2D42]">3,99</span>
                      <span className="text-[#8D99AE]">€/mes</span>
                    </div>
                  </div>
                  <Button onClick={() => handleSubscribe("monthly")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-6" data-testid="subscribe-monthly-btn">
                    Suscribirse
                  </Button>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm p-5 border-2 border-[#FF6B6B] relative">
                <div className="absolute -top-3 right-4 bg-[#FF6B6B] text-white text-xs font-bold px-3 py-1 rounded-full">AHORRA 37%</div>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-[#2B2D42]">Anual</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-black text-[#2B2D42]">29,99</span>
                      <span className="text-[#8D99AE]">€/año</span>
                    </div>
                    <p className="text-xs text-[#8D99AE]">Solo 2,50€/mes</p>
                  </div>
                  <Button onClick={() => handleSubscribe("annual")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-6" data-testid="subscribe-annual-btn">
                    Suscribirse
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Municipality */}
        <div className="bg-[#2B2D42] rounded-2xl p-5 text-white mt-6">
          <h2 className="font-bold mb-1" style={{ fontFamily: 'Nunito, sans-serif' }}>Para Ayuntamientos</h2>
          <p className="text-white/60 text-xs mb-3">Panel de control, analíticas avanzadas y moderación</p>
          <div className="flex justify-between items-center">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black">50</span><span className="text-white/60">€/mes</span>
            </div>
            <Button onClick={() => navigate("/dashboard/register")} variant="outline" className="border-white/30 text-white hover:bg-white/10 rounded-xl font-bold" data-testid="municipality-subscribe-btn">
              Registrar Municipio
            </Button>
          </div>
        </div>

        <p className="text-center text-xs text-[#8D99AE] mt-6">
          Pago a través de App Store o Google Play. Cancela cuando quieras.
        </p>
      </div>
    </div>
  );
}
