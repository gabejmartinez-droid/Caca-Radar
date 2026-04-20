import { ArrowLeft, Cookie } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../contexts/LanguageContext";
import LegalLinksFooter from "../components/LegalLinksFooter";

function Section({ title, children }) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-bold text-[#2B2D42]">{title}</h2>
      <div className="space-y-3 text-[#5C677D] leading-7 text-[15px]">{children}</div>
    </section>
  );
}

export default function CookiesPage() {
  const navigate = useNavigate();
  const { isRtl, t } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="cookies-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("backToMap")}
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-3xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex items-center gap-3 mb-3">
            <Cookie className="w-6 h-6 text-[#42A5F5]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              Política de Cookies de Caca Radar
            </h1>
          </div>
          <p className="text-sm font-semibold text-[#8D99AE]">Última actualización: 20 de abril de 2026</p>
        </section>

        <article className="bg-white rounded-2xl shadow-sm p-6 md:p-8 space-y-8">
          <Section title="1. Qué usamos en la web">
            <p>
              La versión web de Caca Radar utiliza cookies y tecnologías similares necesarias para iniciar sesión, mantener la sesión,
              gestionar funciones públicas como votos o alertas y recordar algunas preferencias del navegador.
            </p>
            <p>
              No hemos detectado en este proyecto cookies publicitarias ni herramientas de analítica o marketing que requieran un banner
              de consentimiento específico.
            </p>
          </Section>

          <Section title="2. Base jurídica">
            <p>
              Las cookies estrictamente necesarias y los identificadores técnicos equivalentes se utilizan porque son necesarios para
              prestar el servicio solicitado, mantener la seguridad y recordar preferencias básicas.
            </p>
            <p>
              TODO-LEGAL: confirmar si en producción existe alguna herramienta adicional de medición o terceros que requiera consentimiento.
            </p>
          </Section>

          <Section title="3. Tecnologías concretas detectadas">
            <div className="overflow-x-auto rounded-2xl border border-[#8D99AE]/15">
              <table className="min-w-full text-sm">
                <thead className="bg-[#F8F9FA] text-left text-[#2B2D42]">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Nombre</th>
                    <th className="px-4 py-3 font-semibold">Tipo</th>
                    <th className="px-4 py-3 font-semibold">Finalidad</th>
                    <th className="px-4 py-3 font-semibold">Duración</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#8D99AE]/10 text-[#5C677D]">
                  <tr>
                    <td className="px-4 py-3">`access_token`</td>
                    <td className="px-4 py-3">Cookie propia, necesaria</td>
                    <td className="px-4 py-3">Mantener la sesión web autenticada</td>
                    <td className="px-4 py-3">1 hora</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">`refresh_token`</td>
                    <td className="px-4 py-3">Cookie propia, necesaria</td>
                    <td className="px-4 py-3">Renovar la sesión web autenticada</td>
                    <td className="px-4 py-3">7 días</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">`anon_id`</td>
                    <td className="px-4 py-3">Cookie propia, necesaria</td>
                    <td className="px-4 py-3">Asociar votos anónimos y suscripciones push sin cuenta</td>
                    <td className="px-4 py-3">12 meses</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">`caca-radar-lang`</td>
                    <td className="px-4 py-3">Local storage, preferencia</td>
                    <td className="px-4 py-3">Recordar el idioma elegido</td>
                    <td className="px-4 py-3">Hasta que lo elimines</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">`caca_notifications`, `notif_prompted`, `activity_banner_*`</td>
                    <td className="px-4 py-3">Local / session storage, técnico</td>
                    <td className="px-4 py-3">Recordar ajustes de notificaciones y banners informativos</td>
                    <td className="px-4 py-3">Hasta cambio o limpieza del navegador</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Service Worker + caché</td>
                    <td className="px-4 py-3">Almacenamiento técnico</td>
                    <td className="px-4 py-3">Habilitar la web app, cachear recursos estáticos y mosaicos del mapa</td>
                    <td className="px-4 py-3">Hasta rotación o limpieza del navegador</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="4. Terceros relacionados">
            <p>
              En la versión web se usan servicios del navegador para notificaciones push y recursos de mapa de OpenStreetMap. Esto no significa
              que Caca Radar instale cookies publicitarias de esos terceros en tu navegador.
            </p>
            <p>
              Para más detalle sobre el tratamiento de datos personales y proveedores técnicos, consulta la{" "}
              <Link to="/privacy" className="text-[#FF6B6B] font-medium">Política de Privacidad</Link>.
            </p>
          </Section>

          <Section title="5. Cómo desactivar o borrar estas tecnologías">
            <p>
              Puedes cerrar sesión, borrar cookies desde tu navegador, limpiar almacenamiento local o eliminar la caché de la web app desde la
              configuración del navegador.
            </p>
            <p>
              Si bloqueas cookies o almacenamiento técnico, es posible que el inicio de sesión, las alertas o algunas funciones de la web no
              funcionen correctamente.
            </p>
          </Section>

          <footer className="pt-2 border-t border-[#8D99AE]/15 space-y-4">
            <p className="text-sm text-[#5C677D]">
              Caca Radar es una herramienta privada, independiente y no oficial. No representa, sustituye ni está afiliada a ningún ayuntamiento,
              administración pública ni entidad gubernamental.
            </p>
            <LegalLinksFooter />
          </footer>
        </article>
      </main>
    </div>
  );
}
