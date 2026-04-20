import { ArrowLeft, Flag, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
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

export default function CommunityGuidelinesPage() {
  const navigate = useNavigate();
  const { isRtl, t } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="community-page">
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
            <ShieldAlert className="w-6 h-6 text-[#FF6B6B]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              Normas de la comunidad y moderación
            </h1>
          </div>
          <p className="text-sm font-semibold text-[#8D99AE]">Última actualización: 20 de abril de 2026</p>
        </section>

        <article className="bg-white rounded-2xl shadow-sm p-6 md:p-8 space-y-8">
          <Section title="1. Qué es Caca Radar">
            <p>
              Caca Radar es una herramienta comunitaria, privada, independiente y no oficial. Los avisos visibles en el mapa son aportaciones de
              la comunidad y pueden ser exactos, incompletos, desactualizados o retirados tras revisión.
            </p>
            <p>
              La app no representa a ningún ayuntamiento ni sustituye canales oficiales de incidencia, denuncia administrativa o emergencias.
            </p>
          </Section>

          <Section title="2. Qué contenido no está permitido">
            <ul className="list-disc pl-6 space-y-2">
              <li>contenido falso o manipulado de forma deliberada;</li>
              <li>acoso, amenazas, insultos o difamación;</li>
              <li>datos personales innecesarios de terceros;</li>
              <li>rostros identificables, menores, matrículas u otra información personal cuando no sea estrictamente necesaria y lícita;</li>
              <li>contenido ilícito, discriminatorio, violento o sexualmente explícito;</li>
              <li>spam, fraude, automatización no autorizada o manipulación del sistema.</li>
            </ul>
          </Section>

          <Section title="3. Cómo reportar contenido">
            <p>
              Si detectas un aviso o una imagen que incumple estas normas, puedes reportarlo desde la función de bandera dentro del detalle del
              reporte en la app o escribir a <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
            </p>
            <p>
              Cuando nos escribas, incluye el identificador del reporte o la mayor cantidad de información posible para localizarlo.
            </p>
          </Section>

          <Section title="4. Qué medidas podemos adoptar">
            <p>
              Podemos revisar, ocultar, marcar, limitar o retirar reportes y, en su caso, limitar cuentas cuando existan indicios razonables de
              incumplimiento, abuso, fraude o riesgo para otras personas usuarias.
            </p>
            <p>
              En el código actual también existen revisiones internas de contenido marcado y flujos de moderación para fotografías e incidencias.
            </p>
          </Section>

          <Section title="5. Revisión o apelación">
            <p>
              Si consideras que se ha retirado tu contenido o limitado tu cuenta por error, puedes solicitar revisión escribiendo a{" "}
              <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
            </p>
            <p>
              Intentaremos revisar la solicitud y responder con una decisión razonable tan pronto como sea posible.
            </p>
          </Section>

          <footer className="pt-2 border-t border-[#8D99AE]/15 space-y-4">
            <div className="rounded-2xl bg-[#F8F9FA] px-4 py-3 text-sm text-[#5C677D] flex items-start gap-3">
              <Flag className="w-4 h-4 text-[#FF6B6B] mt-0.5 shrink-0" />
              <p>
                Los avisos mostrados en Caca Radar son aportaciones de la comunidad. Pueden ser aproximados, incompletos, desactualizados o
                retirados tras moderación.
              </p>
            </div>
            <LegalLinksFooter />
          </footer>
        </article>
      </main>
    </div>
  );
}
