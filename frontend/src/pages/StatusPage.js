import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Activity, CheckCircle2, AlertTriangle, RefreshCw, Server, Database, GitCommitHorizontal, Globe } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import LegalLinksFooter from "../components/LegalLinksFooter";
import { useLanguage } from "../contexts/LanguageContext";
import { API, HOSTED_WEB_URL } from "../config";

function StatusPill({ ok, children }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
        ok ? "bg-[#66BB6A]/10 text-[#2E7D32]" : "bg-[#FF6B6B]/10 text-[#C62828]"
      }`}
    >
      {ok ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
      {children}
    </span>
  );
}

function StatRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 border-b border-[#8D99AE]/10 last:border-b-0">
      <span className="text-sm text-[#5C677D]">{label}</span>
      <span className="text-sm font-semibold text-[#2B2D42] text-right break-all">{value}</span>
    </div>
  );
}

function formatDateTime(value, language, fallback) {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(language, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatRelativeUptime(value, t) {
  if (!value) return t("statusUi.notAvailable");
  const started = new Date(value);
  if (Number.isNaN(started.getTime())) return t("statusUi.notAvailable");
  const diffMs = Date.now() - started.getTime();
  if (diffMs < 0) return t("statusUi.notAvailable");

  const totalMinutes = Math.floor(diffMs / 60000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;

  const parts = [];
  if (days) parts.push(`${days}d`);
  if (hours) parts.push(`${hours}h`);
  if (!days && minutes) parts.push(`${minutes}m`);
  return parts.length ? parts.join(" ") : t("statusUi.lessThanMinute");
}

export default function StatusPage() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchStatus = async () => {
      setLoading(true);
      setError("");
      try {
        const [healthResponse, versionResponse] = await Promise.all([
          fetch(`${API}/health/deep`, { credentials: "include" }),
          fetch(`${API}/version`, { credentials: "include" }),
        ]);

        if (!healthResponse.ok || !versionResponse.ok) {
          throw new Error(t("statusUi.loadError"));
        }

        const [healthData, versionData] = await Promise.all([
          healthResponse.json(),
          versionResponse.json(),
        ]);

        if (!cancelled) {
          setHealth(healthData);
          setVersion(versionData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || t("statusUi.loadError"));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchStatus();
    return () => {
      cancelled = true;
    };
  }, [t]);

  const runtime = version?.runtime || health?.runtime || {};
  const appVersions = runtime.app_versions || {};
  const allChecksPassing = useMemo(() => {
    if (!health) return false;
    return Boolean(health.database && health.reports_readable && health.users_readable);
  }, [health]);

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="status-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-4xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <Activity className="w-6 h-6 text-[#42A5F5]" />
                <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                  {t("statusUi.title")}
                </h1>
              </div>
              <p className="text-[#5C677D] leading-7 max-w-2xl">
                {t("statusUi.intro")}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
              className="border-[#8D99AE]/20"
              data-testid="status-refresh-btn"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {t("statusUi.refresh")}
            </Button>
          </div>

          <div className="mt-4 rounded-2xl bg-[#F8F9FA] px-4 py-3 text-sm text-[#5C677D]">
            {t("legalUi.nonOfficialDisclaimer")}
          </div>
        </section>

        {loading ? (
          <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
            <p className="text-[#5C677D]">{t("statusUi.loading")}</p>
          </section>
        ) : error ? (
          <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
            <StatusPill ok={false}>{t("statusUi.queryError")}</StatusPill>
            <p className="mt-4 text-[#5C677D]">{error}</p>
          </section>
        ) : (
          <div className="space-y-6">
            <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
              <div className="flex flex-wrap items-center gap-3 mb-5">
                <StatusPill ok={health?.status === "ok" && allChecksPassing}>
                  {health?.status === "ok" && allChecksPassing ? t("statusUi.operational") : t("statusUi.degraded")}
                </StatusPill>
                <StatusPill ok={Boolean(health?.database)}>{t("statusUi.database")}</StatusPill>
                <StatusPill ok={Boolean(health?.reports_readable)}>{t("statusUi.reportReads")}</StatusPill>
                <StatusPill ok={Boolean(health?.users_readable)}>{t("statusUi.userReads")}</StatusPill>
                <StatusPill ok={Boolean(health?.production_db_safe)}>{t("statusUi.productionSafe")}</StatusPill>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl bg-[#F8F9FA] p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Server className="w-5 h-5 text-[#42A5F5]" />
                    <h2 className="text-lg font-bold text-[#2B2D42]">{t("statusUi.runtimeTitle")}</h2>
                  </div>
                  <StatRow label={t("statusUi.environment")} value={runtime.environment || t("statusUi.notAvailable")} />
                  <StatRow label={t("statusUi.currentUptime")} value={formatRelativeUptime(runtime.started_at, t)} />
                  <StatRow label={t("statusUi.startedAt")} value={formatDateTime(runtime.started_at, language, t("statusUi.notAvailable"))} />
                  <StatRow label={t("statusUi.deployedCommit")} value={runtime.commit || "unknown"} />
                </div>

                <div className="rounded-2xl bg-[#F8F9FA] p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Database className="w-5 h-5 text-[#66BB6A]" />
                    <h2 className="text-lg font-bold text-[#2B2D42]">{t("statusUi.databaseTitle")}</h2>
                  </div>
                  <StatRow label={t("statusUi.host")} value={runtime.mongo_host || t("statusUi.notAvailable")} />
                  <StatRow label={t("statusUi.logicalName")} value={runtime.db_name || t("statusUi.notAvailable")} />
                  <StatRow label={t("statusUi.localMongo")} value={runtime.mongo_is_local ? t("statusUi.yes") : t("statusUi.no")} />
                  <StatRow label={t("statusUi.productionSafe")} value={health?.production_db_safe ? t("statusUi.yes") : t("statusUi.no")} />
                </div>
              </div>
            </section>

            <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
              <div className="flex items-center gap-2 mb-4">
                <GitCommitHorizontal className="w-5 h-5 text-[#FF6B6B]" />
                <h2 className="text-lg font-bold text-[#2B2D42]">{t("statusUi.publishedVersions")}</h2>
              </div>
              <div className="rounded-2xl bg-[#F8F9FA] p-5">
                <StatRow label="Web" value={appVersions.web || t("statusUi.notAvailable")} />
                <StatRow
                  label="iOS"
                  value={appVersions.ios ? `${appVersions.ios.version} (${appVersions.ios.build})` : t("statusUi.notAvailable")}
                />
                <StatRow
                  label="Android"
                  value={appVersions.android ? `${appVersions.android.version} (${appVersions.android.build})` : t("statusUi.notAvailable")}
                />
                <StatRow label="Backend" value={runtime.backend_version || t("statusUi.notAvailable")} />
              </div>
            </section>

            <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-5 h-5 text-[#FFA726]" />
                <h2 className="text-lg font-bold text-[#2B2D42]">{t("statusUi.publicChecks")}</h2>
              </div>
              <div className="rounded-2xl bg-[#F8F9FA] p-5 space-y-3 text-sm text-[#5C677D]">
                <p>
                  {t("statusUi.baseApi")}: <a className="text-[#FF6B6B] font-medium" href={`${HOSTED_WEB_URL}/api/health`} target="_blank" rel="noreferrer">{HOSTED_WEB_URL}/api/health</a>
                </p>
                <p>
                  {t("statusUi.deepHealth")}: <a className="text-[#FF6B6B] font-medium" href={`${HOSTED_WEB_URL}/api/health/deep`} target="_blank" rel="noreferrer">{HOSTED_WEB_URL}/api/health/deep</a>
                </p>
                <p>
                  {t("statusUi.versionMetadata")}: <a className="text-[#FF6B6B] font-medium" href={`${HOSTED_WEB_URL}/api/version`} target="_blank" rel="noreferrer">{HOSTED_WEB_URL}/api/version</a>
                </p>
                <p className="text-[#8D99AE]">
                  {t("statusUi.publicChecksNote")}
                </p>
              </div>
            </section>

            <footer className="space-y-4 pb-2">
              <LegalLinksFooter />
            </footer>
          </div>
        )}
      </main>
    </div>
  );
}
