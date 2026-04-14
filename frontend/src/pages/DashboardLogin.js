import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Building2, Mail, Lock, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useAuth } from "../contexts/AuthContext";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function DashboardLogin() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.role === "municipality" || result.role === "admin") {
        navigate("/dashboard");
      } else {
        setError("Esta cuenta no tiene acceso al panel de municipios.");
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col" data-testid="dashboard-login-page">
      <div className="p-4">
        <Button variant="ghost" onClick={() => navigate("/")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />Volver al mapa
        </Button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-14 h-14 bg-[#2B2D42] rounded-2xl flex items-center justify-center">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <div>
            <span className="text-2xl font-black text-[#2B2D42] block" style={{ fontFamily: 'Nunito, sans-serif' }}>Caca Radar</span>
            <span className="text-sm text-[#8D99AE]">Panel de Ayuntamiento</span>
          </div>
        </div>

        <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-6">
          <h1 className="text-2xl font-bold text-[#2B2D42] text-center mb-6" style={{ fontFamily: 'Nunito, sans-serif' }}>Acceso Municipio</h1>

          {error && <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-[#2B2D42]">Email</Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="municipio@ayuntamiento.es" className="pl-10" required data-testid="email-input" />
              </div>
            </div>
            <div>
              <Label htmlFor="password" className="text-[#2B2D42]">Contraseña</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="pl-10" required data-testid="password-input" />
              </div>
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-[#2B2D42] hover:bg-[#1a1b2e] text-white py-5 rounded-xl font-bold" data-testid="submit-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Acceder al Panel"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
