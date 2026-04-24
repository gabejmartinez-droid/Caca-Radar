import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Building2, MapPin, Flag, Archive, Eye, EyeOff, CheckCircle, XCircle, Loader2, BarChart3, AlertTriangle, LogOut, RefreshCw, Camera, Shield, TrendingUp } from "lucide-react";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { getRankLabel } from "../utils/ranks";
import "leaflet/dist/leaflet.css";

import { API } from "../config";

const FLAG_REASON_LABELS = {
  license_plate: "Matrícula visible",
  face: "Cara visible",
  name: "Nombre visible",
  personal_info: "Info personal",
  inappropriate: "Contenido inapropiado",
  spam: "Spam / Falso",
  other: "Otro"
};

const MAP_MARKER_STYLES = {
  active: { color: "#FF6B6B", radius: 7, fillOpacity: 0.8 },
  flagged: { color: "#FFA726", radius: 6, fillOpacity: 0.7 },
  archived: { color: "#66BB6A", radius: 5, fillOpacity: 0.45 },
};

function MunicipalityMapCard({ mapData }) {
  if (!mapData?.points?.length || !mapData?.bounds) {
    return (
      <div className="bg-white rounded-2xl shadow-sm p-6 text-center text-[#8D99AE]">
        No hay reportes geolocalizados para mostrar en el mapa.
      </div>
    );
  }

  const bounds = [
    [mapData.bounds.south, mapData.bounds.west],
    [mapData.bounds.north, mapData.bounds.east],
  ];
  const isSinglePoint =
    mapData.bounds.south === mapData.bounds.north &&
    mapData.bounds.west === mapData.bounds.east;
  const center = [mapData.bounds.center_lat, mapData.bounds.center_lng];

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div className="p-5 border-b border-[#8D99AE]/10">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-lg font-bold text-[#2B2D42]">Mapa del municipio</h2>
            <p className="text-sm text-[#8D99AE]">Vista general de los reportes en {mapData.municipality} a nivel ciudad.</p>
          </div>
          <div className="flex gap-2 flex-wrap text-xs">
            <span className="inline-flex items-center gap-1 rounded-full bg-[#FF6B6B]/10 text-[#FF6B6B] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#FF6B6B]" /> Activos {mapData.active_reports}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#FFA726]/10 text-[#C77800] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#FFA726]" /> Reportados {mapData.flagged_reports}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-[#66BB6A]/10 text-[#2E7D32] px-3 py-1 font-bold">
              <span className="w-2 h-2 rounded-full bg-[#66BB6A]" /> Archivados {mapData.archived_reports}
            </span>
          </div>
        </div>
      </div>

      <div className="h-[420px]">
        <MapContainer
          {...(isSinglePoint ? { center, zoom: 14 } : { bounds, boundsOptions: { padding: [28, 28] } })}
          className="h-full w-full"
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mapData.points.map((point) => {
            const style = MAP_MARKER_STYLES[point.type] || MAP_MARKER_STYLES.active;
            return (
              <CircleMarker
                key={point.id}
                center={[point.lat, point.lng]}
                radius={style.radius}
                pathOptions={{
                  color: style.color,
                  fillColor: style.color,
                  fillOpacity: style.fillOpacity,
                  weight: 2,
                }}
              />
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [flags, setFlags] = useState([]);
  const [photoReviews, setPhotoReviews] = useState([]);
  const [reportFilter, setReportFilter] = useState("active");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = useCallback(async (filter, currentPage) => {
    try {
      const { data } = await axios.get(`${API}/municipality/reports?status=${filter}&page=${currentPage}`, { withCredentials: true });
      setReports(data.reports);
      setTotalPages(data.pages);
    } catch (err) { console.error("Failed to fetch reports:", err); }
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, reportsRes, flagsRes, mapRes, photoRes] = await Promise.all([
        axios.get(`${API}/municipality/stats`, { withCredentials: true }),
        axios.get(`${API}/municipality/reports?status=${reportFilter}&page=${page}`, { withCredentials: true }),
        axios.get(`${API}/municipality/flags?status=pending`, { withCredentials: true }),
        axios.get(`${API}/municipality/map`, { withCredentials: true }),
        axios.get(`${API}/municipality/photo-reviews`, { withCredentials: true }).catch(() => ({ data: [] }))
      ]);
      setStats(statsRes.data);
      setReports(reportsRes.data.reports);
      setTotalPages(reportsRes.data.pages);
      setFlags(flagsRes.data);
      setMapData(mapRes.data);
      setPhotoReviews(photoRes.data);
    } catch (err) {
      if (err.response?.status === 403) navigate("/dashboard/login");
      else toast.error("Error loading dashboard");
    } finally { setLoading(false); }
  }, [navigate, page, reportFilter]);

  useEffect(() => {
    if (!user || (user.role !== "municipality" && user.role !== "admin")) {
      navigate("/dashboard/login");
      return;
    }
    fetchAll();
  }, [fetchAll, navigate, user]);

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
    } catch (err) { toast.error(err.response?.data?.detail || "Error"); }
  };

  const handleLogout = async () => { await logout(); navigate("/dashboard/login"); };

  if (loading) return <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#2B2D42]" /></div>;

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="dashboard-page">
      {/* Header */}
      <div className="ios-safe-header bg-[#2B2D42] text-white px-4 sm:px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Building2 className="w-6 h-6" />
            <div>
              <h1 className="font-bold text-lg" style={{ fontFamily: 'Nunito, sans-serif' }}>{user?.municipality_name || "Dashboard"}</h1>
              <p className="text-white/60 text-xs">Panel de Ayuntamiento — €50/mes</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => navigate("/dashboard/analytics")} className="text-white/80 hover:text-white hover:bg-white/10" data-testid="analytics-btn">
              <TrendingUp className="w-4 h-4 mr-2" />Analíticas
            </Button>
            <Button variant="ghost" onClick={handleLogout} className="text-white/80 hover:text-white hover:bg-white/10" data-testid="dashboard-logout-btn">
              <LogOut className="w-4 h-4 mr-2" />Salir
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Stats */}
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
              <div key={label} className="bg-white rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4" style={{ color }} />
                  <span className="text-xs text-[#8D99AE]">{label}</span>
                </div>
                <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
              </div>
            ))}
          </div>
        )}

        <Tabs defaultValue="map" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="map" data-testid="tab-map">Mapa</TabsTrigger>
            <TabsTrigger value="reports" data-testid="tab-reports">Reportes</TabsTrigger>
            <TabsTrigger value="photos" data-testid="tab-photos">
              Revisión Fotos {photoReviews.length > 0 && <Badge variant="destructive" className="ml-2 text-xs">{photoReviews.length}</Badge>}
            </TabsTrigger>
            <TabsTrigger value="flags" data-testid="tab-flags">
              Moderación {flags.length > 0 && <Badge variant="destructive" className="ml-2 text-xs">{flags.length}</Badge>}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="map">
            <MunicipalityMapCard mapData={mapData} />
          </TabsContent>

          {/* Reports Tab */}
          <TabsContent value="reports">
            <div className="flex gap-2 mb-4 flex-wrap">
              {["active", "flagged", "archived"].map((f) => (
                <Button key={f} variant={reportFilter === f ? "default" : "outline"} size="sm" onClick={() => handleFilterChange(f)}
                  className={reportFilter === f ? "bg-[#2B2D42]" : ""} data-testid={`filter-${f}`}>
                  {f === "active" ? "Activos" : f === "flagged" ? "Reportados" : "Archivados"}
                </Button>
              ))}
              <Button variant="ghost" size="sm" onClick={fetchAll} className="ml-auto"><RefreshCw className="w-4 h-4" /></Button>
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
                      <th className="px-4 py-3 text-left text-xs font-medium text-[#8D99AE]">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {reports.length === 0 ? (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-[#8D99AE]">No hay reportes</td></tr>
                    ) : reports.map((r) => (
                      <tr key={r.id} className="hover:bg-[#F8F9FA]">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {r.photo_url && <img src={`${API}/files/${r.photo_url}`} alt="" className="w-8 h-8 rounded object-cover" />}
                            <span className="text-xs text-[#2B2D42]">{r.latitude?.toFixed(4)}, {r.longitude?.toFixed(4)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            <span className="text-xs font-medium text-[#2B2D42]">{r.contributor_name || "Anónimo"}</span>
                            {r.contributor_rank && <span className="text-xs text-[#FF6B6B] block max-w-[180px] truncate">{getRankLabel(r.contributor_rank_key || r.contributor_rank, t)}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-[#8D99AE]">{new Date(r.created_at).toLocaleDateString("es-ES")}</td>
                        <td className="px-4 py-3">
                          <span className="text-xs"><span className="text-[#66BB6A]">{r.upvotes || 0}</span> / <span className="text-[#FF5252]">{r.downvotes || 0}</span></span>
                        </td>
                        <td className="px-4 py-3"><span className="text-xs font-medium text-[#FF5252]">{r.flag_count || 0}</span></td>
                        <td className="px-4 py-3">
                          {r.flagged ? <Badge variant="destructive" className="text-xs">Reportado</Badge> : r.archived ? <Badge variant="secondary" className="text-xs">Archivado</Badge> : <Badge className="text-xs bg-[#66BB6A]">Activo</Badge>}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            {!r.flagged && <Button size="sm" variant="ghost" onClick={() => handleModerate(r.id, "hide")} className="text-[#FF5252] h-7 px-2"><EyeOff className="w-3 h-3" /></Button>}
                            {r.flagged && <Button size="sm" variant="ghost" onClick={() => handleModerate(r.id, "restore")} className="text-[#66BB6A] h-7 px-2"><Eye className="w-3 h-3" /></Button>}
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

          {/* Photo Reviews Tab */}
          <TabsContent value="photos">
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Camera className="w-5 h-5 text-[#FF5252]" />
                <h2 className="font-bold text-[#2B2D42]">Revisión de Fotos</h2>
              </div>
              <p className="text-sm text-[#8D99AE]">Reportes marcados por violaciones de privacidad (matrículas, caras, nombres). Se ocultan automáticamente con 2+ flags.</p>
            </div>

            <div className="space-y-4">
              {photoReviews.length === 0 ? (
                <div className="bg-white rounded-xl p-8 text-center shadow-sm">
                  <Shield className="w-12 h-12 text-[#66BB6A] mx-auto mb-3" />
                  <p className="text-[#2B2D42] font-medium">No hay fotos pendientes de revisión</p>
                  <p className="text-[#8D99AE] text-sm">Todas las fotos cumplen con las normas de privacidad</p>
                </div>
              ) : photoReviews.map((review) => (
                <div key={review.report?.id} className="bg-white rounded-xl shadow-sm overflow-hidden" data-testid={`photo-review-${review.report?.id}`}>
                  <div className="flex flex-col sm:flex-row">
                    {/* Photo */}
                    {review.report?.photo_url ? (
                      <div className="sm:w-48 h-48 sm:h-auto shrink-0">
                        <img src={`${API}/files/${review.report.photo_url}`} alt="Foto reportada" className="w-full h-full object-cover" />
                      </div>
                    ) : (
                      <div className="sm:w-48 h-48 sm:h-auto shrink-0 bg-[#F8F9FA] flex items-center justify-center">
                        <Camera className="w-8 h-8 text-[#8D99AE]" />
                      </div>
                    )}

                    {/* Details */}
                    <div className="flex-1 p-4">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        {review.flags.map((f, i) => (
                          <Badge key={`${f.reason}-${i}`} variant="destructive" className="text-xs">{FLAG_REASON_LABELS[f.reason] || f.reason}</Badge>
                        ))}
                      </div>
                      <div className="text-xs text-[#8D99AE] space-y-1 mb-3">
                        <p>Ubicación: {review.report?.latitude?.toFixed(4)}, {review.report?.longitude?.toFixed(4)}</p>
                        <p>Fecha: {review.report?.created_at ? new Date(review.report.created_at).toLocaleDateString("es-ES") : "-"}</p>
                        <p>Contribuidor: {review.report?.contributor_name || "Anónimo"}</p>
                        <p className="font-medium text-[#FF5252]">{review.photo_violation_count} violaciones de privacidad</p>
                      </div>

                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleModerate(review.report.id, "hide")} className="bg-[#FF5252] hover:bg-[#E53935] text-white" data-testid={`photo-hide-${review.report?.id}`}>
                          <EyeOff className="w-3 h-3 mr-1" />Ocultar Reporte
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleModerate(review.report.id, "dismiss")} data-testid={`photo-dismiss-${review.report?.id}`}>
                          <CheckCircle className="w-3 h-3 mr-1" />Foto Correcta
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          {/* Flags Tab */}
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
                      <p className="text-xs text-[#8D99AE]">Reporte: {flag.report?.latitude?.toFixed(4)}, {flag.report?.longitude?.toFixed(4)}</p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Button size="sm" onClick={() => handleModerate(flag.report_id, "hide")} className="bg-[#FF5252] hover:bg-[#E53935] text-white h-8">
                        <EyeOff className="w-3 h-3 mr-1" />Ocultar
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleModerate(flag.report_id, "dismiss")} className="h-8">
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
