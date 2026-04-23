import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Users, FileText, Eye, AlertTriangle, DollarSign, TrendingUp, Search, ChevronLeft, ChevronRight, Loader2, LogOut, Image, CheckCircle, XCircle, Globe, Smartphone, MonitorSmartphone } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { toast } from "sonner";
import axios from "axios";

import { API } from "../config";

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

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("overview");
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [userTotal, setUserTotal] = useState(0);
  const [userPage, setUserPage] = useState(0);
  const [userSearch, setUserSearch] = useState("");
  const [violations, setViolations] = useState([]);
  const [violationTotal, setViolationTotal] = useState(0);
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
    } catch { toast.error("Error cargando usuarios"); }
  }, [userPage, userSearch]);

  const fetchViolations = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/admin/photo-violations`, { withCredentials: true });
      setViolations(data.violations);
      setViolationTotal(data.total);
    } catch { toast.error("Error cargando violaciones"); }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  useEffect(() => {
    if (tab === "users") fetchUsers();
    if (tab === "violations") fetchViolations();
  }, [fetchUsers, fetchViolations, tab]);

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
          { id: "users", label: "Usuarios", icon: Users },
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

      <div className="max-w-2xl mx-auto px-4 py-5 pb-20">
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
            <div className="grid grid-cols-2 gap-3">
              <StatCard icon={FileText} label="Total" value={d.reports.total} />
              <StatCard icon={Eye} label="Activos" value={d.reports.active} color="#66BB6A" />
              <StatCard icon={AlertTriangle} label="Marcados" value={d.reports.flagged} color="#FF5252" />
              <StatCard icon={FileText} label="Últimos 7d" value={d.reports.last_7d} sub={`${d.reports.last_30d} en 30d`} color="#FFA726" />
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
                    <TableHead className="min-w-[110px]">Acceso</TableHead>
                    <TableHead className="min-w-[120px]">Auth</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u, i) => (
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
                  ))}
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

        {tab === "violations" && (
          <>
            <p className="text-xs text-[#8D99AE] mb-3">{violationTotal} violaciones de foto pendientes</p>
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
                        "bg-amber-100 text-amber-600"
                      }`}>{v.reason}</span>
                      <p className="text-xs text-[#8D99AE] mt-1">{v.report?.municipality || "?"} · {v.report?.created_at?.slice(0, 10) || "?"}</p>
                      <p className="text-[10px] text-[#8D99AE]">ID: {v.report_id?.slice(0, 8)}...</p>
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
                  <p className="text-[#8D99AE] text-sm">No hay violaciones pendientes</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
