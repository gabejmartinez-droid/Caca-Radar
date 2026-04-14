import { useNavigate } from "react-router-dom";
import { MapPin, ArrowLeft, Check, Star } from "lucide-react";
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
    if (!user) {
      navigate("/login");
      return;
    }
    try {
      await axios.post(`${API}/users/subscribe`, { plan }, { withCredentials: true });
      toast.success("Suscripción activada");
      await checkAuth();
      navigate("/leaderboard");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error activating subscription");
    }
  };

  const features = [
    "Nombre de usuario personalizado",
    "Leaderboard nacional",
    "Leaderboard por ciudad",
    "Insignias de reportero",
    "Estadísticas avanzadas"
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
        <p className="text-[#8D99AE] mb-8">Accede a funciones exclusivas y compite en los leaderboards.</p>

        {/* Features */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-6">
          <h2 className="font-bold text-[#2B2D42] mb-4" style={{ fontFamily: 'Nunito, sans-serif' }}>Funciones Premium</h2>
          <div className="space-y-3">
            {features.map((f) => (
              <div key={f} className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-[#66BB6A]/10 flex items-center justify-center">
                  <Check className="w-4 h-4 text-[#66BB6A]" />
                </div>
                <span className="text-sm text-[#2B2D42]">{f}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-4">
          <div className="bg-white rounded-2xl shadow-sm p-6 border-2 border-transparent hover:border-[#FF6B6B] transition-colors">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-[#2B2D42]">Mensual</h3>
            </div>
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
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-[#2B2D42]">Anual</h3>
            </div>
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

        <p className="text-center text-xs text-[#8D99AE] mt-6">
          El pago se procesará a través de la App Store o Google Play.
          <br />Puedes cancelar en cualquier momento desde la configuración de tu dispositivo.
        </p>
      </div>
    </div>
  );
}
