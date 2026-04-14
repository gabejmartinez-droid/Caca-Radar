import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Star } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import axios from "axios";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function SubscriptionPage() {
  const { user, checkAuth } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();

  const handleSubscribe = async (plan) => {
    if (!user) { navigate("/login"); return; }
    try {
      await axios.post(`${API}/users/subscribe`, { plan }, { withCredentials: true });
      toast.success("Suscripción activada");
      await checkAuth();
      navigate("/leaderboard");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    }
  };

  const userFeatures = [
    "Tu nombre y rango visibles en tus reportes",
    "Nombre de usuario personalizado",
    "Leaderboard nacional y por ciudad",
    "Insignias de reportero",
    "Multiplicador de puntos 1.5x"
  ];

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? 'rtl' : 'ltr'}`} data-testid="subscription-page">
      <div className="p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-[#FF6B6B] rounded-full flex items-center justify-center">
            <Star className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>Premium</h1>
        </div>
        <p className="text-[#8D99AE] mb-6">Reportes gratuitos para todos. Suscríbete para destacar y competir.</p>

        {/* Free vs Premium comparison */}
        <div className="bg-white rounded-2xl shadow-sm p-5 mb-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <h3 className="font-bold text-[#2B2D42] text-sm mb-2">Gratis</h3>
              <ul className="space-y-1.5 text-xs text-[#8D99AE]">
                <li>Reportar y ver el mapa</li>
                <li>Votar y validar</li>
                <li>Reportes como "Anónimo"</li>
              </ul>
            </div>
            <div className="w-px bg-[#F8F9FA]"></div>
            <div className="flex-1">
              <h3 className="font-bold text-[#FF6B6B] text-sm mb-2">Premium</h3>
              <ul className="space-y-1.5 text-xs text-[#2B2D42]">
                {userFeatures.map((f) => (
                  <li key={f} className="flex items-start gap-1.5">
                    <Check className="w-3.5 h-3.5 text-[#66BB6A] mt-0.5 shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Pricing */}
        <div className="grid gap-4 mb-8">
          <div className="bg-white rounded-2xl shadow-sm p-6 border-2 border-transparent hover:border-[#FF6B6B] transition-colors">
            <h3 className="font-bold text-[#2B2D42] mb-1">Mensual</h3>
            <div className="flex items-baseline gap-1 mb-4">
              <span className="text-3xl font-black text-[#2B2D42]">0,99</span>
              <span className="text-lg text-[#8D99AE]">€/mes</span>
            </div>
            <Button onClick={() => handleSubscribe("monthly")} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold" data-testid="subscribe-monthly-btn">
              Suscribirse
            </Button>
          </div>

          <div className="bg-white rounded-2xl shadow-sm p-6 border-2 border-[#FF6B6B] relative">
            <div className="absolute -top-3 right-4 bg-[#FF6B6B] text-white text-xs font-bold px-3 py-1 rounded-full">AHORRA 17%</div>
            <h3 className="font-bold text-[#2B2D42] mb-1">Anual</h3>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-3xl font-black text-[#2B2D42]">9,99</span>
              <span className="text-lg text-[#8D99AE]">€/año</span>
            </div>
            <p className="text-xs text-[#8D99AE] mb-4">Solo 0,83€/mes</p>
            <Button onClick={() => handleSubscribe("annual")} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white py-5 rounded-xl font-bold" data-testid="subscribe-annual-btn">
              Suscribirse
            </Button>
          </div>
        </div>

        {/* Municipality section */}
        <div className="bg-[#2B2D42] rounded-2xl p-6 text-white">
          <h2 className="font-bold text-lg mb-2" style={{ fontFamily: 'Nunito, sans-serif' }}>Para Ayuntamientos</h2>
          <p className="text-white/70 text-sm mb-4">Panel de control con estadísticas, moderación de contenido y gestión de reportes en tu municipio.</p>
          <div className="flex items-baseline gap-1 mb-4">
            <span className="text-3xl font-black">49</span>
            <span className="text-lg text-white/60">€/mes</span>
          </div>
          <Button onClick={() => navigate("/dashboard/register")} variant="outline" className="w-full border-white/30 text-white hover:bg-white/10 py-5 rounded-xl font-bold" data-testid="municipality-subscribe-btn">
            Registrar Municipio
          </Button>
        </div>

        <p className="text-center text-xs text-[#8D99AE] mt-6">
          El pago se procesará a través de la App Store o Google Play.
          <br />Puedes cancelar en cualquier momento.
        </p>
      </div>
    </div>
  );
}
