import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Building2, Mail, Lock, MapPin, User, Loader2, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import axios from "axios";

const API = "/api";

export default function MunicipalityRegister() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1=form, 2=verify, 3=done
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form fields
  const [name, setName] = useState("");
  const [municipalityName, setMunicipalityName] = useState("");
  const [province, setProvince] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 6) { setError("La contraseña debe tener al menos 6 caracteres"); return; }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/municipality/register`, {
        email, password, name, municipality_name: municipalityName, province
      }, { withCredentials: true });
      
      if (data.verification_required) {
        setPendingEmail(email);
        setStep(2);
        toast.success("Código de verificación enviado a tu email");
      } else {
        setStep(3);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await axios.post(`${API}/municipality/verify`, {
        email: pendingEmail, code: verificationCode
      }, { withCredentials: true });
      setStep(3);
      toast.success("Email verificado correctamente");
    } catch (err) {
      setError(err.response?.data?.detail || "Código inválido");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await axios.post(`${API}/municipality/resend-verification`, { email: pendingEmail }, { withCredentials: true });
      toast.success("Código reenviado");
    } catch {
      toast.error("Error al reenviar el código");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col" data-testid="municipality-register-page">
      <div className="p-4">
        <Button variant="ghost" onClick={() => navigate("/dashboard/login")} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />Volver al login
        </Button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-14 h-14 bg-[#2B2D42] rounded-2xl flex items-center justify-center">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <div>
            <span className="text-2xl font-black text-[#2B2D42] block" style={{ fontFamily: 'Nunito, sans-serif' }}>Caca Radar</span>
            <span className="text-sm text-[#8D99AE]">Registro de Ayuntamiento</span>
          </div>
        </div>

        <div className="w-full max-w-md bg-white rounded-2xl shadow-sm p-6">
          {/* Step indicators */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= s ? 'bg-[#2B2D42] text-white' : 'bg-[#F8F9FA] text-[#8D99AE]'}`}>
                  {step > s ? <CheckCircle className="w-4 h-4" /> : s}
                </div>
                {s < 3 && <div className={`w-8 h-0.5 ${step > s ? 'bg-[#2B2D42]' : 'bg-[#F8F9FA]'}`} />}
              </div>
            ))}
          </div>

          {step === 1 && (
            <>
              <h1 className="text-xl font-bold text-[#2B2D42] text-center mb-2" style={{ fontFamily: 'Nunito, sans-serif' }}>Registra tu Ayuntamiento</h1>
              <p className="text-sm text-[#8D99AE] text-center mb-6">Usa tu email oficial del ayuntamiento para verificar tu identidad.</p>

              {error && <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4" data-testid="error-message">{error}</div>}

              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label className="text-[#2B2D42]">Nombre del contacto</Label>
                  <div className="relative mt-1">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                    <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nombre y apellido" className="pl-10" required data-testid="contact-name-input" />
                  </div>
                </div>
                <div>
                  <Label className="text-[#2B2D42]">Nombre del municipio</Label>
                  <div className="relative mt-1">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                    <Input value={municipalityName} onChange={(e) => setMunicipalityName(e.target.value)} placeholder="Ej: Alcobendas" className="pl-10" required data-testid="municipality-name-input" />
                  </div>
                </div>
                <div>
                  <Label className="text-[#2B2D42]">Provincia</Label>
                  <div className="relative mt-1">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                    <Input value={province} onChange={(e) => setProvince(e.target.value)} placeholder="Ej: Madrid" className="pl-10" required data-testid="province-input" />
                  </div>
                </div>
                <div>
                  <Label className="text-[#2B2D42]">Email oficial del ayuntamiento</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                    <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="nombre@ayuntamiento.es" className="pl-10" required data-testid="email-input" />
                  </div>
                  <p className="text-xs text-[#8D99AE] mt-1">Debe ser un dominio oficial (.es, .gob.es, .org)</p>
                </div>
                <div>
                  <Label className="text-[#2B2D42]">Contraseña</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D99AE]" />
                    <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mínimo 6 caracteres" className="pl-10" required data-testid="password-input" />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#2B2D42] hover:bg-[#1a1b2e] text-white py-5 rounded-xl font-bold" data-testid="register-submit-btn">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Registrar Municipio"}
                </Button>
              </form>
            </>
          )}

          {step === 2 && (
            <>
              <h1 className="text-xl font-bold text-[#2B2D42] text-center mb-2" style={{ fontFamily: 'Nunito, sans-serif' }}>Verifica tu email</h1>
              <p className="text-sm text-[#8D99AE] text-center mb-6">Hemos enviado un código de 6 dígitos a <strong>{pendingEmail}</strong></p>

              {error && <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm mb-4">{error}</div>}

              <form onSubmit={handleVerify} className="space-y-4">
                <div>
                  <Label className="text-[#2B2D42]">Código de verificación</Label>
                  <Input type="text" value={verificationCode} onChange={(e) => setVerificationCode(e.target.value)} placeholder="123456" className="text-center text-2xl tracking-widest" maxLength={6} required data-testid="verification-code-input" />
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#2B2D42] hover:bg-[#1a1b2e] text-white py-5 rounded-xl font-bold" data-testid="verify-submit-btn">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Verificar"}
                </Button>
              </form>
              <Button variant="ghost" onClick={handleResend} className="w-full text-[#8D99AE] mt-2">Reenviar código</Button>
            </>
          )}

          {step === 3 && (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-[#66BB6A] mx-auto mb-4" />
              <h1 className="text-xl font-bold text-[#2B2D42] mb-2" style={{ fontFamily: 'Nunito, sans-serif' }}>Registro completado</h1>
              <p className="text-sm text-[#8D99AE] mb-6">Tu cuenta de municipio ha sido creada. Ya puedes acceder al panel de control.</p>
              <Button onClick={() => navigate("/dashboard")} className="bg-[#2B2D42] hover:bg-[#1a1b2e] text-white py-5 rounded-xl font-bold px-8" data-testid="go-to-dashboard-btn">
                Ir al Panel
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
