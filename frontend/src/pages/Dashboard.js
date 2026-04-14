import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Building2, MapPin, Flag, Archive, Eye, EyeOff, CheckCircle, XCircle, Loader2, BarChart3, AlertTriangle, LogOut, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { useAuth } from "../contexts/AuthContext";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const FLAG_REASON_LABELS = {
  license_plate: "Matrícula visible",
  face: "Cara visible",
  name: "Nombre visible",
  personal_info: "Info personal",
  inappropriate: "Contenido inapropiado",
  spam: "Spam / Falso",
  other: "Otro"
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [flags, setFlags] = useState([]);
  const [reportFilter, setReportFilter] = useState("active");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || (user.role !== "municipality" && user.role !== "admin")) {
      navigate("/dashboard/login");
      return;
    }
    fetchAll();
  }, [user, navigate]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [statsRes, reportsRes, flagsRes] = await Promise.all([
        axios.get(`${API}/municipality/stats`, { withCredentials: true }),
        axios.get(`${API}/municipality/reports?status=${reportFilter}&page=${page}`, { withCredentials: true }),
        axios.get(`${API}/municipality/flags?status=pending`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setReports(reportsRes.data.reports);
      setTotalPages(reportsRes.data.pages);
      setFlags(flagsRes.data);
    } catch (err) {
      if (err.response?.status === 403) navigate("/dashboard/login");
      else toast.error("Error loading dashboard");
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async (filter, p) => {
    try {
      const { data } = await axios.get(`${API}/municipality/reports?status=${filter}&page=${p}`, { withCredentials: true });
      setReports(data.reports);
      setTotalPages(data.pages);
    } catch { /* ignore */ }
  };

  const handleFilterChange = (filter) => {
    setReportFilter(filter);
    setPage(1);
    fetchReports(filter, 1);
  };

  const handleModerate = async (reportId, action) => {
    try {
      await axios.post(`${API}/municipality/moderate/${reportId}`, { action }, { withCredentials: true });
      toast.success(`Acción "${action}" aplicada`);
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/dashboard/login");
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-[#2B2D42]" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="dashboard-page">
      {/* Header */}
      <div className="bg-[#2B2D42] text-white px-4 sm:px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Building2 className="w-6 h-6" />
            <div>
              <h1 className="font-bold text-lg" style={{ fontFamily: 'Nunito, sans-serif' }}>{user?.municipality_name || "Dashboard"}</h1>
              <p className="text-white/60 text-xs">Panel de Ayuntamiento</p>
            </div>
          </div>
          <Button variant="ghost" onClick={handleLogout} className="text-white/80 hover:text-white hover:bg-white/10" data-testid="dashboard-logout-btn">
            <LogOut className="w-4 h-4 mr-2" />Salir
          </Button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            {[
              { label: "Total Reportes", value: stats.total_reports, icon: MapPin, color: "#FF6B6B" },
              { label: "Activos", value: stats.active_reports, icon: Eye, color: "#FFA726" },
              { label: "Reportados", value: stats.flagged_reports, icon: Flag, color: "#FF5252" },
              { label: "Archivados", value: stats.archived_reports, icon: Archive, color: "#66BB6A" },
              { label: "Últimos 7 días", value: stats.recent_reports_7d, icon: BarChart3, color: "#42A5F5" },
              { label: "Flags Pendientes", value: stats.pending_flags, icon: AlertTriangle, color: "#FF5252" }
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-white rounded-xl p-4 shadow-sm" data-testid={`stat-${label.toLowerCase().replace(/ /g, '-')}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4" style={{ color }} />
                  <span className="text-xs text-[#8D99AE]">{label}</span>
                </div>
                <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
              </div>
            ))}
          </div>
        )}

        <Tabs defaultValue="reports" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="reports" data-testid="tab-reports">Reportes</TabsTrigger>
            <TabsTrigger value="flags" data-testid="tab-flags">
              Moderación {flags.length > 0 && <Badge variant="destructive" className="ml-2 text-xs">{flags.length}</Badge>}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="reports">
            {/* Filter */}
            <div className="flex gap-2 mb-4 flex-wrap">
              {["active", "flagged", "archived"].map((f) => (
                <Button key={f} variant={reportFilter === f ? "default" : "outline"} size="sm" onClick={() => handleFilterChange(f)}
                  className={reportFilter === f ? "bg-[#2B2D42]" : ""} data-testid={`filter-${f}`}>
                  {f === "active" ? "Activos" : f === "flagged" ? "Reportados" : "Archivados"}
                </Button>
              ))}
              <Button variant="ghost" size="sm" onClick={fetchAll} className="ml-auto"><RefreshCw className="w-4 h-4" /></Button>
            </div>

            {/* Reports Table */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-[#F8F9FA] border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Ubicación</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Fecha</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Votos</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Flags</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Estado</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {reports.length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-8 text-center text-[#8D99AE]">No hay reportes</td></tr>
                    ) : reports.map((r) => (
                      <tr key={r.id} className="hover:bg-[#F8F9FA]">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {r.photo_url && <img src={`${API}/files/${r.photo_url}`} alt="" className="w-8 h-8 rounded object-cover" />}
                            <span className="text-xs text-[#2B2D42]">{r.latitude?.toFixed(4)}, {r.longitude?.toFixed(4)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-[#8D99AE]">{new Date(r.created_at).toLocaleDateString("es-ES")}</td>
                        <td className="px-4 py-3">
                          <span className="text-xs"><span className="text-[#FF5252]">{r.still_there_count || 0}</span> / <span className="text-[#66BB6A]">{r.cleaned_count || 0}</span></span>
                        </td>
                        <td className="px-4 py-3"><span className="text-xs font-medium text-[#FF5252]">{r.flag_count || 0}</span></td>
                        <td className="px-4 py-3">
                          {r.flagged ? <Badge variant="destructive" className="text-xs">Reportado</Badge> : r.archived ? <Badge variant="secondary" className="text-xs">Archivado</Badge> : <Badge className="text-xs bg-[#66BB6A]">Activo</Badge>}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            {!r.flagged && <Button size="sm" variant="ghost" onClick={() => handleModerate(r.id, "hide")} className="text-[#FF5252] h-7 px-2" data-testid={`hide-${r.id}`}><EyeOff className="w-3 h-3" /></Button>}
                            {r.flagged && <Button size="sm" variant="ghost" onClick={() => handleModerate(r.id, "restore")} className="text-[#66BB6A] h-7 px-2" data-testid={`restore-${r.id}`}><Eye className="w-3 h-3" /></Button>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="flex justify-between items-center px-4 py-3 border-t">
                  <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => { setPage(p => p - 1); fetchReports(reportFilter, page - 1); }}>Anterior</Button>
                  <span className="text-xs text-[#8D99AE]">Página {page} de {totalPages}</span>
                  <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => { setPage(p => p + 1); fetchReports(reportFilter, page + 1); }}>Siguiente</Button>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="flags">
            <div className="space-y-3">
              {flags.length === 0 ? (
                <div className="bg-white rounded-xl p-8 text-center shadow-sm">
                  <CheckCircle className="w-12 h-12 text-[#66BB6A] mx-auto mb-3" />
                  <p className="text-[#2B2D42] font-medium">No hay flags pendientes</p>
                  <p className="text-[#8D99AE] text-sm">Todo limpio por aquí</p>
                </div>
              ) : flags.map((flag) => (
                <div key={flag.id} className="bg-white rounded-xl p-4 shadow-sm" data-testid={`flag-${flag.id}`}>
                  <div className="flex items-start gap-4">
                    {flag.report?.photo_url && (
                      <img src={`${API}/files/${flag.report.photo_url}`} alt="" className="w-20 h-20 rounded-xl object-cover" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="destructive" className="text-xs">{FLAG_REASON_LABELS[flag.reason] || flag.reason}</Badge>
                        <span className="text-xs text-[#8D99AE]">{new Date(flag.created_at).toLocaleDateString("es-ES")}</span>
                      </div>
                      <p className="text-xs text-[#8D99AE]">
                        Reporte: {flag.report?.latitude?.toFixed(4)}, {flag.report?.longitude?.toFixed(4)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleModerate(flag.report_id, "hide")} className="bg-[#FF5252] hover:bg-[#E53935] text-white h-8" data-testid={`flag-hide-${flag.report_id}`}>
                        <EyeOff className="w-3 h-3 mr-1" />Ocultar
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleModerate(flag.report_id, "dismiss")} className="h-8" data-testid={`flag-dismiss-${flag.report_id}`}>
                        <XCircle className="w-3 h-3 mr-1" />Descartar
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
