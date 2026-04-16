import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Loader2, ArrowLeft, BarChart3, TrendingUp, MapPin, Clock, Flag, CheckCircle, Calendar } from "lucide-react";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useAuth } from "../contexts/AuthContext";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from "recharts";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";
const COLORS = ["#FF6B6B", "#FFA726", "#66BB6A", "#42A5F5", "#AB47BC", "#26C6DA"];
const TICK_STYLE = { fontSize: 11 };
const GRID_DASH = "3 3";
const GRID_COLOR = "#F0F0F0";
const AXIS_COLOR = "#8D99AE";
const BAR_RADIUS = [4, 4, 0, 0];

export default function AnalyticsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || (user.role !== "municipality" && user.role !== "admin")) {
      navigate("/dashboard/login");
      return;
    }
    fetchAnalytics();
  }, [user, navigate]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/municipality/analytics`, { withCredentials: true });
      setAnalytics(data);
    } catch { navigate("/dashboard"); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#2B2D42]" /></div>;
  if (!analytics) return null;

  return (
    <div className="min-h-screen bg-[#F8F9FA]" data-testid="analytics-page">
      <div className="bg-[#2B2D42] text-white px-4 sm:px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate("/dashboard")} className="text-white/80 hover:text-white hover:bg-white/10 px-2">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="font-bold text-lg" style={{ fontFamily: 'Nunito, sans-serif' }}>Analíticas — {analytics.municipality}</h1>
            <p className="text-white/60 text-xs">Datos de los últimos 30 días</p>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: "Reportes (30d)", value: analytics.summary.reports_30d, icon: MapPin, color: "#FF6B6B", delta: analytics.summary.reports_trend },
            { label: "Verificados", value: analytics.summary.verified, icon: CheckCircle, color: "#66BB6A" },
            { label: "Tiempo medio resolución", value: analytics.summary.avg_resolution_hours ? `${analytics.summary.avg_resolution_hours}h` : "—", icon: Clock, color: "#42A5F5" },
            { label: "Tasa de flags", value: `${analytics.summary.flag_rate}%`, icon: Flag, color: "#FFA726" }
          ].map(({ label, value, icon: Icon, color, delta }) => (
            <div key={label} className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Icon className="w-4 h-4" style={{ color }} />
                <span className="text-xs text-[#8D99AE]">{label}</span>
              </div>
              <p className="text-2xl font-black text-[#2B2D42]">{value}</p>
              {delta !== undefined && (
                <p className={`text-xs mt-1 ${delta >= 0 ? 'text-[#FF6B6B]' : 'text-[#66BB6A]'}`}>
                  <TrendingUp className="w-3 h-3 inline mr-0.5" />{delta >= 0 ? '+' : ''}{delta}% vs mes anterior
                </p>
              )}
            </div>
          ))}
        </div>

        <Tabs defaultValue="timeline" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="timeline">Evolución</TabsTrigger>
            <TabsTrigger value="hours">Por Hora</TabsTrigger>
            <TabsTrigger value="status">Estados</TabsTrigger>
            <TabsTrigger value="top">Top Zonas</TabsTrigger>
          </TabsList>

          {/* Timeline Chart */}
          <TabsContent value="timeline">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold text-[#2B2D42] mb-4">Reportes por día</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analytics.daily_reports}>
                  <CartesianGrid strokeDasharray={GRID_DASH} stroke={GRID_COLOR} />
                  <XAxis dataKey="date" tick={TICK_STYLE} stroke={AXIS_COLOR} />
                  <YAxis tick={TICK_STYLE} stroke={AXIS_COLOR} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" stroke="#FF6B6B" fill="#FF6B6B" fillOpacity={0.15} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          {/* Hourly Distribution */}
          <TabsContent value="hours">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold text-[#2B2D42] mb-4">Distribución por hora del día</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.hourly_distribution}>
                  <CartesianGrid strokeDasharray={GRID_DASH} stroke={GRID_COLOR} />
                  <XAxis dataKey="hour" tick={TICK_STYLE} stroke={AXIS_COLOR} />
                  <YAxis tick={TICK_STYLE} stroke={AXIS_COLOR} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#FF6B6B" radius={BAR_RADIUS} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          {/* Status Pie */}
          <TabsContent value="status">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold text-[#2B2D42] mb-4">Estado de reportes</h3>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={analytics.status_distribution} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="count" nameKey="status" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {analytics.status_distribution.map((entry, i) => (
                        <Cell key={entry.status} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {analytics.status_distribution.map((s, i) => (
                    <div key={s.status} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-sm text-[#2B2D42]">{s.status}: <strong>{s.count}</strong></span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Top Zones */}
          <TabsContent value="top">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold text-[#2B2D42] mb-4">Zonas con más reportes</h3>
              {analytics.top_zones.length === 0 ? (
                <p className="text-center text-[#8D99AE] py-8">No hay suficientes datos</p>
              ) : (
                <div className="space-y-3">
                  {analytics.top_zones.map((zone, i) => (
                    <div key={zone.area} className="flex items-center gap-3">
                      <span className="w-6 h-6 flex items-center justify-center rounded-full bg-[#FF6B6B]/10 text-[#FF6B6B] text-xs font-bold">{i + 1}</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-[#2B2D42]">{zone.area}</span>
                          <span className="text-sm font-bold text-[#FF6B6B]">{zone.count}</span>
                        </div>
                        <div className="w-full bg-[#F8F9FA] rounded-full h-2">
                          <div className="h-2 rounded-full bg-[#FF6B6B]" style={{ width: `${(zone.count / (analytics.top_zones[0]?.count || 1)) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
