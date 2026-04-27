import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Download, ExternalLink, Image as ImageIcon, Smartphone } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import LegalLinksFooter from "../components/LegalLinksFooter";
import SocialShareButtons from "../components/SocialShareButtons";
import { useLanguage } from "../contexts/LanguageContext";
import { API, HOSTED_WEB_URL } from "../config";
import { formatTranslation } from "../utils/ranks";
import { shareWithNativeOrCopy } from "../utils/socialShare";
import { buildLocationImageUrl, buildLocationShareUrl } from "../utils/locationShare";

const FALLBACK_STORES = {
  app_store_url: "https://apps.apple.com/app/caca-radar/id000000000",
  play_store_url: "https://play.google.com/store/apps/details?id=com.cacaradar.app",
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
  const { t } = useLanguage();
  const [stores, setStores] = useState(FALLBACK_STORES);

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
      const city = searchParams.get("city") || "madrid";
      const barrio = searchParams.get("barrio") || "";
      return buildLocationShareUrl(city, barrio);
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
      return buildLocationImageUrl(city, barrio || "");
    }
    return "/share-example-es.png";
  }, [kind, searchParams]);
  const sharePayload = useMemo(() => ({
    title: contextTitle,
    text: `${t("shareUi.tagline")}\n\n${contextTitle}`,
    url: shareUrl,
    imageUrl: kind === "city-rankings" || kind === "barrio-rankings" || kind === "city-report" ? previewImageUrl : undefined,
  }), [contextTitle, kind, previewImageUrl, shareUrl, t]);

  const handleShare = async () => {
    try {
      await shareWithNativeOrCopy({
        ...sharePayload,
        onCopied: () => toast.success(t("mapUi.linkCopied")),
      });
    } catch {
      // noop
    }
  };

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
            <Button onClick={handleShare} variant="outline" className="w-full mt-4 rounded-xl border-[#FF6B6B]/30 text-[#FF6B6B] hover:bg-[#FF6B6B]/10">
              {t("mapUi.share")}
            </Button>
            <SocialShareButtons
              className="mt-3"
              prefix="download-share"
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
          </aside>
        </div>

        <footer className="mt-8">
          <LegalLinksFooter />
        </footer>
      </main>
    </div>
  );
}
