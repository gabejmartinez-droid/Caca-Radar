import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Star, MapPin, Filter, Bell, Crown, Zap, Building2, Landmark, Building, Mail } from "lucide-react";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LanguageSelector } from "../components/LanguageSelector";
import axios from "axios";
import { toast } from "sonner";

import { API } from "../config";
import { isCapacitorNative } from "../tokenManager";

const MUNICIPAL_CONTACT_HREF = "mailto:jefe@cacaradar.es?subject=Solicitud%20de%20cuenta%20municipal%20Caca%20Radar";

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

  const municipalPlans = useMemo(() => ([
    {
      id: "small",
      icon: Landmark,
      title: t("subscriptionUi.municipalSmallTitle"),
      population: t("subscriptionUi.municipalSmallPopulation"),
      price: t("subscriptionUi.municipalSmallPrice"),
      description: t("subscriptionUi.municipalSmallDescription"),
      features: [
        t("subscriptionUi.municipalFeatureVerifiedProfile"),
        t("subscriptionUi.municipalFeaturePublicReports"),
        t("subscriptionUi.municipalFeatureBasicDashboard"),
        t("subscriptionUi.municipalFeatureBasicMap"),
        t("subscriptionUi.municipalFeatureResolve"),
        t("subscriptionUi.municipalFeatureMonthlyExport"),
        t("subscriptionUi.municipalFeatureEmailSupport"),
      ],
      highlighted: false,
      tint: "from-[#F8F9FA] to-white",
      border: "border-[#8D99AE]/20",
      iconColor: "text-[#42A5F5]",
    },
    {
      id: "medium",
      icon: Building2,
      title: t("subscriptionUi.municipalMediumTitle"),
      population: t("subscriptionUi.municipalMediumPopulation"),
      price: t("subscriptionUi.municipalMediumPrice"),
      description: t("subscriptionUi.municipalMediumDescription"),
      features: [
        t("subscriptionUi.municipalFeatureEverythingSmall"),
        t("subscriptionUi.municipalFeatureStaffAccounts"),
        t("subscriptionUi.municipalFeatureBarrioFilters"),
        t("subscriptionUi.municipalFeatureVisibleStatuses"),
        t("subscriptionUi.municipalFeatureBasicAnalytics"),
        t("subscriptionUi.municipalFeatureCsvExports"),
        t("subscriptionUi.municipalFeatureReplyTemplates"),
        t("subscriptionUi.municipalFeatureMonthlyPdf"),
      ],
      highlighted: true,
      tint: "from-[#FF6B6B]/10 to-white",
      border: "border-[#FF6B6B]",
      iconColor: "text-[#FF6B6B]",
    },
    {
      id: "large",
      icon: Building,
      title: t("subscriptionUi.municipalLargeTitle"),
      population: t("subscriptionUi.municipalLargePopulation"),
      price: t("subscriptionUi.municipalLargePrice"),
      description: t("subscriptionUi.municipalLargeDescription"),
      features: [
        t("subscriptionUi.municipalFeatureEverythingMedium"),
        t("subscriptionUi.municipalFeatureTeams"),
        t("subscriptionUi.municipalFeatureAdvancedHeatmaps"),
        t("subscriptionUi.municipalFeaturePrioritySupport"),
        t("subscriptionUi.municipalFeatureCustomCategories"),
        t("subscriptionUi.municipalFeatureQuarterlyReports"),
        t("subscriptionUi.municipalFeatureCampaignTools"),
        t("subscriptionUi.municipalFeatureCustomOnboarding"),
      ],
      highlighted: false,
      tint: "from-[#2B2D42]/5 to-white",
      border: "border-[#2B2D42]/15",
      iconColor: "text-[#2B2D42]",
    },
  ]), [t]);

  const alreadySubscribed = user?.subscription_active;

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="subscription-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />{t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-8">
        <div className="max-w-lg mx-auto">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-[#FF6B6B] to-[#FF5252] rounded-2xl flex items-center justify-center mx-auto mb-3">
              <Star className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>{t("subscriptionUi.premiumTitle")}</h1>
            <p className="text-[#8D99AE] text-sm mt-1">{t("subscriptionUi.premiumSubtitle")}</p>
          </div>

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
        </div>

        <section className="mt-10 bg-[#2B2D42] rounded-[24px] p-6 md:p-8 text-white">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-3">
              <Building2 className="w-5 h-5 text-[#FF6B6B]" />
              <h2 className="text-2xl font-black" style={{ fontFamily: "Nunito, sans-serif" }}>{t("subscriptionUi.municipalAccountsTitle")}</h2>
            </div>
            <p className="text-white/82 text-sm md:text-base leading-7">{t("subscriptionUi.municipalAccountsSubtitle")}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-full bg-white/10 border border-white/10 px-3 py-1 text-xs text-white/80">{t("subscriptionUi.municipalAccountsSetupNote")}</span>
              <span className="rounded-full bg-[#FF6B6B]/15 border border-[#FF6B6B]/20 px-3 py-1 text-xs text-[#FFD5D5]">{t("subscriptionUi.municipalPilotNote")}</span>
            </div>
          </div>

          <div className="grid gap-4 mt-6 lg:grid-cols-3">
            {municipalPlans.map((plan) => {
              const Icon = plan.icon;
              return (
                <article
                  key={plan.id}
                  className={`relative flex h-full flex-col rounded-2xl border bg-gradient-to-b ${plan.tint} ${plan.border} p-5 text-[#2B2D42] shadow-sm`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-5 rounded-full bg-[#FF6B6B] px-3 py-1 text-xs font-bold text-white shadow-sm">
                      {t("subscriptionUi.mostCommonMunicipal")}
                    </div>
                  )}

                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className={`w-5 h-5 ${plan.iconColor}`} />
                        <h3 className="text-lg font-black" style={{ fontFamily: "Nunito, sans-serif" }}>{plan.title}</h3>
                      </div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#8D99AE]">
                        {t("subscriptionUi.municipalPopulationLabel")} · {plan.population}
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="text-3xl font-black text-[#2B2D42]">{plan.price}</div>
                  </div>

                  <p className="text-sm text-[#5C677D] leading-6 mb-4">{plan.description}</p>

                  <ul className="space-y-2.5 text-sm text-[#2B2D42] mb-5 flex-1">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2">
                        <Check className="w-4 h-4 mt-0.5 shrink-0 text-[#66BB6A]" />
                        <span className="leading-5">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-auto space-y-3">
                    <p className="text-xs text-[#8D99AE] leading-5">{t("subscriptionUi.municipalOnboardingContact")}</p>
                    <Button
                      asChild
                      className={`w-full rounded-xl font-bold ${plan.highlighted ? "bg-[#FF6B6B] hover:bg-[#FF5252] text-white" : "bg-[#2B2D42] hover:bg-[#23253A] text-white"}`}
                      data-testid={`municipal-plan-${plan.id}-cta`}
                    >
                      <a href={MUNICIPAL_CONTACT_HREF}>
                        <Mail className="w-4 h-4" />
                        {t("subscriptionUi.requestMunicipalAccess")}
                      </a>
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="mt-5 rounded-2xl border border-white/10 bg-white/6 p-4 md:p-5">
            <p className="text-sm text-white/85 leading-6">{t("subscriptionUi.municipalConfiguredIndividually")}</p>
            <p className="text-sm text-white/75 leading-6 mt-2">{t("subscriptionUi.municipalBillingContact")}</p>
          </div>
        </section>

        <p className="text-center text-xs text-[#8D99AE] mt-6">
          {t("subscriptionUi.paymentNote")}
        </p>
      </div>
    </div>
  );
}
