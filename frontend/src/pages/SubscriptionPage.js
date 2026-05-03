import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Star, MapPin, Filter, Bell, Crown, Zap, Building2, ClipboardCheck, Sparkles, Wrench } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import axios from "axios";
import { toast } from "sonner";

import { API } from "../config";
import { isCapacitorNative } from "../tokenManager";

export default function SubscriptionPage() {
  const { user, checkAuth } = useAuth();
  const { t, isRtl } = useLanguage();
  const navigate = useNavigate();

  const handleSubscribe = async (plan) => {
    if (!user) { navigate("/login"); return; }
    try {
      const { data } = await axios.post(
        `${API}/users/subscribe`,
        { plan },
        { withCredentials: !isCapacitorNative() },
      );
      toast.success(data.trial ? t("subscriptionUi.trialActivated") : t("subscriptionUi.subscriptionActivated"));
      await checkAuth();
      navigate("/");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 403) {
        toast.error("Las compras premium deben completarse con la integración oficial de la tienda.");
        return;
      }
      toast.error(detail || "Error");
    }
  };

  const freeFeatures = [
    { icon: MapPin, text: t("subscriptionUi.freePhotoDesc") },
    { icon: MapPin, text: t("subscriptionUi.freeMapReports") },
    { icon: Check, text: t("subscriptionUi.freeValidate") },
    { icon: Crown, text: t("rankUi.rankSystemFeature") },
    { icon: Bell, text: t("rankUi.rankAlertsFeature") },
  ];

  const premiumFeatures = [
    { icon: Zap, text: t("subscriptionUi.heatDensity") },
    { icon: Filter, text: t("subscriptionUi.advancedFilterDetails") },
    { icon: Bell, text: t("subscriptionUi.nearbyPushAlerts") },
    { icon: Star, text: t("premiumUi.cityRankingsFeature") },
    { icon: MapPin, text: t("premiumUi.barrioRankingsFeature") },
    { icon: Zap, text: t("subscriptionUi.cleanRoute") },
    { icon: Crown, text: t("premiumUi.weeklyLeaderboardFeature") },
    { icon: Crown, text: t("rankUi.visibleRankFeature") },
    { icon: Zap, text: t("premiumUi.pointsMultiplierFeature") },
    { icon: Crown, text: t("premiumUi.premiumBadgeFeature") },
  ];

  const alreadySubscribed = user?.subscription_active;

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? 'rtl' : 'ltr'}`} data-testid="subscription-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
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
          <h1 className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("subscriptionUi.premiumTitle")}</h1>
          <p className="text-[#8D99AE] text-sm mt-1">{t("subscriptionUi.premiumSubtitle")}</p>
        </div>

        {/* Free vs Premium */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-white rounded-2xl shadow-sm p-4">
            <h3 className="font-bold text-[#2B2D42] text-sm mb-3">{t("subscriptionUi.free")}</h3>
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
            <p className="font-bold text-[#2B2D42]">{t("subscriptionUi.alreadyPremium")}</p>
            <p className="text-xs text-[#8D99AE] mt-1">{t("subscriptionUi.enjoyFeatures")}</p>
          </div>
        ) : (
          <>
            {/* Free Trial CTA */}
            {!user?.trial_used && (
              <div className="bg-gradient-to-r from-[#FF6B6B] to-[#FF5252] rounded-2xl p-6 text-white text-center mb-4">
                <Zap className="w-8 h-8 mx-auto mb-2" />
                <h2 className="text-xl font-black mb-1">{t("subscriptionUi.freeTrialTitle")}</h2>
                <p className="text-white/80 text-sm mb-4">{t("subscriptionUi.freeTrialSubtitle")}</p>
                <Button onClick={() => handleSubscribe("monthly")} className="bg-white text-[#FF6B6B] hover:bg-white/90 py-5 px-8 rounded-xl font-bold" data-testid="free-trial-btn">
                  {t("subscriptionUi.startFreeTrial")}
                </Button>
              </div>
            )}

            {/* Pricing */}
            <div className="grid gap-3">
              <div className="bg-white rounded-2xl shadow-sm p-5 hover:border-[#FF6B6B] border-2 border-transparent transition-colors">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-[#2B2D42]">{t("subscriptionUi.monthly")}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-black text-[#2B2D42]">3,99</span>
                      <span className="text-[#8D99AE]">{t("subscriptionUi.perMonth")}</span>
                    </div>
                  </div>
                  <Button onClick={() => handleSubscribe("monthly")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-6" data-testid="subscribe-monthly-btn">
                    {t("subscriptionUi.subscribe")}
                  </Button>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm p-5 border-2 border-[#FF6B6B] relative">
                <div className="absolute -top-3 right-4 bg-[#FF6B6B] text-white text-xs font-bold px-3 py-1 rounded-full">{t("subscriptionUi.save37")}</div>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-[#2B2D42]">{t("subscriptionUi.annual")}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-black text-[#2B2D42]">29,99</span>
                      <span className="text-[#8D99AE]">{t("subscriptionUi.perYear")}</span>
                    </div>
                    <p className="text-xs text-[#8D99AE]">{t("subscriptionUi.onlyMonthly")}</p>
                  </div>
                  <Button onClick={() => handleSubscribe("annual")} className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl font-bold px-6" data-testid="subscribe-annual-btn">
                    {t("subscriptionUi.subscribe")}
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Municipality */}
        <div className="bg-[#2B2D42] rounded-2xl p-5 text-white mt-6">
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="w-5 h-5 text-[#FF6B6B]" />
            <h2 className="font-bold" style={{ fontFamily: 'Nunito, sans-serif' }}>{t("subscriptionUi.municipalities")}</h2>
          </div>
          <p className="text-white/70 text-sm leading-6 mb-4">{t("subscriptionUi.municipalitySubtitle")}</p>

          <div className="grid gap-3 sm:grid-cols-2 mb-4">
            {[
              { icon: Building2, text: t("subscriptionUi.municipalityFeatureDashboards") },
              { icon: ClipboardCheck, text: t("subscriptionUi.municipalityFeatureCleaning") },
              { icon: Sparkles, text: t("subscriptionUi.municipalityFeatureCustom") },
              { icon: Wrench, text: t("subscriptionUi.municipalityFeatureSupport") },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="rounded-xl bg-white/8 border border-white/10 px-3 py-3 text-sm text-white/85 flex items-start gap-3">
                <Icon className="w-4 h-4 mt-0.5 text-[#FF6B6B] shrink-0" />
                <span className="leading-5">{text}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="rounded-xl bg-white/8 border border-white/10 p-4">
              <p className="text-xs uppercase tracking-wide text-white/55 mb-1">{t("subscriptionUi.monthly")}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-black">75</span>
                <span className="text-white/70">{t("subscriptionUi.perMonth")}</span>
              </div>
            </div>
            <div className="rounded-xl bg-white/8 border border-white/10 p-4">
              <p className="text-xs uppercase tracking-wide text-white/55 mb-1">{t("subscriptionUi.annual")}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-black">1000</span>
                <span className="text-white/70">{t("subscriptionUi.perYear")}</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-white/8 border border-white/10 p-3 mb-3 text-xs text-white/80 space-y-2">
            <p>{t("subscriptionUi.municipalityAppStoreNote")}</p>
            <p>{t("subscriptionUi.municipalityBillingWarning")}</p>
            <p>{t("subscriptionUi.municipalityManualSetup")}</p>
          </div>

          <Button onClick={() => navigate("/dashboard/register")} variant="outline" className="w-full border-white/30 text-white hover:bg-white/10 rounded-xl font-bold" data-testid="municipality-subscribe-btn">
              {t("subscriptionUi.createMunicipalityDashboard")}
          </Button>
        </div>

        <p className="text-center text-xs text-[#8D99AE] mt-6">
          {t("subscriptionUi.paymentNote")}
        </p>
      </div>
    </div>
  );
}
