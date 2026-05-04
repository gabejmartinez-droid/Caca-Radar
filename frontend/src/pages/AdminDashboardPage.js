import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Users, FileText, Eye, AlertTriangle, DollarSign, TrendingUp, Search, ChevronLeft, ChevronRight, Loader2, LogOut, Image, CheckCircle, XCircle, Globe, Smartphone, MonitorSmartphone, Clock3, Skull, Building2, MapPin, Flag, Archive, RefreshCw, Camera, BarChart3 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import MunicipalityMapCard from "../components/MunicipalityMapCard";
import { toast } from "sonner";
import axios from "axios";

import { API } from "../config";

const FLAG_REASON_LABELS = {
  license_plate: "Matrícula visible",
  face: "Cara visible",
  name: "Nombre visible",
  personal_info: "Info personal",
  inappropriate: "Contenido inapropiado",
  spam: "Spam / Falso",
  other: "Otro",
};

function StatCard({ icon: Icon, label, value, sub, color = "#FF6B6B" }) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <span className="text-xs text-[#8D99AE] font-medium">{label}</span>
      </div>
      <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
      {sub && <p className="text-xs text-[#8D99AE] mt-0.5">{sub}</p>}
    </div>
  );
}

function formatDateTime(value) {
  if (!value) return "Nunca";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Nunca";
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function PlatformBadge({ platform }) {
  const normalized = (platform || "unknown").toLowerCase();
  const config = normalized === "ios"
    ? { label: "iPhone", Icon: Smartphone, color: "#42A5F5", bg: "#42A5F515" }
    : normalized === "android"
      ? { label: "Android", Icon: Smartphone, color: "#66BB6A", bg: "#66BB6A15" }
      : normalized === "web"
        ? { label: "Web", Icon: Globe, color: "#8D99AE", bg: "#8D99AE15" }
        : normalized === "native"
          ? { label: "Nativo", Icon: MonitorSmartphone, color: "#FFA726", bg: "#FFA72615" }
          : { label: "Desconocido", Icon: MonitorSmartphone, color: "#8D99AE", bg: "#8D99AE15" };

  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold" style={{ color: config.color, backgroundColor: config.bg }}>
      <config.Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function municipalityLabel(municipality) {
  if (!municipality) return "Selecciona un municipio";
  return municipality.province
    ? `${municipality.municipality_name} · ${municipality.province}`
    : municipality.municipality_name;
}

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("overview");
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [userDrafts, setUserDrafts] = useState({});
  const [userTotal, setUserTotal] = useState(0);
  const [userPage, setUserPage] = useState(0);
  const [userSearch, setUserSearch] = useState("");
  const [savingUserId, setSavingUserId] = useState(null);
  const [violations, setViolations] = useState([]);
  const [violationTotal, setViolationTotal] = useState(0);
  const [photoApprovals, setPhotoApprovals] = useState([]);
  const [photoApprovalTotal, setPhotoApprovalTotal] = useState(0);
  const [photoApprovalPage, setPhotoApprovalPage] = useState(0);
  const [selectedPhotoApprovalIds, setSelectedPhotoApprovalIds] = useState([]);
  const [photoApprovalLoading, setPhotoApprovalLoading] = useState(false);
  const [recentReports, setRecentReports] = useState([]);
  const [reportTotal, setReportTotal] = useState(0);
  const [reportPage, setReportPage] = useState(0);
  const [municipalityDashboards, setMunicipalityDashboards] = useState([]);
  const [selectedMunicipality, setSelectedMunicipality] = useState("");
  const [municipalityDashboard, setMunicipalityDashboard] = useState(null);
  const [municipalityLoading, setMunicipalityLoading] = useState(false);
  const [municipalityView, setMunicipalityView] = useState("map");
  const [municipalityReportFilter, setMunicipalityReportFilter] = useState("active");
  const [municipalityReportPage, setMunicipalityReportPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/dashboard`, { withCredentials: true });
      setDashboard(data);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        navigate("/admin/login");
      } else {
        toast.error("Error cargando datos");
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const fetchUsers = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/users?skip=${userPage * 20}&limit=20&search=${encodeURIComponent(userSearch)}`, { withCredentials: true });
      setUsers(data.users);
      setUserTotal(data.total);
      setUserDrafts((prev) => {
        const next = { ...prev };
        for (const user of data.users || []) {
          const draftKey = user.id || user.email;
          if (!draftKey) continue;
          next[draftKey] = {
            accountType: user.account_type || "standard",
            municipalityName: user.municipality_name || "",
            municipalityProvince: user.municipality_province || "",
          };
        }
        return next;
      });
    } catch { toast.error("Error cargando usuarios"); }
  }, [userPage, userSearch]);

  const updateUserDraft = useCallback((userId, patch) => {
    setUserDrafts((prev) => ({
      ...prev,
      [userId]: {
        ...(prev[userId] || {}),
        ...patch,
      },
    }));
  }, []);

  const handleSaveUserAccountType = useCallback(async (user) => {
    const draftKey = user.id || user.email;
    const draft = userDrafts[draftKey];
    if (!draft || !draftKey) return;
    if (draft.accountType === "municipal_worker" && !draft.municipalityName.trim()) {
      toast.error("Asigna un municipio antes de guardar.");
      return;
    }
    setSavingUserId(draftKey);
    try {
      const { data } = await axios.put(
        `${API}/admin/users/${draftKey}/account-type`,
        {
          account_type: draft.accountType,
          municipality_name: draft.accountType === "municipal_worker" ? draft.municipalityName.trim() : null,
          municipality_province: draft.accountType === "municipal_worker" ? (draft.municipalityProvince || "").trim() : null,
        },
        { withCredentials: true }
      );
      setUsers((prev) => prev.map((entry) => (
        (entry.id || entry.email) === draftKey
          ? {
              ...entry,
              account_type: data.user?.account_type || draft.accountType,
              municipality_name: data.user?.municipality_name ?? (draft.accountType === "municipal_worker" ? draft.municipalityName.trim() : null),
              municipality_province: data.user?.municipality_province ?? (draft.accountType === "municipal_worker" ? (draft.municipalityProvince || "").trim() : null),
            }
          : entry
      )));
      setUserDrafts((prev) => ({
        ...prev,
        [draftKey]: {
          accountType: data.user?.account_type || draft.accountType,
          municipalityName: data.user?.municipality_name || "",
          municipalityProvince: data.user?.municipality_province || "",
        },
      }));
      toast.success("Tipo de cuenta actualizado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "No pudimos actualizar el tipo de cuenta");
    } finally {
      setSavingUserId(null);
    }
  }, [userDrafts]);

  const fetchViolations = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/photo-violations`, { withCredentials: true });
      setViolations(data.violations);
      setViolationTotal(data.total);
    } catch { toast.error("Error cargando violaciones"); }
  }, []);

  const fetchPhotoApprovals = useCallback(async () => {
    setPhotoApprovalLoading(true);
    try {
      const { data } = await axios.get(
        `${API}/admin/photo-approvals?skip=${photoApprovalPage * 100}&limit=100`,
        { withCredentials: true }
      );
      const approvals = data.approvals || [];
      setPhotoApprovals(approvals);
      setPhotoApprovalTotal(data.total || 0);
      setSelectedPhotoApprovalIds((prev) => prev.filter((id) => approvals.some((item) => item.id === id)));
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        navigate("/admin/login");
      } else {
        toast.error("Error cargando aprobaciones de fotos");
      }
    } finally {
      setPhotoApprovalLoading(false);
    }
  }, [navigate, photoApprovalPage]);

  const fetchRecentReports = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/recent-reports?skip=${reportPage * 100}&limit=100`, { withCredentials: true });
      setRecentReports(data.reports);
      setReportTotal(data.total);
    } catch {
      toast.error("Error cargando reportes recientes");
    }
  }, [reportPage]);

  const fetchMunicipalityDashboards = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/municipalities`, { withCredentials: true });
      const options = data.municipalities || [];
      setMunicipalityDashboards(options);
      setSelectedMunicipality((current) => {
        if (current && options.some((item) => item.municipality_name === current)) {
          return current;
        }
        return options[0]?.municipality_name || "";
      });
    } catch {
      toast.error("Error cargando dashboards municipales");
    }
  }, []);

  const fetchMunicipalityDashboard = useCallback(async () => {
    if (!selectedMunicipality) {
      setMunicipalityDashboard(null);
      return;
    }
    setMunicipalityLoading(true);
    try {
      const params = new URLSearchParams({
        municipality: selectedMunicipality,
        status: municipalityReportFilter,
        page: String(municipalityReportPage),
        limit: "20",
      });
      const { data } = await axios.get(`${API}/admin/municipality-dashboard?${params.toString()}`, { withCredentials: true });
      setMunicipalityDashboard(data);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        navigate("/admin/login");
      } else {
        toast.error(err.response?.data?.detail || "Error cargando el dashboard municipal");
      }
    } finally {
      setMunicipalityLoading(false);
    }
  }, [municipalityReportFilter, municipalityReportPage, navigate, selectedMunicipality]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  useEffect(() => {
    if (tab === "users") fetchUsers();
    if (tab === "violations") fetchViolations();
    if (tab === "photoApprovals") fetchPhotoApprovals();
    if (tab === "reports") fetchRecentReports();
    if (tab === "municipalities") fetchMunicipalityDashboards();
  }, [fetchMunicipalityDashboards, fetchPhotoApprovals, fetchUsers, fetchViolations, fetchRecentReports, tab]);

  useEffect(() => {
    if (tab === "municipalities" && selectedMunicipality) {
      fetchMunicipalityDashboard();
    }
  }, [fetchMunicipalityDashboard, selectedMunicipality, tab]);

  const handleModerate = async (reportId, action) => {
    try {
      await axios.post(`${API}/admin/moderate/${reportId}`, { action }, { withCredentials: true });
      toast.success(`Reporte ${action === "hide" ? "ocultado" : action === "restore" ? "restaurado" : "flags descartados"}`);
      fetchViolations();
      fetchDashboard();
    } catch { toast.error("Error al moderar"); }
  };

  const handleLogout = async () => {
    await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    navigate("/admin/login");
  };

  const togglePhotoApprovalSelection = useCallback((reportId) => {
    setSelectedPhotoApprovalIds((prev) => (
      prev.includes(reportId) ? prev.filter((id) => id !== reportId) : [...prev, reportId]
    ));
  }, []);

  const toggleAllPhotoApprovals = useCallback(() => {
    const visibleIds = (photoApprovals || []).map((item) => item.id);
    if (!visibleIds.length) return;
    setSelectedPhotoApprovalIds((prev) => (
      visibleIds.every((id) => prev.includes(id)) ? prev.filter((id) => !visibleIds.includes(id)) : visibleIds
    ));
  }, [photoApprovals]);

  const handlePhotoApprovalModeration = useCallback(async (action, ids = null) => {
    const reportIds = Array.isArray(ids) ? ids : selectedPhotoApprovalIds;
    if (!reportIds.length) {
      toast.error("Selecciona al menos una foto");
      return;
    }

    setPhotoApprovalLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/admin/photo-approvals/moderate`,
        { action, report_ids: reportIds },
        { withCredentials: true }
      );
      toast.success(data.message || (action === "approve" ? "Fotos aprobadas" : "Reportes eliminados"));
      setSelectedPhotoApprovalIds((prev) => prev.filter((id) => !reportIds.includes(id)));
      await Promise.all([fetchPhotoApprovals(), fetchDashboard(), fetchRecentReports()]);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error moderando fotos");
    } finally {
      setPhotoApprovalLoading(false);
    }
  }, [fetchDashboard, fetchPhotoApprovals, fetchRecentReports, selectedPhotoApprovalIds]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#FF6B6B]" />
      </div>
    );
  }

  const d = dashboard;

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="admin-dashboard">
      {/* Header */}
      <div className="bg-[#2B2D42] text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-[#FF6B6B]" />
          <span className="font-bold text-sm">Admin Panel</span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="text-white/60 hover:text-white hover:bg-white/10" data-testid="admin-logout">
          <LogOut className="w-4 h-4 mr-1" /> Salir
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#8D99AE]/10 bg-white">
        {[
          { id: "overview", label: "Resumen", icon: TrendingUp },
          { id: "municipalities", label: "Municipios", icon: Building2 },
          { id: "reports", label: "Reportes", icon: FileText },
          { id: "users", label: "Usuarios", icon: Users },
          { id: "photoApprovals", label: "Fotos", icon: Image },
          { id: "violations", label: "Violaciones", icon: AlertTriangle },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5 border-b-2 transition-colors ${
              tab === id ? "border-[#FF6B6B] text-[#FF6B6B]" : "border-transparent text-[#8D99AE]"
            }`}
            data-testid={`admin-tab-${id}`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      <div className="max-w-6xl mx-auto px-4 py-5 pb-20">
        {tab === "overview" && d && (
          <>
            {/* User Stats */}
            <h2 className="text-sm font-bold text-[#2B2D42] mb-3">Usuarios</h2>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <StatCard icon={Users} label="Total usuarios" value={d.users.total} sub={`+${d.users.new_7d} esta semana`} />
              <StatCard icon={Users} label="Premium" value={d.users.premium} sub={`${d.users.conversion_rate}% conversión`} color="#66BB6A" />
              <StatCard icon={Users} label="Gratuitos" value={d.users.free} />
              <StatCard icon={TrendingUp} label="Nuevos (30d)" value={d.users.new_30d} color="#FFA726" />
            </div>

            {/* Subscription Stats */}
            <h2 className="text-sm font-bold text-[#2B2D42] mb-3">Suscripciones</h2>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <StatCard icon={DollarSign} label="Ingresos est./mes" value={`€${d.subscriptions.est_monthly_revenue}`} color="#66BB6A" />
              <StatCard icon={Users} label="Mensuales" value={d.subscriptions.monthly} />
              <StatCard icon={Users} label="Anuales" value={d.subscriptions.annual} />
              <StatCard icon={Users} label="Municipios activos" value={d.subscriptions.municipality_active} sub={`de ${d.subscriptions.municipality_total} total`} color="#FFA726" />
            </div>

            {/* Report Stats */}
            <h2 className="text-sm font-bold text-[#2B2D42] mb-3">Reportes</h2>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <StatCard icon={FileText} label="Total" value={d.reports.total} />
              <StatCard icon={Eye} label="Activos" value={d.reports.active} color="#66BB6A" />
              <StatCard icon={AlertTriangle} label="Marcados" value={d.reports.flagged} color="#FF5252" />
              <StatCard icon={FileText} label="Últimos 7d" value={d.reports.last_7d} sub={`${d.reports.last_30d} en 30d`} color="#FFA726" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <StatCard icon={TrendingUp} label="Frescos" value={d.reports.fresh} sub="≤ 24h" color="#66BB6A" />
              <StatCard icon={Clock3} label="Antiguos" value={d.reports.old} sub="1–7 días" color="#FFA726" />
              <StatCard icon={Skull} label="Fósiles" value={d.reports.fossil} sub="> 7 días" color="#FF5252" />
            </div>
          </>
        )}

        {tab === "municipalities" && (
          <>
            <div className="bg-white rounded-2xl shadow-sm p-4 mb-4">
              <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
                <div>
                  <h2 className="text-base font-bold text-[#2B2D42]">Dashboards municipales</h2>
                  <p className="text-sm text-[#8D99AE]">
                    Selecciona un municipio activo para ver su panel con el mismo alcance que tiene ese ayuntamiento.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    fetchMunicipalityDashboards();
                    fetchMunicipalityDashboard();
                  }}
                >
                  <RefreshCw className="w-4 h-4 mr-2" /> Actualizar
                </Button>
              </div>

              <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px]">
                <div>
                  <label className="text-xs font-bold text-[#8D99AE] mb-2 block">Municipio activo</label>
                  <Select
                    value={selectedMunicipality}
                    onValueChange={(value) => {
                      setSelectedMunicipality(value);
                      setMunicipalityReportPage(1);
                      setMunicipalityReportFilter("active");
                      setMunicipalityView("map");
                    }}
                  >
                    <SelectTrigger className="bg-[#F8F9FA] border-0 h-11 rounded-xl">
                      <SelectValue placeholder="Selecciona un municipio" />
                    </SelectTrigger>
                    <SelectContent>
                      {municipalityDashboards.map((municipality) => (
                        <SelectItem key={municipality.municipality_name} value={municipality.municipality_name}>
                          {municipalityLabel(municipality)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="bg-[#F8F9FA] rounded-xl px-4 py-3">
                  <p className="text-xs font-bold text-[#8D99AE]">Dashboards activos</p>
                  <p className="text-2xl font-black text-[#2B2D42]">{municipalityDashboards.length}</p>
                </div>
              </div>
            </div>

            {!municipalityDashboards.length && !municipalityLoading && (
              <div className="bg-white rounded-2xl shadow-sm p-8 text-center">
                <Building2 className="w-10 h-10 text-[#8D99AE] mx-auto mb-3" />
                <p className="text-[#2B2D42] font-bold mb-1">No hay dashboards municipales activos</p>
                <p className="text-sm text-[#8D99AE]">Cuando un municipio tenga acceso activo, aparecerá aquí para revisión admin.</p>
              </div>
            )}

            {municipalityLoading && (
              <div className="bg-white rounded-2xl shadow-sm p-10 flex items-center justify-center">
                <Loader2 className="w-7 h-7 animate-spin text-[#FF6B6B]" />
              </div>
            )}

            {!municipalityLoading && municipalityDashboard && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                  {[
                    { label: "Total reportes", value: municipalityDashboard.stats?.total_reports, icon: MapPin, color: "#FF6B6B" },
                    { label: "Activos", value: municipalityDashboard.stats?.active_reports, icon: Eye, color: "#FFA726" },
                    { label: "Reportados", value: municipalityDashboard.stats?.flagged_reports, icon: Flag, color: "#FF5252" },
                    { label: "Archivados", value: municipalityDashboard.stats?.archived_reports, icon: Archive, color: "#66BB6A" },
                    { label: "Últimos 7 días", value: municipalityDashboard.stats?.recent_reports_7d, icon: BarChart3, color: "#42A5F5" },
                    { label: "Flags pendientes", value: municipalityDashboard.stats?.pending_flags, icon: AlertTriangle, color: "#FF5252" },
                  ].map(({ label, value, icon, color }) => (
                    <StatCard key={label} icon={icon} label={label} value={value ?? 0} color={color} />
                  ))}
                </div>

                <div className="flex gap-2 mb-4 flex-wrap">
                  {[
                    { id: "map", label: "Mapa" },
                    { id: "reports", label: "Reportes" },
                    { id: "photos", label: `Fotos (${municipalityDashboard.photo_reviews?.length || 0})` },
                    { id: "flags", label: `Flags (${municipalityDashboard.flags?.length || 0})` },
                  ].map((view) => (
                    <Button
                      key={view.id}
                      size="sm"
                      variant={municipalityView === view.id ? "default" : "outline"}
                      className={municipalityView === view.id ? "bg-[#2B2D42]" : ""}
                      onClick={() => setMunicipalityView(view.id)}
                    >
                      {view.label}
                    </Button>
                  ))}
                </div>

                {municipalityView === "map" && (
                  <MunicipalityMapCard
                    mapData={municipalityDashboard.map}
                    title={`Mapa de ${municipalityDashboard.municipality}`}
                    subtitle="Vista admin reflejada del mapa municipal activo."
                  />
                )}

                {municipalityView === "reports" && (
                  <>
                    <div className="flex gap-2 mb-4 flex-wrap">
                      {[
                        { id: "active", label: "Activos" },
                        { id: "flagged", label: "Reportados" },
                        { id: "archived", label: "Archivados" },
                      ].map((filter) => (
                        <Button
                          key={filter.id}
                          size="sm"
                          variant={municipalityReportFilter === filter.id ? "default" : "outline"}
                          className={municipalityReportFilter === filter.id ? "bg-[#2B2D42]" : ""}
                          onClick={() => {
                            setMunicipalityReportFilter(filter.id);
                            setMunicipalityReportPage(1);
                          }}
                        >
                          {filter.label}
                        </Button>
                      ))}
                    </div>

                    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-[#F8F9FA] border-b">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Ubicación</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Contribuidor</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Fecha</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Votos</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Flags</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Estado</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {(municipalityDashboard.reports?.reports || []).length === 0 ? (
                              <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-[#8D99AE]">No hay reportes</td>
                              </tr>
                            ) : (municipalityDashboard.reports?.reports || []).map((report) => (
                              <tr key={report.id} className="hover:bg-[#F8F9FA]">
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    {report.photo_url ? (
                                      <img src={`${API}/files/${report.photo_url}`} alt="" className="w-8 h-8 rounded object-cover" />
                                    ) : null}
                                    <span className="text-xs text-[#2B2D42]">
                                      {report.latitude?.toFixed?.(4)}, {report.longitude?.toFixed?.(4)}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="text-xs">
                                    <p className="font-bold text-[#2B2D42]">{report.contributor_name || "Anónimo"}</p>
                                    <p className="text-[#8D99AE]">{report.contributor_rank || "Sin rango"}</p>
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-xs text-[#8D99AE]">{formatDateTime(report.created_at)}</td>
                                <td className="px-4 py-3 text-xs">
                                  <span className="text-[#66BB6A]">{report.upvotes || 0}</span>
                                  <span className="text-[#8D99AE] mx-1">/</span>
                                  <span className="text-[#FF5252]">{report.downvotes || 0}</span>
                                </td>
                                <td className="px-4 py-3 text-xs font-bold text-[#FF5252]">{report.flag_count || 0}</td>
                                <td className="px-4 py-3">
                                  {report.flagged ? (
                                    <Badge variant="destructive" className="text-xs">Reportado</Badge>
                                  ) : report.archived ? (
                                    <Badge variant="secondary" className="text-xs">Archivado</Badge>
                                  ) : (
                                    <Badge className="text-xs bg-[#66BB6A]">Activo</Badge>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="flex justify-between items-center px-4 py-3 border-t">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={(municipalityDashboard.reports?.page || 1) <= 1}
                          onClick={() => setMunicipalityReportPage((page) => Math.max(1, page - 1))}
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </Button>
                        <span className="text-xs text-[#8D99AE]">
                          Pág {municipalityDashboard.reports?.page || 1} de {Math.max(1, municipalityDashboard.reports?.pages || 1)}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={(municipalityDashboard.reports?.page || 1) >= Math.max(1, municipalityDashboard.reports?.pages || 1)}
                          onClick={() => setMunicipalityReportPage((page) => page + 1)}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </>
                )}

                {municipalityView === "photos" && (
                  <div className="space-y-4">
                    {(municipalityDashboard.photo_reviews || []).length === 0 ? (
                      <div className="bg-white rounded-2xl shadow-sm p-8 text-center text-[#8D99AE]">
                        No hay revisiones de foto pendientes.
                      </div>
                    ) : (municipalityDashboard.photo_reviews || []).map((review, index) => (
                      <div key={review.report?.id || index} className="bg-white rounded-xl p-4 shadow-sm">
                        <div className="flex items-start gap-3 mb-3">
                          {review.report?.photo_url ? (
                            <img src={`${API}/files/${review.report.photo_url}`} alt="Foto reportada" className="w-20 h-20 object-cover rounded-lg" />
                          ) : (
                            <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center">
                              <Camera className="w-6 h-6 text-[#8D99AE]" />
                            </div>
                          )}
                          <div className="min-w-0 flex-1">
                            <p className="font-bold text-[#2B2D42] mb-1">{review.report?.contributor_name || "Anónimo"}</p>
                            <p className="text-xs text-[#8D99AE] mb-2">{formatDateTime(review.report?.created_at)}</p>
                            <div className="flex flex-wrap gap-2">
                              {(review.flags || []).map((flag, flagIndex) => (
                                <span key={`${review.report?.id || index}-${flagIndex}`} className="text-[10px] px-2 py-1 rounded-full font-bold bg-[#FFE8E8] text-[#FF5252]">
                                  {FLAG_REASON_LABELS[flag.reason] || flag.reason}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {municipalityView === "flags" && (
                  <div className="space-y-4">
                    {(municipalityDashboard.flags || []).length === 0 ? (
                      <div className="bg-white rounded-2xl shadow-sm p-8 text-center text-[#8D99AE]">
                        No hay flags pendientes.
                      </div>
                    ) : (municipalityDashboard.flags || []).map((flag, index) => (
                      <div key={`${flag.report_id}-${index}`} className="bg-white rounded-xl p-4 shadow-sm">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="font-bold text-[#2B2D42]">{FLAG_REASON_LABELS[flag.reason] || flag.reason}</p>
                            <p className="text-xs text-[#8D99AE]">{formatDateTime(flag.created_at)}</p>
                            <p className="text-xs text-[#8D99AE]">
                              {flag.report?.latitude?.toFixed?.(4)}, {flag.report?.longitude?.toFixed?.(4)}
                            </p>
                          </div>
                          {flag.report?.photo_url ? (
                            <img src={`${API}/files/${flag.report.photo_url}`} alt="Flag" className="w-14 h-14 object-cover rounded-lg" />
                          ) : (
                            <div className="w-14 h-14 bg-gray-100 rounded-lg flex items-center justify-center">
                              <Image className="w-5 h-5 text-[#8D99AE]" />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}

        {tab === "reports" && (
          <>
            <p className="text-xs text-[#8D99AE] mb-3">{reportTotal} reportes totales · 100 por página</p>
            <div className="space-y-3">
              {recentReports.map((report, i) => (
                <div key={report.id || i} className="bg-white rounded-xl p-4 shadow-sm" data-testid={`recent-report-${i}`}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="min-w-0">
                      <p className="font-bold text-[#2B2D42] truncate">{report.reporter?.display_name || report.contributor_name || "Anónimo"}</p>
                      <p className="text-[11px] text-[#8D99AE] truncate">{report.reporter?.email || "Sin email"}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-[11px] font-bold text-[#2B2D42]">{formatDateTime(report.created_at)}</p>
                      <p className="text-[10px] text-[#8D99AE]">{report.id?.slice(0, 8)}...</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-[#42A5F5]/10 text-[#42A5F5]">
                      {report.reporter?.role || "user"}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-[#8D99AE]/10 text-[#8D99AE]">
                      {report.municipality || "Sin municipio"}{report.barrio ? ` · ${report.barrio}` : ""}
                    </span>
                    {report.flagged && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-600">Marcado</span>
                    )}
                    {report.archived && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-gray-100 text-gray-600">Archivado</span>
                    )}
                  </div>
                  <p className="text-xs text-[#2B2D42] mb-1">
                    <span className="font-bold">Rango:</span> {report.contributor_rank || "Sin rango"}
                  </p>
                  <p className="text-xs text-[#2B2D42] mb-1">
                    <span className="font-bold">Coords:</span> {typeof report.latitude === "number" ? report.latitude.toFixed(5) : "?"}, {typeof report.longitude === "number" ? report.longitude.toFixed(5) : "?"}
                  </p>
                  {report.description ? (
                    <p className="text-xs text-[#8D99AE] line-clamp-3">{report.description}</p>
                  ) : (
                    <p className="text-xs text-[#8D99AE] italic">Sin descripción</p>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center mt-4">
              <Button size="sm" variant="outline" disabled={reportPage === 0} onClick={() => setReportPage(p => p - 1)} data-testid="reports-prev">
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-xs text-[#8D99AE]">Pág {reportPage + 1} de {Math.max(1, Math.ceil(reportTotal / 100))}</span>
              <Button size="sm" variant="outline" disabled={(reportPage + 1) * 100 >= reportTotal} onClick={() => setReportPage(p => p + 1)} data-testid="reports-next">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}

        {tab === "users" && (
          <>
            <div className="flex gap-2 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                <Input
                  value={userSearch}
                  onChange={(e) => { setUserSearch(e.target.value); setUserPage(0); }}
                  placeholder="Buscar por email, username, nombre..."
                  className="pl-10"
                  data-testid="user-search-input"
                />
              </div>
            </div>
            <p className="text-xs text-[#8D99AE] mb-3">{userTotal} usuarios encontrados</p>
            <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[220px]">Usuario</TableHead>
                    <TableHead className="min-w-[120px]">Último login</TableHead>
                    <TableHead className="min-w-[110px]">Plataforma</TableHead>
                    <TableHead className="min-w-[90px]">Reportes</TableHead>
                    <TableHead className="min-w-[80px]">Votos</TableHead>
                    <TableHead className="min-w-[90px]">Puntos</TableHead>
                    <TableHead className="min-w-[220px]">Tipo de cuenta</TableHead>
                    <TableHead className="min-w-[110px]">Acceso</TableHead>
                    <TableHead className="min-w-[120px]">Auth</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u, i) => {
                    const draftKey = u.id || u.email;
                    const draft = userDrafts[draftKey] || {
                      accountType: u.account_type || "standard",
                      municipalityName: u.municipality_name || "",
                      municipalityProvince: u.municipality_province || "",
                    };
                    const isMunicipalWorker = draft.accountType === "municipal_worker";
                    const hasDraftChanges =
                      draft.accountType !== (u.account_type || "standard")
                      || draft.municipalityName !== (u.municipality_name || "")
                      || draft.municipalityProvince !== (u.municipality_province || "");
                    return (
                    <TableRow key={u.email} data-testid={`user-row-${i}`}>
                      <TableCell>
                        <div className="min-w-0">
                          <p className="font-bold text-[#2B2D42] truncate">{u.display_name}</p>
                          <p className="text-[11px] text-[#8D99AE] truncate">{u.email}</p>
                          <p className="text-[10px] text-[#8D99AE] truncate">
                            {u.created_at ? `Alta ${formatDateTime(u.created_at)}` : "Sin fecha de alta"}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-[#2B2D42]">{formatDateTime(u.last_login_at)}</TableCell>
                      <TableCell><PlatformBadge platform={u.last_platform} /></TableCell>
                      <TableCell>
                        <div className="text-xs font-bold text-[#2B2D42]">{u.reports_count || 0}</div>
                        <div className="text-[10px] text-[#8D99AE]">racha {u.streak_days || 0}</div>
                      </TableCell>
                      <TableCell className="text-xs font-bold text-[#2B2D42]">{u.votes_count || 0}</TableCell>
                      <TableCell>
                        <div className="text-xs font-bold text-[#2B2D42]">{u.total_score || 0}</div>
                        <div className="text-[10px] text-[#8D99AE]">trust {u.trust_score || 0}</div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-2 min-w-[220px]">
                          <Select
                            value={draft.accountType}
                            onValueChange={(value) => updateUserDraft(draftKey, {
                              accountType: value,
                              ...(value === "standard" ? { municipalityName: "", municipalityProvince: "" } : {}),
                            })}
                          >
                            <SelectTrigger className="h-8 text-xs">
                              <SelectValue placeholder="Selecciona tipo" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="standard">Usuario estándar</SelectItem>
                              <SelectItem value="municipal_worker">Operario municipal</SelectItem>
                            </SelectContent>
                          </Select>
                          {isMunicipalWorker ? (
                            <div className="grid gap-2">
                              <Input
                                value={draft.municipalityName}
                                onChange={(event) => updateUserDraft(draftKey, { municipalityName: event.target.value })}
                                placeholder="Municipio asignado"
                                className="h-8 text-xs"
                              />
                              <Input
                                value={draft.municipalityProvince}
                                onChange={(event) => updateUserDraft(draftKey, { municipalityProvince: event.target.value })}
                                placeholder="Provincia (opcional)"
                                className="h-8 text-xs"
                              />
                            </div>
                          ) : (
                            <p className="text-[10px] text-[#8D99AE]">Sin permisos especiales de limpieza.</p>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs"
                            disabled={savingUserId === draftKey || !hasDraftChanges || (isMunicipalWorker && !draft.municipalityName.trim())}
                            onClick={() => handleSaveUserAccountType(u)}
                          >
                            {savingUserId === draftKey ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : null}
                            Guardar
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                          u.subscription_active ? "bg-[#66BB6A]/10 text-[#66BB6A]" : "bg-gray-100 text-[#8D99AE]"
                        }`}>
                          {u.subscription_label}
                        </span>
                        {u.subscription_type && (
                          <div className="text-[10px] text-[#8D99AE] mt-1">{u.subscription_type}</div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-[11px] text-[#2B2D42]">{(u.auth_methods || []).join(", ") || "—"}</div>
                        <div className="text-[10px] text-[#8D99AE]">{u.rank || "—"}</div>
                      </TableCell>
                    </TableRow>
                  )})}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4">
              <Button size="sm" variant="outline" disabled={userPage === 0} onClick={() => setUserPage(p => p - 1)} data-testid="users-prev">
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-xs text-[#8D99AE]">Pág {userPage + 1} de {Math.max(1, Math.ceil(userTotal / 20))}</span>
              <Button size="sm" variant="outline" disabled={(userPage + 1) * 20 >= userTotal} onClick={() => setUserPage(p => p + 1)} data-testid="users-next">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}

        {tab === "photoApprovals" && (
          <>
            <div className="bg-white rounded-2xl shadow-sm p-4 mb-4">
              <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
                <div>
                  <h2 className="text-base font-bold text-[#2B2D42]">Aprobaciones de fotos</h2>
                  <p className="text-sm text-[#8D99AE]">
                    Las fotos adjuntas quedan pendientes hasta que un admin las aprueba. Si se rechazan, el reporte original se elimina.
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={fetchPhotoApprovals} disabled={photoApprovalLoading}>
                  {photoApprovalLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                  Actualizar
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 items-center justify-between">
                <p className="text-xs text-[#8D99AE]">
                  {photoApprovalTotal} fotos pendientes · 100 por página
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={toggleAllPhotoApprovals}
                    disabled={!photoApprovals.length}
                  >
                    {photoApprovals.length && photoApprovals.every((item) => selectedPhotoApprovalIds.includes(item.id))
                      ? "Deseleccionar visibles"
                      : "Seleccionar visibles"}
                  </Button>
                  <Button
                    size="sm"
                    className="bg-[#66BB6A] hover:bg-[#4CAF50] text-white"
                    onClick={() => handlePhotoApprovalModeration("approve")}
                    disabled={photoApprovalLoading || selectedPhotoApprovalIds.length === 0}
                  >
                    Aprobar seleccionadas ({selectedPhotoApprovalIds.length})
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handlePhotoApprovalModeration("reject")}
                    disabled={photoApprovalLoading || selectedPhotoApprovalIds.length === 0}
                  >
                    Rechazar seleccionadas ({selectedPhotoApprovalIds.length})
                  </Button>
                </div>
              </div>
            </div>

            {photoApprovalLoading && !photoApprovals.length ? (
              <div className="bg-white rounded-2xl shadow-sm p-10 flex items-center justify-center">
                <Loader2 className="w-7 h-7 animate-spin text-[#FF6B6B]" />
              </div>
            ) : photoApprovals.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm p-8 text-center">
                <CheckCircle className="w-10 h-10 text-[#66BB6A] mx-auto mb-3" />
                <p className="text-[#2B2D42] font-bold mb-1">No hay fotos pendientes de aprobación</p>
                <p className="text-sm text-[#8D99AE]">Las nuevas imágenes aparecerán aquí antes de mostrarse al resto de usuarios.</p>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {photoApprovals.map((approval, index) => (
                    <div key={approval.id || index} className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="flex items-start gap-4">
                        <input
                          type="checkbox"
                          checked={selectedPhotoApprovalIds.includes(approval.id)}
                          onChange={() => togglePhotoApprovalSelection(approval.id)}
                          className="mt-1 h-4 w-4 rounded border-[#8D99AE]/40"
                          aria-label={`Seleccionar foto ${approval.id}`}
                        />
                        {approval.photo_url ? (
                          <img
                            src={`${API}/files/${approval.photo_url}`}
                            alt="Miniatura pendiente"
                            className="w-24 h-24 rounded-xl object-cover shrink-0 bg-[#F8F9FA]"
                          />
                        ) : (
                          <div className="w-24 h-24 rounded-xl bg-[#F8F9FA] flex items-center justify-center shrink-0">
                            <Image className="w-6 h-6 text-[#8D99AE]" />
                          </div>
                        )}

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <p className="font-bold text-[#2B2D42]">{approval.municipality || "Sin municipio"}</p>
                            {approval.barrio ? (
                              <Badge variant="outline" className="text-[10px]">{approval.barrio}</Badge>
                            ) : null}
                            <Badge className="bg-[#FFA726] text-white text-[10px]">Pendiente</Badge>
                          </div>
                          <div className="text-xs text-[#8D99AE] space-y-1 mb-2">
                            <p>Subida: {formatDateTime(approval.photo_submitted_at || approval.created_at)}</p>
                            <p>Contribuidor: {approval.contributor_name || "Anónimo"}</p>
                            <p>{approval.latitude?.toFixed?.(4)}, {approval.longitude?.toFixed?.(4)}</p>
                          </div>
                          {approval.description ? (
                            <p className="text-sm text-[#2B2D42] italic line-clamp-2">"{approval.description}"</p>
                          ) : (
                            <p className="text-xs text-[#8D99AE] italic">Sin descripción</p>
                          )}
                        </div>

                        <div className="flex flex-col gap-2 shrink-0">
                          <Button
                            size="sm"
                            className="bg-[#66BB6A] hover:bg-[#4CAF50] text-white"
                            onClick={() => handlePhotoApprovalModeration("approve", [approval.id])}
                            disabled={photoApprovalLoading}
                          >
                            Aprobar
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handlePhotoApprovalModeration("reject", [approval.id])}
                            disabled={photoApprovalLoading}
                          >
                            Rechazar
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex justify-between items-center mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={photoApprovalPage === 0}
                    onClick={() => setPhotoApprovalPage((page) => Math.max(0, page - 1))}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-xs text-[#8D99AE]">
                    Pág {photoApprovalPage + 1} de {Math.max(1, Math.ceil(photoApprovalTotal / 100))}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={(photoApprovalPage + 1) * 100 >= photoApprovalTotal}
                    onClick={() => setPhotoApprovalPage((page) => page + 1)}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </>
            )}
          </>
        )}

        {tab === "violations" && (
          <>
            <p className="text-xs text-[#8D99AE] mb-3">{violationTotal} reportes pendientes de moderación</p>
            <div className="space-y-3">
              {violations.map((v, i) => (
                <div key={v.report_id || i} className="bg-white rounded-xl p-4 shadow-sm" data-testid={`violation-${i}`}>
                  <div className="flex items-start gap-3 mb-3">
                    {v.report?.photo_url ? (
                      <img src={`${API}/files/${v.report.photo_url}`} alt="Foto" className="w-16 h-16 object-cover rounded-lg" />
                    ) : (
                      <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center"><Image className="w-6 h-6 text-[#8D99AE]" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        v.reason === "face" ? "bg-red-100 text-red-600" :
                        v.reason === "license_plate" ? "bg-orange-100 text-orange-600" :
                        v.reason === "spam" ? "bg-violet-100 text-violet-700" :
                        v.reason === "inappropriate" ? "bg-fuchsia-100 text-fuchsia-700" :
                        "bg-amber-100 text-amber-600"
                      }`}>{FLAG_REASON_LABELS[v.reason] || v.reason}</span>
                      <p className="text-xs text-[#8D99AE] mt-1">{v.report?.municipality || "?"} · {v.report?.created_at?.slice(0, 10) || "?"}</p>
                      <p className="text-[10px] text-[#8D99AE]">ID: {v.report_id?.slice(0, 8)}...</p>
                      <p className="text-[10px] text-[#8D99AE]">Flags acumulados: {v.report?.flag_count || 1}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="flex-1 text-red-500 border-red-200 hover:bg-red-50" onClick={() => handleModerate(v.report_id, "hide")} data-testid={`hide-${i}`}>
                      <XCircle className="w-3.5 h-3.5 mr-1" /> Ocultar
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1 text-[#66BB6A] border-[#66BB6A]/30 hover:bg-[#66BB6A]/10" onClick={() => handleModerate(v.report_id, "dismiss")} data-testid={`dismiss-${i}`}>
                      <CheckCircle className="w-3.5 h-3.5 mr-1" /> Descartar
                    </Button>
                  </div>
                </div>
              ))}
              {violations.length === 0 && (
                <div className="text-center py-12">
                  <CheckCircle className="w-10 h-10 text-[#66BB6A] mx-auto mb-3" />
                  <p className="text-[#8D99AE] text-sm">No hay reportes pendientes de moderación</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
