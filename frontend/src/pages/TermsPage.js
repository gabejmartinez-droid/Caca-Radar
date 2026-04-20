import { ArrowLeft, FileText } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../contexts/LanguageContext";

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
              Términos de Uso y Aviso Legal — Caca Radar
            </h1>
          </div>
          <p className="text-sm font-semibold text-[#8D99AE]">Última actualización: 19 de abril de 2026</p>
        </section>

        <article className="bg-white rounded-2xl shadow-sm p-6 md:p-8 space-y-8">
          <Section title="1. Identificación del titular">
            <p>En cumplimiento de la normativa aplicable, se informa de que el titular y responsable de la aplicación Caca Radar es:</p>
            <div className="space-y-1 font-medium text-[#2B2D42]">
              <p>Gabriel Joseph Martinez Nicolini</p>
              <p>NIF: 12455167T</p>
              <p>Dirección: Callejón de la Parra, 3, 2, 3, 30202 Cartagena, Murcia, España</p>
              <p>Correo electrónico de contacto: <a className="text-[#FF6B6B]" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
            </div>
            <p>A efectos de estos Términos, “Caca Radar”, “la App”, “nosotros” o “el Titular” se refiere al titular arriba identificado.</p>
          </Section>

          <Section title="2. Objeto">
            <p>Caca Radar es una aplicación destinada a que las personas usuarias puedan visualizar, comunicar y consultar incidencias o avisos relacionados con excrementos caninos y cuestiones similares de higiene urbana en espacios públicos, así como acceder a funciones informativas, comunitarias y, en su caso, de pago.</p>
            <p>Estos Términos regulan el acceso, navegación y uso de la App y, cuando proceda, la contratación de funcionalidades de pago o suscripciones.</p>
          </Section>

          <Section title="3. Aceptación de los Términos">
            <p>Al acceder, registrarte o utilizar la App, aceptas quedar vinculado por estos Términos, por la <Link to="/privacy" className="text-[#FF6B6B] font-medium">Política de Privacidad</Link> y por cualquier otra política o norma específica que se muestre dentro de la App.</p>
            <p>Si no estás de acuerdo con estos Términos, no debes utilizar la App.</p>
          </Section>

          <Section title="4. Requisitos de uso">
            <p>Para usar la App debes:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>tener capacidad legal suficiente para contratar o usar servicios digitales conforme a la legislación aplicable;</li>
              <li>facilitar información veraz, actual y completa al crear una cuenta;</li>
              <li>mantener la confidencialidad de tus credenciales de acceso;</li>
              <li>usar la App de forma lícita, diligente y respetuosa con terceros.</li>
            </ul>
            <p>Si eres menor de edad, solo podrás usar la App con autorización de tus padres, madre, padre o representante legal cuando así lo exija la normativa aplicable.</p>
          </Section>

          <Section title="5. Naturaleza del servicio">
            <p>Caca Radar ofrece una herramienta tecnológica de información y participación ciudadana. La App no es un servicio público oficial, no sustituye a un ayuntamiento, no equivale a una denuncia administrativa formal, y no es un servicio de emergencias.</p>
            <p>La información mostrada puede provenir de aportaciones de personas usuarias, datos agregados, estimaciones, geolocalización aproximada u otras fuentes técnicas. Por ello, la exactitud, actualidad o integridad de cada aviso no puede garantizarse en todo momento.</p>
          </Section>

          <Section title="6. Cuenta de usuario">
            <p>Para acceder a determinadas funciones puede ser necesario crear una cuenta.</p>
            <p>La persona usuaria se compromete a:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>no crear cuentas falsas o suplantar a terceros;</li>
              <li>no ceder su cuenta a otra persona;</li>
              <li>no utilizar la cuenta con fines ilícitos, abusivos o fraudulentos;</li>
              <li>avisarnos sin demora si sospecha un acceso no autorizado.</li>
            </ul>
            <p>Podremos suspender o cancelar cuentas cuando existan indicios razonables de incumplimiento de estos Términos, de uso abusivo o de riesgo para la App, para otras personas usuarias o para terceros.</p>
          </Section>

          <Section title="7. Normas de uso y conducta">
            <p>Queda prohibido utilizar la App para:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>publicar contenido falso, engañoso o manipulado de forma deliberada;</li>
              <li>acosar, insultar, amenazar o difamar a terceros;</li>
              <li>publicar datos personales de otras personas sin base legítima;</li>
              <li>subir contenido ilícito, ofensivo, discriminatorio, violento, sexualmente explícito o que vulnere derechos de terceros;</li>
              <li>introducir virus, bots, scrapers, automatizaciones no autorizadas o código malicioso;</li>
              <li>intentar acceder sin autorización a sistemas, cuentas o datos;</li>
              <li>usar la App para fines comerciales no autorizados, spam o publicidad no permitida;</li>
              <li>infringir derechos de propiedad intelectual o industrial.</li>
            </ul>
            <p>También queda prohibido usar la App de forma que pueda perjudicar la seguridad vial o la seguridad física, por ejemplo manipulándola de manera peligrosa mientras se conduce.</p>
          </Section>

          <Section title="8. Contenido aportado por las personas usuarias">
            <p>La persona usuaria conserva, en principio, la titularidad sobre el contenido que suba o publique, en la medida en que tenga derechos sobre él.</p>
            <p>No obstante, al subir contenido a la App, otorgas al Titular una licencia no exclusiva, mundial, gratuita, sublicenciable y limitada al funcionamiento del servicio para alojar, almacenar, reproducir, adaptar técnicamente, mostrar y comunicar dicho contenido en la medida necesaria para:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>prestar la App;</li>
              <li>mostrar avisos e incidencias en mapas, listados o estadísticas;</li>
              <li>moderar contenidos;</li>
              <li>prevenir fraude o abuso;</li>
              <li>promocionar la App de forma agregada, anonimizada o no identificativa, salvo que el contenido incluya datos personales, que se tratarán conforme a la Política de Privacidad.</li>
            </ul>
            <p>Declaras y garantizas que el contenido que subes:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>no vulnera la ley ni derechos de terceros;</li>
              <li>no incluye datos personales de terceros sin legitimación suficiente;</li>
              <li>no es manifiestamente falso o engañoso de forma intencionada.</li>
            </ul>
          </Section>

          <Section title="9. Moderación de contenidos">
            <p>Podremos revisar, limitar, desindexar, ocultar o retirar contenido, así como suspender funcionalidades o cuentas, cuando apreciemos indicios razonables de:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>ilicitud;</li>
              <li>vulneración de estos Términos;</li>
              <li>riesgo para terceros;</li>
              <li>uso fraudulento, abusivo o manipulación del sistema.</li>
            </ul>
            <p>Las personas usuarias podrán comunicar contenido presuntamente ilícito o contrario a estos Términos escribiendo a <a className="text-[#FF6B6B]" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a> e indicando, en la medida de lo posible, la ubicación del contenido, el motivo de la reclamación y cualquier información útil para su identificación.</p>
          </Section>

          <Section title="10. Exactitud de la información y disponibilidad">
            <p>Hacemos esfuerzos razonables para que la App funcione correctamente, pero no garantizamos:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>disponibilidad ininterrumpida;</li>
              <li>ausencia total de errores;</li>
              <li>exactitud absoluta de todas las incidencias o mapas;</li>
              <li>compatibilidad con todos los dispositivos, navegadores o versiones del sistema operativo.</li>
            </ul>
            <p>La App puede verse afectada por mantenimiento, incidencias técnicas, errores de terceros, redes móviles, GPS, mapas, tiendas de aplicaciones o proveedores externos.</p>
          </Section>

          <Section title="11. Funcionalidades de pago y suscripciones">
            <p>Si la App ofrece en el futuro funciones premium, planes de pago o suscripciones:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>el precio, impuestos incluidos o excluidos según se indique, se mostrará antes de confirmar la contratación;</li>
              <li>se informará de la periodicidad, renovación, forma de cancelación y funcionalidades incluidas;</li>
              <li>cuando la compra se realice a través de Google Play o Apple App Store, la facturación, renovaciones y cancelaciones podrán estar además sujetas a las condiciones de la plataforma correspondiente;</li>
              <li>la persona usuaria deberá revisar también las condiciones de la tienda desde la que contrate.</li>
            </ul>
            <p>Salvo indicación expresa en sentido contrario, las suscripciones se renovarán automáticamente por periodos sucesivos hasta su cancelación.</p>
          </Section>

          <Section title="12. Cancelación y baja">
            <p>La persona usuaria podrá dejar de usar la App en cualquier momento.</p>
            <p>Cuando existan suscripciones activas contratadas a través de una tienda de aplicaciones, la cancelación deberá hacerse desde la cuenta de la plataforma correspondiente, salvo que se indique otro método dentro de la App.</p>
            <p>La baja de la cuenta no elimina automáticamente toda la información cuando debamos conservar parte de ella por obligaciones legales, seguridad, prevención del fraude, ejercicio o defensa de reclamaciones, o copias de respaldo temporales.</p>
          </Section>

          <Section title="13. Derecho de desistimiento y derechos de las personas consumidoras">
            <p>Cuando resulte aplicable la normativa de consumo, las personas consumidoras tendrán los derechos que les reconozca la legislación vigente.</p>
            <p>En caso de contratación a distancia de servicios digitales de pago, podrá existir derecho de desistimiento dentro del plazo legal, salvo en los casos en que la normativa establezca una excepción, incluida la prestación de servicios ya ejecutados o el suministro de contenido/servicios digitales iniciado con consentimiento previo expreso y con reconocimiento de la posible pérdida del derecho de desistimiento, cuando proceda conforme a Derecho.</p>
            <p>Nada de lo previsto en estos Términos limitará los derechos irrenunciables que correspondan a las personas consumidoras y usuarias.</p>
          </Section>

          <Section title="14. Propiedad intelectual e industrial">
            <p>Todos los derechos sobre la App, su código, diseño, textos, estructura, selección y disposición de contenidos, marcas, logotipos y demás elementos pertenecen al Titular o a sus licenciantes, salvo el contenido de terceros o de personas usuarias.</p>
            <p>No se permite copiar, descompilar, extraer, reproducir, distribuir, transformar, realizar ingeniería inversa o explotar la App o sus contenidos más allá de lo necesario para su uso normal y permitido, salvo autorización expresa o habilitación legal.</p>
          </Section>

          <Section title="15. Enlaces y servicios de terceros">
            <p>La App puede integrar o enlazar servicios de terceros, como mapas, sistemas de autenticación, tiendas de aplicaciones, pasarelas de pago o herramientas analíticas.</p>
            <p>No controlamos íntegramente esos servicios externos y no respondemos de su disponibilidad, funcionamiento o políticas, que se regirán por sus propios términos y políticas.</p>
          </Section>

          <Section title="16. Protección de datos y cookies">
            <p>El tratamiento de datos personales se regula en la <Link to="/privacy" className="text-[#FF6B6B] font-medium">Política de Privacidad</Link>. El uso de cookies o tecnologías similares, cuando exista versión web o se utilicen identificadores equivalentes, se regula en la política correspondiente.</p>
          </Section>

          <Section title="17. Responsabilidad">
            <p>En la medida permitida por la ley, no seremos responsables de:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>daños derivados del uso incorrecto de la App por parte de la persona usuaria;</li>
              <li>contenido publicado por terceras personas usuarias;</li>
              <li>caídas temporales del servicio, errores técnicos, falta de conectividad o fallos de terceros;</li>
              <li>decisiones tomadas por personas usuarias o terceros basadas exclusivamente en información mostrada en la App.</li>
            </ul>
            <p>No obstante, nada en estos Términos excluirá ni limitará responsabilidad cuando dicha exclusión o limitación no esté permitida por la ley aplicable, especialmente frente a personas consumidoras.</p>
          </Section>

          <Section title="18. Modificaciones de los Términos">
            <p>Podremos modificar estos Términos por motivos legales, técnicos, operativos o de evolución del servicio.</p>
            <p>Cuando los cambios sean relevantes, informaremos por medios razonables dentro de la App o por correo electrónico si procede. La fecha de “última actualización” se modificará en consecuencia.</p>
            <p>Si continúas usando la App tras la entrada en vigor de los cambios, se entenderá que aceptas los nuevos Términos, salvo cuando la ley exija un mecanismo distinto.</p>
          </Section>

          <Section title="19. Idioma">
            <p>Estos Términos podrán mostrarse en varios idiomas. En caso de discrepancia entre versiones, y salvo que la legislación imperativa disponga otra cosa, prevalecerá la versión en castellano para usuarios en España.</p>
          </Section>

          <Section title="20. Ley aplicable y jurisdicción">
            <p>Estos Términos se rigen por la legislación española y por la normativa imperativa de la Unión Europea que resulte aplicable.</p>
            <p>Cuando la persona usuaria tenga la condición legal de consumidora, cualquier controversia se someterá a los juzgados y tribunales que correspondan conforme a la normativa imperativa aplicable.</p>
            <p>Si la persona usuaria no tiene condición de consumidora y la ley lo permite, las partes se someterán a los juzgados y tribunales de Cartagena, Murcia, España.</p>
          </Section>

          <Section title="21. Contacto y reclamaciones">
            <p>Para cualquier consulta, incidencia o reclamación relacionada con la App o estos Términos, puedes contactar en:</p>
            <p><a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a></p>
          </Section>

          <footer className="pt-2 border-t border-[#8D99AE]/15">
            <p className="text-sm text-[#5C677D]">Si tienes dudas sobre estos Términos, escríbenos a <a className="text-[#FF6B6B] font-medium" href="mailto:jefe@cacaradar.es">jefe@cacaradar.es</a>.</p>
          </footer>
        </article>
      </main>
    </div>
  );
}
