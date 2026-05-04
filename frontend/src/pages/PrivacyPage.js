import { ArrowLeft, Mail, Shield } from "lucide-react";
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

export default function PrivacyPage() {
  const navigate = useNavigate();
  const { isRtl, t } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="privacy-page">
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
            <Shield className="w-6 h-6 text-[#66BB6A]" />
            <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
              Política de Privacidad de Caca Radar
            </h1>
          </div>
          <p className="text-sm font-semibold text-[#8D99AE]">Última actualización: 4 de mayo de 2026</p>
        </section>

        <article className="bg-white rounded-2xl shadow-sm p-6 md:p-8 space-y-8">
          <Section title="1. Responsable del tratamiento">
            <div className="space-y-1 font-medium text-[#2B2D42]">
              <p>Responsable: Gabriel Joseph Martinez Nicolini</p>
              <p>NIF: 12455167T</p>
              <p>Dirección: Callejón de la Parra, 3, 2, 3, Cartagena 30202, España</p>
              <p>Correo electrónico general: <a className="text-[#FF6B6B]" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
              <p>Correo para privacidad y ejercicio de derechos: <a className="text-[#FF6B6B]" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
            </div>
            <p>
              Caca Radar es una aplicación y servicio digital privado e independiente. No existe un Delegado de Protección de Datos separado.
            </p>
          </Section>

          <Section title="2. Ámbito de aplicación">
            <ul className="list-disc pl-6 space-y-2">
              <li>la app móvil Caca Radar;</li>
              <li>la web y la web app de Caca Radar;</li>
              <li>las cuentas de usuario;</li>
              <li>las comunicaciones de soporte;</li>
              <li>las funciones de mapas, reportes, notificaciones y suscripciones que estén realmente activas.</li>
            </ul>
            <p>No se aplica a servicios de terceros enlazados desde Caca Radar, que se regirán por sus propias políticas.</p>
          </Section>

          <Section title="3. Qué datos personales tratamos">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-[#2B2D42]">a) Cuenta y acceso</h3>
                <ul className="list-disc pl-6 space-y-2 mt-2">
                  <li>email;</li>
                  <li>nombre visible o nombre de usuario;</li>
                  <li>identificador interno de cuenta;</li>
                  <li>hash de contraseña si accedes por email y contraseña;</li>
                  <li>datos básicos del proveedor de acceso cuando usas Google, como identificador, nombre, email e imagen de perfil si Google los facilita.</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">b) Reportes y contenido</h3>
                <ul className="list-disc pl-6 space-y-2 mt-2">
                  <li>texto descriptivo del reporte;</li>
                  <li>fotografías subidas;</li>
                  <li>ubicación del reporte;</li>
                  <li>fecha, estado, votos, validaciones, flags y métricas del propio reporte.</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">c) Ubicación</h3>
                <p>
                  Si activas la localización o seleccionas un punto en el mapa, tratamos coordenadas para crear reportes, validar cercanía y mostrar avisos en el mapa.
                </p>
                <p className="font-medium text-[#2B2D42]">
                  Los reportes no se muestran de forma pública y abierta a personas no autenticadas. Su visualización queda limitada a cuentas autenticadas, flujos internos del servicio y accesos municipales o administrativos autorizados.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">d) Datos técnicos</h3>
                <ul className="list-disc pl-6 space-y-2 mt-2">
                  <li>dirección IP y cabeceras técnicas del navegador o dispositivo;</li>
                  <li>idioma, versión de la app, plataforma y sistema operativo;</li>
                  <li>tokens de acceso en builds nativas y cookies de sesión en web;</li>
                  <li>registros técnicos necesarios para autenticación, seguridad y funcionamiento;</li>
                  <li>estado de suscripciones push y ubicaciones asociadas a esas alertas.</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">e) Suscripciones y pagos</h3>
                <p>
                  El proyecto incluye lógica de suscripciones premium y verificación de compras de Apple App Store y Google Play. Tratamos el plan,
                  estado, fechas de expiración, identificadores de compra y metadatos de verificación recibidos de la tienda correspondiente.
                </p>
                <p>No almacenamos números completos de tarjeta.</p>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">f) Soporte y reclamaciones</h3>
                <p>Tratamos la información que nos envías por email o por formularios internos de feedback y soporte.</p>
              </div>
              <div>
                <h3 className="font-semibold text-[#2B2D42]">g) Cookies y tecnologías similares</h3>
                <p>
                  En la web usamos cookies técnicas, almacenamiento local y caché del navegador para sesión, idioma, avisos, notificaciones y funcionamiento de la web app.
                  Más detalle en la <Link to="/cookies" className="text-[#FF6B6B] font-medium">Política de Cookies</Link>.
                </p>
              </div>
            </div>
          </Section>

          <Section title="4. Datos que no debes subir">
            <ul className="list-disc pl-6 space-y-2">
              <li>datos de salud, financieros o documentos identificativos;</li>
              <li>rostros identificables, menores, matrículas u otra información personal de terceros salvo necesidad estricta y base legítima;</li>
              <li>datos especialmente sensibles o innecesarios para el uso normal del servicio.</li>
            </ul>
            <p>Podemos ocultar, revisar o eliminar contenido que incluya datos personales de terceros de forma innecesaria.</p>
          </Section>

          <Section title="5. Cómo obtenemos los datos">
            <ul className="list-disc pl-6 space-y-2">
              <li>directamente de ti cuando te registras, inicias sesión, configuras alertas, subes contenido o contactas con nosotros;</li>
              <li>automáticamente cuando usas la app o la web para mantener la sesión, detectar abuso y prestar el servicio;</li>
              <li>de Google cuando eliges iniciar sesión con Google;</li>
              <li>de Apple App Store o Google Play cuando el flujo de suscripción correspondiente está en uso;</li>
              <li>de servicios técnicos integrados para mapas, geocodificación, almacenamiento de imágenes o notificaciones.</li>
            </ul>
          </Section>

          <Section title="6. Finalidades y bases jurídicas">
            <div className="space-y-4">
              <p><span className="font-semibold text-[#2B2D42]">Cuenta y acceso:</span> crear, autenticar y mantener tu cuenta. Base jurídica: ejecución del contrato.</p>
              <p><span className="font-semibold text-[#2B2D42]">Mapa y reportes:</span> permitir crear, mostrar, compartir, votar y moderar reportes comunitarios. Base jurídica: ejecución del contrato.</p>
              <p><span className="font-semibold text-[#2B2D42]">Permisos del dispositivo:</span> usar cámara, galería, ubicación y notificaciones solo cuando tú activas la función. Base jurídica: consentimiento y prestación del servicio solicitado.</p>
              <p><span className="font-semibold text-[#2B2D42]">Suscripciones:</span> activar funciones premium, verificar compras y gestionar renovaciones o expiraciones. Base jurídica: ejecución del contrato y obligaciones legales.</p>
              <p><span className="font-semibold text-[#2B2D42]">Soporte y seguridad:</span> responder incidencias, prevenir fraude, spam y abuso, y mantener la estabilidad del servicio. Base jurídica: interés legítimo y, cuando proceda, ejecución del contrato.</p>
            </div>
          </Section>

          <Section title="7. Decisiones automatizadas">
            <p>No adoptamos decisiones basadas exclusivamente en tratamientos automatizados con efectos jurídicos o significativamente similares sobre la persona usuaria.</p>
            <p>El servicio sí usa automatismos básicos de seguridad, validación, proximidad, ranking y moderación técnica.</p>
          </Section>

          <Section title="8. Destinatarios y proveedores técnicos">
            <ul className="list-disc pl-6 space-y-2">
              <li>Google, para inicio de sesión con Google;</li>
              <li>OpenStreetMap y Nominatim, para mosaicos y geocodificación inversa del mapa;</li>
              <li>Emergent, como proveedor principal de despliegue, hosting y almacenamiento de objetos del servicio;</li>
              <li>MongoDB Atlas, como proveedor de base de datos principal;</li>
              <li>Resend, para el envío de emails transaccionales como verificación, recuperación de acceso y algunas comunicaciones operativas;</li>
              <li>Apple App Store y Google Play, para suscripciones y verificación de compras cuando aplique;</li>
              <li>servicios push del navegador y Google Firebase Cloud Messaging para notificaciones push cuando la función está activada.</li>
            </ul>
            <p>
              El servicio está orientado a infraestructura en la Unión Europea y España. Cuando algún proveedor técnico trate datos fuera del Espacio Económico Europeo, aplicaremos las garantías adecuadas previstas por el RGPD.
            </p>
          </Section>

          <Section title="9. Contenido visible públicamente">
            <p>Los reportes de Caca Radar son aportaciones de la comunidad, pero no están pensados como un tablón público abierto a cualquier visitante.</p>
            <p>En el estado actual del servicio, el acceso a reportes queda limitado a personas usuarias autenticadas y, cuando proceda, a cuentas municipales o administrativas autorizadas.</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>la fotografía del reporte, si existe, según permisos y contexto de acceso;</li>
              <li>el texto descriptivo, si existe;</li>
              <li>la fecha y el estado del aviso;</li>
              <li>la ubicación del aviso según el nivel de acceso aplicable al usuario autenticado;</li>
              <li>una identificación reducida del contribuyente, con anonimización o etiquetado genérico cuando corresponda.</li>
            </ul>
            <p>Las vistas públicas anónimas no muestran listados abiertos de reportes. Algunos detalles, imágenes o enlaces compartibles pueden requerir autenticación, revisión o una acción expresa de la persona usuaria antes de mostrarse.</p>
          </Section>

          <Section title="10. Transferencias internacionales">
            <p>La infraestructura principal del servicio está configurada para operar en entorno UE / España.</p>
            <p>
              Algunos proveedores integrados pueden tratar datos fuera del Espacio Económico Europeo en casos puntuales o como parte de sus redes globales de soporte. Cuando exista transferencia internacional, se aplicarán los mecanismos previstos por el RGPD, como decisiones de adecuación,
              cláusulas contractuales tipo u otras garantías válidas.
            </p>
          </Section>

          <Section title="11. Conservación de los datos">
            <ul className="list-disc pl-6 space-y-2">
              <li>datos de cuenta: mientras la cuenta esté activa; tras su eliminación, la cuenta se borra y los reportes publicados se anonimizan;</li>
              <li>reportes: pueden permanecer accesibles para personas usuarias autenticadas, equipos municipales autorizados o flujos internos hasta archivo automático, moderación o eliminación; el código actual archiva reportes antiguos a partir de 30 días;</li>
              <li>cookie `access_token`: 1 hora;</li>
              <li>cookie `refresh_token`: 7 días;</li>
              <li>cookie `anon_id`: hasta 12 meses;</li>
              <li>suscripciones push: hasta baja, desactivación o supresión de cuenta;</li>
              <li>registros de seguridad y autenticación: 30 días;</li>
              <li>emails de soporte y solicitudes de contacto: 12 meses;</li>
              <li>copias de seguridad operativas: 30 días;</li>
              <li>recibos, facturación y registros contables: 6 años o el plazo legal aplicable si fuera mayor.</li>
            </ul>
            <p>
              Conservamos la información únicamente durante el tiempo necesario para operar el servicio, prevenir abuso, atender reclamaciones razonables y cumplir obligaciones legales. Cuando un dato deja de ser necesario, lo eliminamos o lo anonimizamos según corresponda.
            </p>
          </Section>

          <Section title="12. Derechos de las personas usuarias">
            <p>
              Puedes ejercitar los derechos de acceso, rectificación, supresión, oposición, limitación del tratamiento, portabilidad cuando proceda y retirada del consentimiento
              respecto de tratamientos basados en consentimiento.
            </p>
            <p>
              Para ejercerlos, escribe a <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>. Responderemos dentro del plazo legal aplicable,
              normalmente un mes, salvo prórroga permitida por ley.
            </p>
            <p>También puedes reclamar ante la Agencia Española de Protección de Datos (AEPD).</p>
          </Section>

          <Section title="13. Supresión de cuenta y datos">
            <p>Puedes solicitar la eliminación de tu cuenta desde la función interna de borrado o en la página <Link to="/delete-account" className="text-[#FF6B6B] font-medium">Eliminar cuenta</Link>.</p>
            <p>
              Cuando la solicitud es válida, eliminamos la cuenta y registros asociados, anonimizamos los reportes publicados para mantener la utilidad del mapa público y
              retiramos tokens, votos, validaciones, flags, feedback y ubicaciones guardadas vinculadas a esa cuenta.
            </p>
            <p>Si compraste una suscripción en Apple o Google, debes cancelarla también desde tu cuenta de la tienda correspondiente.</p>
            <p>
              Algunas copias de seguridad seguras pueden persistir temporalmente después de una solicitud válida de supresión, pero quedan aisladas,
              no se reutilizan para finalidades ordinarias y desaparecen cuando rota el ciclo normal de backups, con un máximo operativo de 30 días.
            </p>
          </Section>

          <Section title="14. Permisos del dispositivo y seguridad">
            <p>La app puede solicitar cámara, galería, ubicación y notificaciones cuando tú activas esas funciones.</p>
            <p>
              Aplicamos medidas razonables de autenticación, control de acceso, cookies seguras, separación entre web y nativo y validaciones técnicas
              del contenido y la proximidad. No podemos garantizar seguridad absoluta.
            </p>
          </Section>

          <Section title="15. Menores de edad">
            <p>Caca Radar no está dirigida a menores de 14 años sin la autorización exigida por la normativa aplicable.</p>
          </Section>

          <Section title="16. Cambios y contacto">
            <p>Podremos actualizar esta política por motivos legales, técnicos u operativos. Cuando los cambios sean relevantes, actualizaremos la fecha y lo comunicaremos por medios razonables.</p>
            <div className="flex items-center gap-3 rounded-2xl bg-[#F8F9FA] px-4 py-3">
              <Mail className="w-4 h-4 text-[#FF6B6B] shrink-0" />
              <p className="text-sm text-[#5C677D]">Contacto: <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
            </div>
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
