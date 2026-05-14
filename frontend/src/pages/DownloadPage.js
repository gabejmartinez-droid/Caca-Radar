import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Download, ExternalLink, Image as ImageIcon, Smartphone, Watch, Building2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import LegalLinksFooter from "../components/LegalLinksFooter";
import SocialShareButtons from "../components/SocialShareButtons";
import { useLanguage } from "../contexts/LanguageContext";
import { API, HOSTED_WEB_URL } from "../config";
import { formatTranslation } from "../utils/ranks";
import { getCurrentPlatform } from "../versionInfo";

const FALLBACK_STORES = {
  app_store_url: "https://apps.apple.com/app/caca-radar/id000000000",
  play_store_url: "https://play.google.com/store/apps/details?id=com.jefe.cacaradar",
};

function buildContextTitle(kind, params, t) {
  const prettify = (value) => String(value || "")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
  const city = prettify(params.get("city") || "");
  const barrio = prettify(params.get("barrio") || "");
  const listType = params.get("list_type") || "";
  const name = params.get("name") || "";

  if (kind === "city-report" && city) {
    return barrio
      ? formatTranslation(t, "downloadUi.cityReportWithBarrio", { city, barrio })
      : formatTranslation(t, "downloadUi.cityReportForCity", { city });
  }
  if (kind === "city-rankings") {
    return listType === "cleanest" ? t("downloadUi.cleanestCities") : t("downloadUi.dirtiestCities");
  }
  if (kind === "barrio-rankings" && city) {
    return formatTranslation(t, "downloadUi.barrioRankingsForCity", { city });
  }
  if (kind === "profile" && name) {
    return formatTranslation(t, "downloadUi.profileForName", { name });
  }
  if (kind === "report" && city) {
    return formatTranslation(t, "downloadUi.reportInCity", { city });
  }
  return t("downloadUi.sharedCard");
}

export default function DownloadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t, language } = useLanguage();
  const [stores, setStores] = useState(FALLBACK_STORES);
  const isIOSApp = getCurrentPlatform() === "ios";

  const kind = searchParams.get("kind") || "";

  useEffect(() => {
    let cancelled = false;

    const loadStoreLinks = async () => {
      try {
        const response = await fetch(`${API}/store-links`, { credentials: "include" });
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) {
          setStores({
            app_store_url: data.app_store_url || FALLBACK_STORES.app_store_url,
            play_store_url: data.play_store_url || FALLBACK_STORES.play_store_url,
          });
        }
      } catch {
        // fall back to configured defaults
      }
    };

    loadStoreLinks();
    return () => {
      cancelled = true;
    };
  }, []);

  const contextTitle = useMemo(() => buildContextTitle(kind, searchParams, t), [kind, searchParams, t]);
  const shareUrl = useMemo(() => {
    if (kind === "city-report") {
      const query = new URLSearchParams({ kind: "city-report", city: searchParams.get("city") || "madrid" });
      const barrio = searchParams.get("barrio");
      if (barrio) query.set("barrio", barrio);
      return `${HOSTED_WEB_URL}/api/share?${query.toString()}`;
    }
    return `${HOSTED_WEB_URL}/api/share?${searchParams.toString()}`;
  }, [kind, searchParams]);
  const previewImageUrl = useMemo(() => {
    if (kind === "city-rankings") {
      const listType = searchParams.get("list_type") || "dirtiest";
      return `${API}/rankings/cities/share-image?list_type=${encodeURIComponent(listType)}`;
    }
    if (kind === "barrio-rankings") {
      const city = searchParams.get("city") || "Madrid";
      return `${API}/rankings/barrios/share-image?city=${encodeURIComponent(city)}`;
    }
    if (kind === "city-report") {
      const city = searchParams.get("city") || "Madrid";
      const barrio = searchParams.get("barrio");
      return `${API}/city-reports/share-image.png?city=${encodeURIComponent(city)}${barrio ? `&barrio=${encodeURIComponent(barrio)}` : ""}`;
    }
    return "/share-example-es.png";
  }, [kind, searchParams]);
  const sharePayload = useMemo(() => ({
    title: contextTitle,
    text: `${t("shareUi.tagline")}\n\n${contextTitle}`,
    url: shareUrl,
    imageUrl: kind === "city-rankings" || kind === "barrio-rankings" || kind === "city-report" ? previewImageUrl : undefined,
  }), [contextTitle, kind, previewImageUrl, shareUrl, t]);
  const watchIntro = isIOSApp
    ? (language === "en"
        ? "Take Caca Radar to your wrist with the companion app for Apple Watch."
        : "Lleva Caca Radar en tu muñeca con el companion app para Apple Watch.")
    : t("downloadUi.watchIntro");

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="download-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-4xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold text-[#5C677D] mb-2">{t("shareUi.tagline")}</p>
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              {t("downloadUi.pageTitle")}
            </h1>
            <p className="text-[#5C677D] leading-7 mt-3">
              {t("downloadUi.pageIntro")}
            </p>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
            <div className="flex items-center gap-2 text-[#5C677D] mb-3">
              <ImageIcon className="w-4 h-4 text-[#FF6B6B]" />
              <span className="text-sm font-semibold">{t("downloadUi.sharedCardPreview")}</span>
            </div>
            <h2 className="text-2xl font-black text-[#2B2D42] mb-2">{contextTitle}</h2>
            <p className="text-sm text-[#8D99AE] mb-5">{t("downloadUi.previewNote")}</p>
            <div className="overflow-hidden rounded-2xl border border-[#8D99AE]/10 bg-[#F8F9FA]">
              <img
                src={previewImageUrl}
                alt={t("downloadUi.previewAlt")}
                className="block w-full h-auto"
              />
            </div>
            <SocialShareButtons
              className="mt-4"
              prefix="download-share"
              label={t("mapUi.share")}
              loadShareData={async () => sharePayload}
              onCopied={() => toast.success(t("mapUi.linkCopied"))}
            />
          </section>

          <aside className="space-y-6">
            <section className="bg-white rounded-2xl shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4">
                <Download className="w-5 h-5 text-[#42A5F5]" />
                <h2 className="text-lg font-bold text-[#2B2D42]">{t("downloadUi.downloadTitle")}</h2>
              </div>
              <p className="text-sm text-[#5C677D] mb-5">{t("downloadUi.downloadIntro")}</p>
              <div className="space-y-3">
                <a
                  href={stores.app_store_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-xl border border-[#8D99AE]/15 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
                >
                  <span className="flex items-center gap-3 font-semibold">
                    <Smartphone className="w-4 h-4 text-[#2B2D42]" />
                    {t("downloadUi.openAppStore")}
                  </span>
                  <ExternalLink className="w-4 h-4 text-[#8D99AE]" />
                </a>
                {!isIOSApp && (
                  <a
                    href={stores.play_store_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between rounded-xl border border-[#8D99AE]/15 px-4 py-3 text-[#2B2D42] hover:bg-[#F8F9FA]"
                  >
                    <span className="flex items-center gap-3 font-semibold">
                      <Smartphone className="w-4 h-4 text-[#2B2D42]" />
                      {t("downloadUi.openPlayStore")}
                    </span>
                    <ExternalLink className="w-4 h-4 text-[#8D99AE]" />
                  </a>
                )}
              </div>
            </section>

            <section className="bg-white rounded-2xl shadow-sm p-6">
              <h2 className="text-lg font-bold text-[#2B2D42] mb-3">{t("downloadUi.whyTitle")}</h2>
              <ul className="space-y-3 text-sm text-[#5C677D]">
                <li>{t("downloadUi.whyOne")}</li>
                <li>{t("downloadUi.whyTwo")}</li>
                <li>{t("downloadUi.whyThree")}</li>
              </ul>
            </section>

            <section className="bg-[#2B2D42] rounded-2xl shadow-sm p-6 text-white">
              <div className="flex items-center gap-2 mb-4">
                <Watch className="w-5 h-5 text-[#FF6B6B]" />
                <h2 className="text-lg font-bold">{t("downloadUi.watchTitle")}</h2>
              </div>
              <p className="text-sm text-white/75 leading-6 mb-4">{watchIntro}</p>
              <ul className="space-y-3 text-sm text-white/85">
                <li>{t("downloadUi.watchOne")}</li>
                <li>{t("downloadUi.watchTwo")}</li>
                <li>{t("downloadUi.watchThree")}</li>
              </ul>
            </section>

            {!isIOSApp && (
            <section className="bg-white rounded-2xl shadow-sm p-6 border border-[#2B2D42]/10">
              <div className="flex items-center gap-2 mb-4">
                <Building2 className="w-5 h-5 text-[#2B2D42]" />
                <h2 className="text-lg font-bold text-[#2B2D42]">{t("downloadUi.municipalTitle")}</h2>
              </div>
              <p className="text-sm text-[#5C677D] leading-6 mb-4">{t("downloadUi.municipalIntro")}</p>
              <ul className="space-y-3 text-sm text-[#5C677D] mb-5">
                <li>{t("downloadUi.municipalOne")}</li>
                <li>{t("downloadUi.municipalTwo")}</li>
                <li>{t("downloadUi.municipalThree")}</li>
              </ul>
              <Button
                onClick={() => navigate("/subscribe")}
                className="w-full rounded-xl bg-[#2B2D42] hover:bg-[#23253A] text-white font-bold"
                data-testid="download-municipal-cta"
              >
                {t("downloadUi.municipalCta")}
              </Button>
            </section>
            )}
          </aside>
        </div>

        <footer className="mt-8">
          <LegalLinksFooter />
        </footer>
      </main>
    </div>
  );
}
