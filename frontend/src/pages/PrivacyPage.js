import { ArrowLeft, Mail, Shield, ChevronRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../contexts/LanguageContext";

const sections = [
  {
    id: "data-controller",
    title: "1. Data Controller",
    body: (
      <>
        <p>Controller: Gabriel Joseph Martinez Nicolini</p>
        <p>Tax ID / NIF/CIF: NIF 12455167T</p>
        <p>Registered address: Callejón de la Parra, 3, 2, 3, Cartagena 30202, Spain</p>
        <p>Email for privacy requests: jefe@cacaradar.es</p>
        <p>General contact email: jefe@cacaradar.es</p>
        <p>Data Protection Officer (if applicable): Not applicable. No separate Data Protection Officer has been appointed; the controller handles privacy matters directly at jefe@cacaradar.es.</p>
        <p className="mt-4">
          If you have questions about this Privacy Policy or about how we process your personal data, you can contact us using the details above.
        </p>
      </>
    ),
  },
  {
    id: "scope",
    title: "2. Scope",
    body: (
      <>
        <p>This Privacy Policy applies to:</p>
        <ul className="list-disc pl-5 space-y-1 mt-3">
          <li>the Caca Radar mobile app;</li>
          <li>the Caca Radar website at https://cacaradar.es;</li>
          <li>user accounts created for the Services;</li>
          <li>support communications with us; and</li>
          <li>any related features, content, maps, reports, subscriptions, and notifications we provide.</li>
        </ul>
        <p className="mt-4">
          This Privacy Policy does not apply to third-party websites, apps, or services that may be linked from our Services or integrated through third-party providers. Those third parties process data under their own privacy policies.
        </p>
      </>
    ),
  },
  {
    id: "personal-data",
    title: "3. Personal Data We May Collect",
    body: (
      <>
        <p>Depending on how you use the Services, we may collect the following categories of personal data:</p>
        <div className="space-y-4 mt-4">
          <div>
            <h3 className="font-semibold text-[#2B2D42]">a) Account and profile data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>name or username;</li>
              <li>email address;</li>
              <li>password hash (if you use email/password login);</li>
              <li>authentication provider data (for example, Google account identifier, name, email address, and profile image, if provided by the provider and authorised by you);</li>
              <li>account preferences and settings.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">b) Report and content data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>reports you submit through the app;</li>
              <li>photographs, text descriptions, comments, votes, flags, or other user-generated content;</li>
              <li>report location selected or detected in connection with the report;</li>
              <li>timestamps and report status information.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">c) Location data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>approximate or precise location data, if you enable location permissions on your device or choose to submit content tied to a location;</li>
              <li>map interaction data related to the areas you view or search.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">d) Device, technical, and usage data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>IP address;</li>
              <li>device identifiers and session identifiers;</li>
              <li>browser type, operating system, app version, language, time zone, and device model;</li>
              <li>app events, log data, diagnostics, crash reports, and performance data.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">e) Subscription and transaction data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>subscription plan;</li>
              <li>subscription status;</li>
              <li>renewal and cancellation information;</li>
              <li>transaction reference IDs and billing metadata received from app stores or payment providers;</li>
              <li>billing country or region where relevant.</li>
            </ul>
            <p className="mt-3">We do not intentionally store full payment card numbers unless we expressly state otherwise. Payment details are typically processed by the relevant app store or payment provider.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">f) Communications and support data</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>messages you send to us;</li>
              <li>support requests and related correspondence;</li>
              <li>feedback, survey responses, and bug reports.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">g) Cookies and similar technologies</h3>
            <p className="mt-2">
              For our website or web app, we may use cookies, SDKs, local storage, pixels, and similar technologies to operate the service, remember preferences, measure performance, and—where you consent—perform analytics or marketing-related functions.
            </p>
          </div>
        </div>
      </>
    ),
  },
  {
    id: "do-not-upload",
    title: "4. Data We Ask You Not to Upload",
    body: (
      <>
        <p>Caca Radar is not intended for the collection of special category data or other unnecessary personal data.</p>
        <p className="mt-3">Please do not upload:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>health information;</li>
          <li>government ID numbers;</li>
          <li>financial information;</li>
          <li>data revealing racial or ethnic origin, political opinions, religious beliefs, trade union membership, sex life, or sexual orientation;</li>
          <li>images of faces, children, vehicle registration plates, or other identifiable third-party information unless strictly necessary and lawful.</li>
        </ul>
        <p className="mt-4">If you upload personal data about other people, you are responsible for ensuring you have a lawful basis to do so.</p>
      </>
    ),
  },
  {
    id: "collection",
    title: "5. How We Collect Data",
    body: (
      <>
        <p>We collect personal data:</p>
        <ul className="list-disc pl-5 space-y-1 mt-3">
          <li>directly from you when you create an account, sign in, submit reports, purchase a subscription, contact support, or change settings;</li>
          <li>automatically through your use of the Services, device permissions, logs, cookies, SDKs, and analytics tools;</li>
          <li>from third-party identity providers when you choose social sign-in;</li>
          <li>from app stores or payment processors when you subscribe or make purchases;</li>
          <li>from service providers that support hosting, analytics, crash reporting, notifications, customer support, or fraud prevention.</li>
        </ul>
      </>
    ),
  },
  {
    id: "purposes",
    title: "6. Purposes of Processing and Legal Bases",
    body: (
      <>
        <p>We process personal data only when we have a valid legal basis. Depending on the context, the legal basis may be one or more of the following: performance of a contract, compliance with a legal obligation, your consent, or our legitimate interests.</p>
        <p className="mt-4">We use personal data for the following purposes:</p>
        <div className="space-y-4 mt-4">
          <div>
            <h3 className="font-semibold text-[#2B2D42]">a) To create and manage your account</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to register you;</li>
              <li>to authenticate your login;</li>
              <li>to maintain your profile and settings;</li>
              <li>to provide account-related features.</li>
            </ul>
            <p className="mt-2">Legal basis: performance of a contract, or steps taken at your request before entering into a contract.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">b) To provide the core reporting and map features</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to let you submit, view, manage, and interact with reports;</li>
              <li>to associate reports with relevant map areas or locations;</li>
              <li>to enable community features related to submitted content.</li>
            </ul>
            <p className="mt-2">Legal basis: performance of a contract.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">c) To use optional device permissions</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to access camera functionality for report photos;</li>
              <li>to access photo library uploads;</li>
              <li>to access precise location where you choose to enable geolocated reporting or nearby map features;</li>
              <li>to send optional push notifications.</li>
            </ul>
            <p className="mt-2">Legal basis: your consent and, where relevant, performance of a contract for the feature you actively request.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">d) To process subscriptions, payments, and billing-related matters</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to activate premium features;</li>
              <li>to verify subscription status;</li>
              <li>to manage renewals, cancellations, and refunds where applicable;</li>
              <li>to comply with accounting and tax obligations.</li>
            </ul>
            <p className="mt-2">Legal basis: performance of a contract and compliance with legal obligations.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">e) To communicate with you</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to send service messages, security alerts, login notices, support responses, and important updates;</li>
              <li>to send marketing communications, newsletters, or promotional messages where you have opted in or where otherwise permitted by law.</li>
            </ul>
            <p className="mt-2">Legal basis: performance of a contract, our legitimate interests for service communications, and your consent for marketing where required.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">f) To secure, improve, and administer the Services</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to monitor service availability;</li>
              <li>to detect, investigate, and prevent fraud, abuse, spam, misuse, and unlawful activity;</li>
              <li>to debug errors and improve performance;</li>
              <li>to enforce our Terms of Use and other policies;</li>
              <li>to analyse aggregated usage trends.</li>
            </ul>
            <p className="mt-2">Legal basis: our legitimate interests in operating a secure and reliable service and, where required for non-essential website technologies, your consent.</p>
          </div>
          <div>
            <h3 className="font-semibold text-[#2B2D42]">g) To comply with law and defend legal claims</h3>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>to comply with legal obligations, lawful requests, court orders, tax rules, consumer rules, and regulatory requirements;</li>
              <li>to establish, exercise, or defend legal claims.</li>
            </ul>
            <p className="mt-2">Legal basis: compliance with legal obligations and our legitimate interests.</p>
          </div>
        </div>
      </>
    ),
  },
  {
    id: "automated-decisions",
    title: "7. Automated Decisions",
    body: (
      <>
        <p>We do not make decisions based solely on automated processing that produce legal effects or similarly significant effects on you.</p>
        <p className="mt-4">We may use automated tools for basic moderation, fraud prevention, ranking, spam detection, abuse prevention, or service analytics, but not for legally significant decisions without appropriate safeguards.</p>
      </>
    ),
  },
  {
    id: "sharing",
    title: "8. Sharing of Personal Data",
    body: (
      <>
        <p>We do not sell your personal data.</p>
        <p className="mt-4">We may share personal data only where necessary with the following categories of recipients:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>hosting and infrastructure providers;</li>
          <li>database, storage, and content delivery providers;</li>
          <li>authentication providers (for example, Google, if you use Google sign-in);</li>
          <li>payment processors and app store platforms;</li>
          <li>analytics, diagnostics, and crash reporting providers;</li>
          <li>mapping, geolocation, or geocoding providers;</li>
          <li>email, notification, and communication service providers;</li>
          <li>customer support tools;</li>
          <li>professional advisers such as lawyers, accountants, auditors, or insurers;</li>
          <li>public authorities, regulators, law enforcement, or courts where required by law or necessary to protect rights, safety, or the integrity of the Services;</li>
          <li>a buyer, investor, successor, or corporate transaction counterparty in connection with a merger, acquisition, financing, asset sale, or restructuring, subject to appropriate safeguards.</li>
        </ul>
        <p className="mt-4">If you publish reports or content publicly within the Services, certain information associated with that content may be visible to other users depending on your settings and the design of the feature.</p>
      </>
    ),
  },
  {
    id: "transfers",
    title: "9. International Transfers",
    body: (
      <>
        <p>Some of our service providers may process personal data outside the European Economic Area.</p>
        <p className="mt-4">Where personal data is transferred outside the EEA, we will rely on an approved transfer mechanism, such as:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>an adequacy decision by the European Commission;</li>
          <li>the European Commission’s Standard Contractual Clauses; or</li>
          <li>another lawful safeguard or derogation recognised under applicable data protection law.</li>
        </ul>
        <p className="mt-4">You may contact us if you want more information about the safeguards used for international transfers.</p>
      </>
    ),
  },
  {
    id: "retention",
    title: "10. Data Retention",
    body: (
      <>
        <p>We keep personal data only for as long as necessary for the purposes described in this Privacy Policy, unless a longer retention period is required or permitted by law.</p>
        <p className="mt-4">In general:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>account data is kept while your account remains active and for a limited period afterwards as needed for security, dispute handling, and legal compliance;</li>
          <li>reports and user-generated content are kept while they remain active in the Services and for a limited period afterwards, unless deleted earlier or retained in anonymised form;</li>
          <li>technical logs, diagnostics, and security records are kept for a limited period appropriate to security and operational needs;</li>
          <li>support communications are kept for as long as needed to resolve the issue and manage follow-up matters;</li>
          <li>subscription and accounting records are kept for the periods required by applicable financial, tax, and accounting laws.</li>
        </ul>
        <p className="mt-4">When data is no longer needed, we delete it or anonymise it.</p>
      </>
    ),
  },
  {
    id: "rights",
    title: "11. Your Rights",
    body: (
      <>
        <p>Subject to applicable law, you have the right to:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>access your personal data;</li>
          <li>correct inaccurate or incomplete personal data;</li>
          <li>request deletion of your personal data;</li>
          <li>request restriction of processing;</li>
          <li>object to processing based on legitimate interests;</li>
          <li>withdraw consent at any time where processing is based on consent;</li>
          <li>request data portability where applicable;</li>
          <li>lodge a complaint with the competent supervisory authority.</li>
        </ul>
        <p className="mt-4">In Spain, you may lodge a complaint with the Agencia Española de Protección de Datos (AEPD) if you believe your data protection rights have been infringed.</p>
        <p className="mt-4">You can exercise your rights by contacting us at jefe@cacaradar.es. We may ask you for information necessary to verify your identity before processing your request.</p>
      </>
    ),
  },
  {
    id: "deletion",
    title: "12. Account Deletion and Data Deletion Requests",
    body: (
      <>
        <p>You may request deletion of your account and associated personal data:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>through the in-app deletion function at: https://cacaradar.es/delete-account; or</li>
          <li>by contacting us at jefe@cacaradar.es.</li>
        </ul>
        <p className="mt-4">When we receive a valid deletion request, we will delete or anonymise your personal data unless we need to retain certain information for legal compliance, fraud prevention, security, dispute resolution, or the establishment, exercise, or defence of legal claims.</p>
        <p className="mt-4">Deleting your account may not immediately remove content that has already been anonymised, aggregated, or irreversibly detached from your identity.</p>
      </>
    ),
  },
  {
    id: "cookies",
    title: "13. Cookies and Similar Technologies",
    body: (
      <>
        <p>If you use our website or web app, we may store or access information on your device using cookies or similar technologies.</p>
        <p className="mt-4">We use these technologies for purposes such as:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>enabling core site functions;</li>
          <li>maintaining sessions and login state;</li>
          <li>remembering preferences;</li>
          <li>measuring traffic and performance; and</li>
          <li>where you consent, analytics or marketing activities.</li>
        </ul>
        <p className="mt-4">Where required by law, we will request your consent before using non-essential cookies or similar technologies.</p>
        <p className="mt-4">You can manage cookies through our consent banner or your browser settings. For more detailed information, see our Cookie Policy / Cookies Section.</p>
      </>
    ),
  },
  {
    id: "permissions",
    title: "14. Device Permissions",
    body: (
      <>
        <p>Depending on your device and how you use the Services, we may request permission to access:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>camera – to take photos for reports;</li>
          <li>photos/files – to upload images;</li>
          <li>location – to submit or display location-based reports and map features;</li>
          <li>notifications – to send optional alerts or account-related notices.</li>
        </ul>
        <p className="mt-4">You can refuse or revoke these permissions at any time in your device settings, although some features may stop working properly.</p>
      </>
    ),
  },
  {
    id: "security",
    title: "15. Security",
    body: (
      <>
        <p>We implement appropriate technical and organisational measures designed to protect personal data against accidental or unlawful destruction, loss, alteration, unauthorised disclosure, or unauthorised access.</p>
        <p className="mt-4">These measures may include, where appropriate:</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>encryption in transit;</li>
          <li>access controls and least-privilege permissions;</li>
          <li>secure authentication procedures;</li>
          <li>monitoring, logging, and incident response processes;</li>
          <li>vendor access controls; and</li>
          <li>data minimisation and privacy-by-design practices.</li>
        </ul>
        <p className="mt-4">However, no system is completely secure, and we cannot guarantee absolute security.</p>
      </>
    ),
  },
  {
    id: "children",
    title: "16. Children",
    body: (
      <>
        <p>Caca Radar is not directed to children under 14 years of age in Spain, and we do not knowingly collect personal data from children below the age at which they may validly consent under applicable law.</p>
        <p className="mt-4">If you are a parent or guardian and believe that a child has provided us with personal data in breach of applicable law, please contact us and we will take appropriate steps.</p>
        <p className="mt-4">If you want to allow minors under the applicable age to use the Services with parental or guardian authorisation, you should revise this section and your onboarding flow accordingly.</p>
      </>
    ),
  },
  {
    id: "changes",
    title: "17. Changes to This Privacy Policy",
    body: (
      <>
        <p>We may update this Privacy Policy from time to time to reflect legal, technical, or business changes.</p>
        <p className="mt-4">When we make material changes, we will take appropriate steps to inform you, such as by posting the updated policy in the app or on the website, updating the "Last updated" date, or sending a notice where appropriate.</p>
      </>
    ),
  },
  {
    id: "contact",
    title: "18. Contact",
    body: (
      <>
        <p>For questions, requests, or complaints regarding privacy or personal data, contact:</p>
        <div className="mt-4 space-y-1">
          <p>Gabriel Joseph Martinez Nicolini / Caca Radar</p>
          <p>Callejón de la Parra, 3, 2, 3, Cartagena 30202, Spain</p>
          <p>jefe@cacaradar.es</p>
          <p>jefe@cacaradar.es</p>
        </div>
      </>
    ),
  },
];

export default function PrivacyPage() {
  const navigate = useNavigate();
  const { isRtl } = useLanguage();

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="privacy-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="lg:sticky lg:top-24 self-start">
            <div className="bg-white rounded-2xl shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-5 h-5 text-[#FF6B6B]" />
                <h1 className="text-lg font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                  Privacy Policy
                </h1>
              </div>
              <p className="text-sm text-[#8D99AE] mb-4">Last updated: 19 April 2026</p>
              <nav aria-label="Privacy policy contents">
                <ul className="space-y-1.5">
                  {sections.map((section) => (
                    <li key={section.id}>
                      <a
                        href={`#${section.id}`}
                        className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-[#2B2D42] hover:bg-[#F8F9FA]"
                      >
                        <span>{section.title}</span>
                        <ChevronRight className="w-4 h-4 text-[#8D99AE]" />
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </aside>

          <div className="space-y-6">
            <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8">
              <p className="text-sm font-medium text-[#FF6B6B] mb-2">Privacy Policy for Caca Radar</p>
              <h2 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                Privacy Policy
              </h2>
              <p className="text-[#5C677D] leading-7 mt-4">
                This Privacy Policy explains how Gabriel Joseph Martinez Nicolini, trading as Caca Radar (&quot;Caca Radar&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) collects, uses, shares, stores, and protects personal data when you use our mobile applications, website, and related services (together, the &quot;Services&quot;).
              </p>
            </section>

            {sections.map((section) => (
              <section key={section.id} id={section.id} className="bg-white rounded-2xl shadow-sm p-6 md:p-8 scroll-mt-24">
                <h2 className="text-2xl font-bold text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                  {section.title}
                </h2>
                <div className="mt-4 space-y-3 text-[#4A5568] leading-7 text-sm md:text-[15px]">
                  {section.body}
                </div>
              </section>
            ))}

            <section className="bg-white rounded-2xl shadow-sm p-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#2B2D42]">Need support?</h2>
                <p className="text-sm text-[#8D99AE]">For privacy or support matters, contact jefe@cacaradar.es.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <a href="mailto:jefe@cacaradar.es" className="inline-flex items-center gap-2 rounded-xl bg-[#2B2D42] px-4 py-2 text-sm font-medium text-white">
                  <Mail className="w-4 h-4" />
                  Contact privacy
                </a>
                <Link to="/help" className="inline-flex items-center gap-2 rounded-xl border border-[#8D99AE]/20 px-4 py-2 text-sm font-medium text-[#2B2D42]">
                  Help page
                </Link>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
