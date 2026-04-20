import { ArrowLeft, FileText } from "lucide-react";
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

export default function TermsPage() {
  const navigate = useNavigate();
  const { isRtl, t } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="terms-page">
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
            <FileText className="w-6 h-6 text-[#FFA726]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              Términos de uso y aviso legal — Caca Radar
            </h1>
          </div>
          <p className="text-sm font-semibold text-[#8D99AE]">Última actualización: 20 de abril de 2026</p>
        </section>

        <article className="bg-white rounded-2xl shadow-sm p-6 md:p-8 space-y-8">
          <Section title="1. Identificación del titular">
            <div className="space-y-1 font-medium text-[#2B2D42]">
              <p>Gabriel Joseph Martinez Nicolini</p>
              <p>NIF: 12455167T</p>
              <p>Dirección: Callejón de la Parra, 3, 2, 3, 30202 Cartagena, Murcia, España</p>
              <p>Email de contacto: <a className="text-[#FF6B6B]" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
            </div>
            <p>A efectos de estos Términos, “Caca Radar”, “la App”, “el Servicio” o “el Titular” se refiere a la persona arriba identificada.</p>
          </Section>

          <Section title="2. Objeto">
            <p>Estos Términos regulan el acceso, navegación y uso de Caca Radar, incluyendo la app, la web, el mapa, los reportes, las funciones comunitarias y las funcionalidades premium que estén activas.</p>
          </Section>

          <Section title="3. Naturaleza del servicio">
            <p className="font-medium text-[#2B2D42]">
              Caca Radar es una herramienta tecnológica privada, independiente y no oficial. No representa, sustituye ni está afiliada a ningún ayuntamiento, administración pública ni entidad gubernamental.
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>no sustituye a un canal administrativo oficial;</li>
              <li>no equivale a una denuncia administrativa formal;</li>
              <li>no es un servicio de emergencias;</li>
              <li>no proporciona información oficial gubernamental.</li>
            </ul>
            <p>Los avisos y contenidos visibles en el servicio son aportaciones de la comunidad y pueden ser exactos, incompletos, desactualizados o retirados tras moderación.</p>
          </Section>

          <Section title="4. Aceptación">
            <p>Al acceder, registrarte o utilizar el Servicio aceptas estos Términos, la <Link to="/privacy" className="text-[#FF6B6B] font-medium">Política de Privacidad</Link>, la <Link to="/cookies" className="text-[#FF6B6B] font-medium">Política de Cookies</Link> en la web y las normas comunitarias aplicables.</p>
            <p>Si no estás de acuerdo, no utilices el Servicio.</p>
          </Section>

          <Section title="5. Requisitos de uso">
            <ul className="list-disc pl-6 space-y-2">
              <li>tener capacidad legal suficiente para contratar o utilizar servicios digitales;</li>
              <li>proporcionar información veraz y actualizada cuando sea necesario;</li>
              <li>custodiar tus credenciales;</li>
              <li>utilizar el Servicio de forma lícita y respetuosa.</li>
            </ul>
            <p>Si eres menor de edad, solo podrás usar el Servicio cuando ello sea conforme con la normativa aplicable y, en su caso, con la autorización de tus representantes legales.</p>
          </Section>

          <Section title="6. Cuenta de usuario">
            <p>Determinadas funciones requieren cuenta. Actualmente el código del servicio permite acceso por email/contraseña y acceso con Google.</p>
            <p>La persona usuaria se compromete a no suplantar a terceros, no crear cuentas falsas con fines abusivos, no ceder la cuenta y avisarnos si detecta un acceso no autorizado.</p>
          </Section>

          <Section title="7. Normas de uso y contenido prohibido">
            <ul className="list-disc pl-6 space-y-2">
              <li>publicar contenido falso o manipulado de forma deliberada;</li>
              <li>acosar, amenazar, insultar o difamar a terceros;</li>
              <li>publicar datos personales de otras personas sin base legítima;</li>
              <li>subir imágenes o textos que identifiquen innecesariamente a terceros, especialmente menores, rostros identificables o matrículas;</li>
              <li>usar bots, scrapers, automatizaciones no autorizadas o código malicioso;</li>
              <li>hacer spam o publicidad no autorizada;</li>
              <li>usar la app de forma peligrosa mientras se conduce o en situaciones que comprometan la seguridad.</li>
            </ul>
          </Section>

          <Section title="8. Contenido aportado por las personas usuarias">
            <p>La persona usuaria conserva la titularidad del contenido que sube en la medida en que tenga derechos sobre él.</p>
            <p>Al subir contenido al Servicio, otorgas al Titular una licencia no exclusiva, mundial, gratuita y limitada a lo necesario para:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>alojar y almacenar el contenido;</li>
              <li>mostrarlo dentro del Servicio;</li>
              <li>procesarlo técnicamente para prestar las funciones del Servicio;</li>
              <li>moderarlo;</li>
              <li>prevenir fraude o abuso;</li>
              <li>generar estadísticas agregadas o contenido anonimizado del funcionamiento del Servicio.</li>
            </ul>
            <p>Esta licencia no autoriza el uso promocional individualizado de contenido identificable sin un permiso adicional y específico.</p>
          </Section>

          <Section title="9. Visibilidad pública del contenido">
            <p>En el diseño actual del servicio pueden mostrarse públicamente dentro de la app o de la web:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>fotografía del reporte, si existe;</li>
              <li>texto descriptivo, si existe;</li>
              <li>fecha y estado;</li>
              <li>ubicación mostrada en el mapa;</li>
              <li>alias o nombre visible de la persona que reportó, salvo anonimización o supresión de cuenta.</li>
            </ul>
            <p>El Servicio también puede generar enlaces internos para compartir reportes.</p>
          </Section>

          <Section title="10. Moderación, reporte y revisión">
            <p>
              Las personas usuarias pueden reportar contenido desde la función de bandera dentro del detalle de un reporte o escribiendo a{" "}
              <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.
            </p>
            <p>Podremos revisar, ocultar, limitar o retirar contenido y, en su caso, limitar cuentas cuando existan indicios razonables de ilicitud, abuso, fraude o riesgo para terceros.</p>
            <p>Si consideras que una retirada o limitación se ha producido por error, puedes solicitar revisión por el mismo correo.</p>
          </Section>

          <Section title="11. Disponibilidad y exactitud">
            <p>No garantizamos disponibilidad ininterrumpida, ausencia total de errores ni exactitud absoluta de todos los avisos o mapas.</p>
            <p>El funcionamiento depende también de GPS, redes, OpenStreetMap, Nominatim, Apple App Store, Google Play, navegadores, sistemas operativos y otros proveedores externos.</p>
          </Section>

          <Section title="12. Funcionalidades premium y suscripciones">
            <p>El código actual del servicio incluye funciones premium, prueba gratuita de 7 días y planes mostrados en la app de 3,99 €/mes y 29,99 €/año, además de lógica de verificación para Apple App Store y Google Play.</p>
            <p>Antes de confirmar una contratación, la información visible en el flujo correspondiente debe mostrar precio, periodicidad, renovación, forma de cancelación y funcionalidades incluidas.</p>
            <p>TODO-LEGAL: confirmar si todos los flujos premium mostrados en la interfaz están activos en producción y si el alta directa `/users/subscribe` sigue siendo un flujo mock.</p>
          </Section>

          <Section title="13. Derecho de desistimiento y derechos de consumo">
            <p>Cuando la contratación la realice una persona consumidora, tendrá los derechos reconocidos por la legislación aplicable.</p>
            <p>Si la prestación de un servicio digital de pago comienza de inmediato, podrá recabarse el consentimiento previo expreso y el reconocimiento de que el derecho de desistimiento puede perderse cuando la normativa lo permita.</p>
            <p>Nada de lo previsto en estos Términos limita los derechos irrenunciables de las personas consumidoras.</p>
          </Section>

          <Section title="14. Baja y cancelación">
            <p>La persona usuaria puede dejar de usar el Servicio en cualquier momento y puede solicitar la eliminación de su cuenta desde la app o desde la página <Link to="/delete-account" className="text-[#FF6B6B] font-medium">Eliminar cuenta</Link>.</p>
            <p>Si existe una suscripción activa contratada a través de Apple o Google, su cancelación debe hacerse también desde la cuenta de la tienda correspondiente.</p>
          </Section>

          <Section title="15. Propiedad intelectual e industrial">
            <p>Los derechos sobre la app, la web, su diseño, estructura, código, textos, marcas y demás elementos corresponden al Titular o a sus licenciantes, salvo el contenido titularidad de terceros o de las personas usuarias.</p>
          </Section>

          <Section title="16. Servicios de terceros">
            <p>El Servicio integra servicios de terceros para autenticación, mapas, geocodificación, almacenamiento de imágenes, notificaciones y suscripciones. Esos terceros se rigen por sus propios términos y políticas.</p>
          </Section>

          <Section title="17. Protección de datos y cookies">
            <p>El tratamiento de datos personales se regula en la <Link to="/privacy" className="text-[#FF6B6B] font-medium">Política de Privacidad</Link> y el uso de cookies o tecnologías similares en la web se regula en la <Link to="/cookies" className="text-[#FF6B6B] font-medium">Política de Cookies</Link>.</p>
          </Section>

          <Section title="18. Responsabilidad">
            <ul className="list-disc pl-6 space-y-2">
              <li>no seremos responsables de daños derivados de un uso indebido del Servicio por la persona usuaria;</li>
              <li>no garantizamos la veracidad absoluta del contenido aportado por terceras personas usuarias;</li>
              <li>no respondemos de caídas temporales, conectividad o fallos de terceros fuera de nuestro control.</li>
            </ul>
            <p>Nada de lo anterior limita la responsabilidad cuando esa limitación no esté permitida por la normativa aplicable.</p>
          </Section>

          <Section title="19. Modificaciones, idioma y ley aplicable">
            <p>Podremos modificar estos Términos por motivos legales, técnicos u operativos. Cuando los cambios sean relevantes, informaremos por medios razonables.</p>
            <p>Estos Términos podrán mostrarse en varios idiomas. Salvo norma imperativa en contrario, prevalecerá la versión en castellano para usuarios en España.</p>
            <p>Se rigen por la legislación española y por la normativa imperativa de la Unión Europea aplicable.</p>
          </Section>

          <Section title="20. Jurisdicción y contacto">
            <p>Si la persona usuaria tiene la condición legal de consumidora, cualquier controversia se someterá a los juzgados y tribunales que correspondan conforme a la normativa imperativa aplicable.</p>
            <p>Si no tiene condición de consumidora y la ley lo permite, las partes se someten a los juzgados y tribunales de Cartagena, Murcia, España.</p>
            <p>Para consultas, incidencias o reclamaciones, escribe a <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.</p>
          </Section>

          <footer className="pt-2 border-t border-[#8D99AE]/15 space-y-4">
            <p className="text-sm text-[#5C677D]">Si tienes dudas sobre estos Términos, escríbenos a <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.</p>
            <LegalLinksFooter />
          </footer>
        </article>
      </main>
    </div>
  );
}
