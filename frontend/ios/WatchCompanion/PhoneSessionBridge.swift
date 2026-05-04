import Foundation
import Security
import WatchConnectivity

enum WatchCopyKey: String {
    case appTitle
    case tapToReport
    case sending
    case reportNow
    case phoneUnavailable
    case reportSent
    case reportConfirmed
    case waitingForLocation
    case locationDenied
    case locationUnavailable
    case missingAccessToken
    case invalidApiUrl
    case invalidResponse
    case reportCooldown
    case restrictedAccount
    case quickReportFailed
    case usingPhoneLocation
}

struct WatchCopy {
    let values: [WatchCopyKey: String]

    func text(_ key: WatchCopyKey) -> String {
        values[key] ?? WatchCopyCatalog.language("es").values[key] ?? key.rawValue
    }
}

enum WatchCopyCatalog {
    static func language(_ code: String) -> WatchCopy {
        switch code {
        case "en":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Tap to report poop here.",
                .sending: "Sending...",
                .reportNow: "Report here",
                .phoneUnavailable: "Open the iPhone app or bring it closer to the watch.",
                .reportSent: "Report sent in %@.",
                .reportConfirmed: "Existing report confirmed in %@.",
                .waitingForLocation: "Getting your location…",
                .locationDenied: "Allow location access on the watch to send reports.",
                .locationUnavailable: "We couldn't get your location.",
                .usingPhoneLocation: "Trying with your iPhone location…",
                .missingAccessToken: "Open Caca Radar on the iPhone and sign in again.",
                .invalidApiUrl: "The phone app has an invalid server URL.",
                .invalidResponse: "The phone sent an invalid response.",
                .reportCooldown: "Please wait 30 seconds between reports.",
                .restrictedAccount: "Your account is temporarily restricted.",
                .quickReportFailed: "The report couldn't be sent.",
            ])
        case "de":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Tippe hier, um Hundekot zu melden.",
                .sending: "Wird gesendet...",
                .reportNow: "Hier melden",
                .phoneUnavailable: "Öffne die iPhone-App oder bringe das iPhone näher an die Uhr.",
                .reportSent: "Meldung in %@ gesendet.",
                .reportConfirmed: "Bestehende Meldung in %@ bestätigt.",
                .waitingForLocation: "Standort wird ermittelt…",
                .locationDenied: "Erlaube den Standortzugriff auf der Uhr, um Meldungen zu senden.",
                .locationUnavailable: "Der Standort konnte nicht ermittelt werden.",
                .usingPhoneLocation: "Versuche es mit dem iPhone-Standort…",
                .missingAccessToken: "Öffne Caca Radar auf dem iPhone und melde dich erneut an.",
                .invalidApiUrl: "Die iPhone-App hat eine ungültige Server-URL.",
                .invalidResponse: "Die Antwort des iPhones war ungültig.",
                .reportCooldown: "Bitte warte 30 Sekunden zwischen Meldungen.",
                .restrictedAccount: "Dein Konto ist vorübergehend eingeschränkt.",
                .quickReportFailed: "Die Meldung konnte nicht gesendet werden.",
            ])
        case "nl":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Tik om hier hondenpoep te melden.",
                .sending: "Verzenden...",
                .reportNow: "Hier melden",
                .phoneUnavailable: "Open de iPhone-app of houd de iPhone dichter bij het horloge.",
                .reportSent: "Melding verzonden in %@.",
                .reportConfirmed: "Bestaande melding bevestigd in %@.",
                .waitingForLocation: "Locatie ophalen…",
                .locationDenied: "Geef locatie-toegang op het horloge om meldingen te versturen.",
                .locationUnavailable: "We konden je locatie niet ophalen.",
                .usingPhoneLocation: "We proberen je iPhone-locatie…",
                .missingAccessToken: "Open Caca Radar op de iPhone en log opnieuw in.",
                .invalidApiUrl: "De iPhone-app heeft een ongeldige server-URL.",
                .invalidResponse: "De iPhone stuurde een ongeldige reactie.",
                .reportCooldown: "Wacht 30 seconden tussen meldingen.",
                .restrictedAccount: "Je account is tijdelijk beperkt.",
                .quickReportFailed: "De melding kon niet worden verzonden.",
            ])
        case "pl":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Stuknij, aby zgłosić tu kupę.",
                .sending: "Wysyłanie...",
                .reportNow: "Zgłoś tutaj",
                .phoneUnavailable: "Otwórz aplikację na iPhonie lub zbliż iPhone'a do zegarka.",
                .reportSent: "Zgłoszenie wysłane w %@.",
                .reportConfirmed: "Istniejące zgłoszenie potwierdzone w %@.",
                .waitingForLocation: "Pobieranie lokalizacji…",
                .locationDenied: "Zezwól zegarkowi na dostęp do lokalizacji, aby wysyłać zgłoszenia.",
                .locationUnavailable: "Nie udało się pobrać lokalizacji.",
                .usingPhoneLocation: "Próbujemy użyć lokalizacji z iPhone’a…",
                .missingAccessToken: "Otwórz Caca Radar na iPhonie i zaloguj się ponownie.",
                .invalidApiUrl: "Aplikacja na iPhonie ma nieprawidłowy adres serwera.",
                .invalidResponse: "iPhone zwrócił nieprawidłową odpowiedź.",
                .reportCooldown: "Odczekaj 30 sekund między zgłoszeniami.",
                .restrictedAccount: "Twoje konto jest tymczasowo ograniczone.",
                .quickReportFailed: "Nie udało się wysłać zgłoszenia.",
            ])
        case "uk":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Натисніть, щоб повідомити про собачі екскременти тут.",
                .sending: "Надсилання...",
                .reportNow: "Повідомити тут",
                .phoneUnavailable: "Відкрийте застосунок на iPhone або піднесіть iPhone ближче до годинника.",
                .reportSent: "Звіт надіслано в %@.",
                .reportConfirmed: "Наявний звіт підтверджено в %@.",
                .waitingForLocation: "Отримуємо геопозицію…",
                .locationDenied: "Дозвольте доступ до геопозиції на годиннику, щоб надсилати звіти.",
                .locationUnavailable: "Не вдалося отримати вашу геопозицію.",
                .usingPhoneLocation: "Пробуємо геопозицію з iPhone…",
                .missingAccessToken: "Відкрийте Caca Radar на iPhone та увійдіть ще раз.",
                .invalidApiUrl: "У застосунку iPhone неправильна адреса сервера.",
                .invalidResponse: "iPhone надіслав некоректну відповідь.",
                .reportCooldown: "Зачекайте 30 секунд між звітами.",
                .restrictedAccount: "Ваш акаунт тимчасово обмежено.",
                .quickReportFailed: "Не вдалося надіслати звіт.",
            ])
        case "ru":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Нажмите, чтобы сообщить о собачьих отходах здесь.",
                .sending: "Отправка...",
                .reportNow: "Сообщить тут",
                .phoneUnavailable: "Откройте приложение на iPhone или поднесите iPhone ближе к часам.",
                .reportSent: "Сообщение отправлено в %@.",
                .reportConfirmed: "Существующее сообщение подтверждено в %@.",
                .waitingForLocation: "Получаем геопозицию…",
                .locationDenied: "Разрешите доступ к геопозиции на часах, чтобы отправлять сообщения.",
                .locationUnavailable: "Не удалось получить вашу геопозицию.",
                .usingPhoneLocation: "Пробуем геопозицию с iPhone…",
                .missingAccessToken: "Откройте Caca Radar на iPhone и войдите снова.",
                .invalidApiUrl: "В приложении iPhone неверный адрес сервера.",
                .invalidResponse: "iPhone прислал неверный ответ.",
                .reportCooldown: "Подождите 30 секунд между сообщениями.",
                .restrictedAccount: "Ваш аккаунт временно ограничен.",
                .quickReportFailed: "Не удалось отправить сообщение.",
            ])
        case "ca":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Toca per informar de caca de gos aquí.",
                .sending: "Enviant...",
                .reportNow: "Informa aquí",
                .phoneUnavailable: "Obre l'app a l'iPhone o acosta'l més al rellotge.",
                .reportSent: "Avís enviat a %@.",
                .reportConfirmed: "Avís existent confirmat a %@.",
                .waitingForLocation: "Obtenint la ubicació…",
                .locationDenied: "Permet l'accés a la ubicació al rellotge per enviar avisos.",
                .locationUnavailable: "No hem pogut obtenir la teva ubicació.",
                .usingPhoneLocation: "Provem amb la ubicació de l’iPhone…",
                .missingAccessToken: "Obre Caca Radar a l'iPhone i torna a iniciar sessió.",
                .invalidApiUrl: "L'app de l'iPhone té una URL del servidor no vàlida.",
                .invalidResponse: "L'iPhone ha enviat una resposta no vàlida.",
                .reportCooldown: "Espera 30 segons entre avisos.",
                .restrictedAccount: "El teu compte està restringit temporalment.",
                .quickReportFailed: "No s'ha pogut enviar l'avís.",
            ])
        case "val":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Toca per a informar de caca de gos ací.",
                .sending: "Enviant...",
                .reportNow: "Informa ací",
                .phoneUnavailable: "Obri l'app a l'iPhone o acosta'l més al rellotge.",
                .reportSent: "Avís enviat a %@.",
                .reportConfirmed: "Avís existent confirmat a %@.",
                .waitingForLocation: "Obtenint la ubicació…",
                .locationDenied: "Permet l'accés a la ubicació al rellotge per a enviar avisos.",
                .locationUnavailable: "No hem pogut obtindre la teua ubicació.",
                .usingPhoneLocation: "Provem amb la ubicació de l’iPhone…",
                .missingAccessToken: "Obri Caca Radar a l'iPhone i torna a iniciar sessió.",
                .invalidApiUrl: "L'app de l'iPhone té una URL del servidor no vàlida.",
                .invalidResponse: "L'iPhone ha enviat una resposta no vàlida.",
                .reportCooldown: "Espera 30 segons entre avisos.",
                .restrictedAccount: "El teu compte està restringit temporalment.",
                .quickReportFailed: "No s'ha pogut enviar l'avís.",
            ])
        case "eu":
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Sakatu hemen txakur-kakaren abisua bidaltzeko.",
                .sending: "Bidaltzen...",
                .reportNow: "Hemen salatu",
                .phoneUnavailable: "Ireki iPhone aplikazioa edo hurbildu iPhonea erlojuara.",
                .reportSent: "Abisua %@ herrian bidali da.",
                .reportConfirmed: "Lehendik zegoen abisua %@ herrian baieztatu da.",
                .waitingForLocation: "Kokapena lortzen…",
                .locationDenied: "Baimendu kokapena erlojuan abisuak bidaltzeko.",
                .locationUnavailable: "Ezin izan dugu zure kokapena lortu.",
                .usingPhoneLocation: "iPhonearen kokapena probatzen…",
                .missingAccessToken: "Ireki Caca Radar iPhonean eta hasi saioa berriro.",
                .invalidApiUrl: "iPhone aplikazioak zerbitzariaren URL baliogabea dauka.",
                .invalidResponse: "iPhoneak erantzun baliogabea bidali du.",
                .reportCooldown: "Itxaron 30 segundo abisuen artean.",
                .restrictedAccount: "Zure kontua aldi baterako mugatuta dago.",
                .quickReportFailed: "Ezin izan da abisua bidali.",
            ])
        default:
            return WatchCopy(values: [
                .appTitle: "Caca Radar",
                .tapToReport: "Pulsa para reportar caca aquí.",
                .sending: "Enviando...",
                .reportNow: "Reporta aquí",
                .phoneUnavailable: "Abre la app en el iPhone o acércalo al reloj.",
                .reportSent: "Aviso enviado en %@.",
                .reportConfirmed: "Se confirmó un aviso existente en %@.",
                .waitingForLocation: "Buscando tu ubicación…",
                .locationDenied: "Permite la ubicación en el reloj para enviar avisos.",
                .locationUnavailable: "No pudimos obtener tu ubicación.",
                .usingPhoneLocation: "Probando con la ubicación del iPhone…",
                .missingAccessToken: "Abre Caca Radar en el iPhone e inicia sesión de nuevo.",
                .invalidApiUrl: "La app del iPhone tiene una URL de servidor no válida.",
                .invalidResponse: "El iPhone devolvió una respuesta no válida.",
                .reportCooldown: "Espera 30 segundos entre reportes.",
                .restrictedAccount: "Tu cuenta está restringida temporalmente.",
                .quickReportFailed: "No se pudo enviar el aviso.",
            ])
        }
    }
}

final class PhoneSessionBridge: NSObject, ObservableObject, WCSessionDelegate {
    @Published var reachable = false
    @Published var preferredLanguage = PhoneSessionBridge.defaultLanguage()
    @Published var authenticated = PhoneSessionBridge.defaultAuthenticated()
    @Published var runtimeDebug = "idle"

    private static let preferredLanguageKey = "watch_preferred_language"
    private static let authenticatedKey = "watch_authenticated"
    private static let apiBaseUrlKey = "watch_api_base_url"

    private enum WatchSecureStorage {
        static let accessService = "com.jefe.cacaradar.watch.access"
        static let refreshService = "com.jefe.cacaradar.watch.refresh"
        static let account = "primary"

        static func read(service: String) -> String? {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: service,
                kSecAttrAccount as String: account,
                kSecReturnData as String: true,
                kSecMatchLimit as String: kSecMatchLimitOne,
            ]
            var item: CFTypeRef?
            let status = SecItemCopyMatching(query as CFDictionary, &item)
            guard status == errSecSuccess, let data = item as? Data else {
                return nil
            }
            let value = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)
            return value?.isEmpty == false ? value : nil
        }

        static func write(_ value: String?, service: String) {
            let trimmed = value?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            if trimmed.isEmpty {
                clear(service: service)
                return
            }

            let data = Data(trimmed.utf8)
            let baseQuery: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: service,
                kSecAttrAccount as String: account,
            ]
            let updateStatus = SecItemUpdate(
                baseQuery as CFDictionary,
                [
                    kSecValueData as String: data,
                    kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
                ] as CFDictionary
            )
            if updateStatus == errSecSuccess {
                return
            }
            guard updateStatus == errSecItemNotFound else {
                return
            }

            var addQuery = baseQuery
            addQuery[kSecValueData as String] = data
            addQuery[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
            SecItemAdd(addQuery as CFDictionary, nil)
        }

        static func clear(service: String) {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: service,
                kSecAttrAccount as String: account,
            ]
            SecItemDelete(query as CFDictionary)
        }
    }

    override init() {
        super.init()
        activate()
    }

    static func defaultLanguage() -> String {
        UserDefaults.standard.string(forKey: preferredLanguageKey)
            ?? Locale.preferredLanguages.first?.split(separator: "-").first.map(String.init)
            ?? "es"
    }

    static func defaultAuthenticated() -> Bool {
        UserDefaults.standard.bool(forKey: authenticatedKey)
            || WatchSecureStorage.read(service: WatchSecureStorage.accessService) != nil
            || WatchSecureStorage.read(service: WatchSecureStorage.refreshService) != nil
    }

    private var storedAccessToken: String? {
        WatchSecureStorage.read(service: WatchSecureStorage.accessService)
    }

    private var storedRefreshToken: String? {
        WatchSecureStorage.read(service: WatchSecureStorage.refreshService)
    }

    private var storedApiBaseUrl: String? {
        let value = UserDefaults.standard.string(forKey: Self.apiBaseUrlKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return value?.isEmpty == false ? value : nil
    }

    private var hasSyncedAuthContext: Bool {
        storedApiBaseUrl != nil && (storedAccessToken != nil || storedRefreshToken != nil)
    }

    var copy: WatchCopy {
        WatchCopyCatalog.language(preferredLanguage)
    }

    var canSubmitReport: Bool {
        hasSyncedAuthContext || reachable
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
        reachable = session.isReachable
        updateDebug("activate reachable=\(session.isReachable)")
        if let preferredLanguage = session.receivedApplicationContext["preferredLanguage"] as? String {
            updatePreferredLanguage(preferredLanguage)
        }
        if session.isReachable {
            Task { await refreshCompanionContext() }
        }
    }

    func sendQuickReport(latitude: Double, longitude: Double) async throws -> QuickReportReply {
        let phoneReachable = WCSession.default.isReachable
        updateDebug("start reachable=\(phoneReachable) synced=\(hasSyncedAuthContext)")

        if phoneReachable {
            await refreshCompanionContext()
            updateDebug("context refreshed synced=\(hasSyncedAuthContext)")
        }

        if hasSyncedAuthContext {
            do {
                updateDebug("path=direct")
                return try await sendQuickReportDirectly(latitude: latitude, longitude: longitude)
            } catch {
                let appErrorCode = (error as NSError).userInfo["appErrorCode"] as? String
                updateDebug("direct error=\(appErrorCode ?? "unknown")")
                if phoneReachable,
                   appErrorCode == "missing_access_token" || appErrorCode == "quick_report_failed" || appErrorCode == "invalid_response" || appErrorCode == "restricted_account" {
                    updateDebug("fallback=phone_relay reason=\(appErrorCode ?? "unknown")")
                    return try await sendQuickReportViaPhone(latitude: latitude, longitude: longitude)
                }
                throw error
            }
        }

        if phoneReachable {
            updateDebug("path=phone_relay_only")
            return try await sendQuickReportViaPhone(latitude: latitude, longitude: longitude)
        }

        updateDebug("error=phone_unavailable")
        throw NSError(
            domain: "PhoneSessionBridge",
            code: 1,
            userInfo: [
                NSLocalizedDescriptionKey: copy.text(.phoneUnavailable),
                "appErrorCode": "phone_unavailable",
            ]
        )
    }

    @discardableResult
    func refreshCompanionContext() async -> Bool {
        guard WCSession.default.isReachable else { return authenticated }

        do {
            let response = try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<[String: Any], Error>) in
                WCSession.default.sendMessage(
                    ["action": "companion_context"],
                    replyHandler: { response in
                        continuation.resume(returning: response)
                    },
                    errorHandler: { error in
                        continuation.resume(throwing: error)
                    }
                )
            }
            await MainActor.run {
                self.apply(applicationContext: response)
            }
            updateDebug("context ok auth=\(authenticated) synced=\(hasSyncedAuthContext)")
            return hasSyncedAuthContext || authenticated
        } catch {
            updateDebug("context error")
            return hasSyncedAuthContext || authenticated
        }
    }

    private func sendMessageWithTimeout<T>(
        _ message: [String: Any],
        timeoutSeconds: TimeInterval = 12,
        transform: @escaping ([String: Any]) throws -> T
    ) async throws -> T {
        try await withThrowingTaskGroup(of: T.self) { group in
            group.addTask {
                try await withCheckedThrowingContinuation { continuation in
                    WCSession.default.sendMessage(
                        message,
                        replyHandler: { response in
                            do {
                                continuation.resume(returning: try transform(response))
                            } catch {
                                continuation.resume(throwing: error)
                            }
                        },
                        errorHandler: { error in
                            continuation.resume(throwing: error)
                        }
                    )
                }
            }

            group.addTask {
                try await Task.sleep(nanoseconds: UInt64(timeoutSeconds * 1_000_000_000))
                self.updateDebug("timeout action=\(message["action"] as? String ?? "unknown")")
                throw NSError(
                    domain: "PhoneSessionBridge",
                    code: 408,
                    userInfo: [
                        NSLocalizedDescriptionKey: self.copy.text(.quickReportFailed),
                        "appErrorCode": "quick_report_failed",
                    ]
                )
            }

            let result = try await group.next()!
            group.cancelAll()
            return result
        }
    }

    private func sendQuickReportViaPhone(latitude: Double, longitude: Double) async throws -> QuickReportReply {
        updateDebug("relay send")
        let reply = try await sendMessageWithTimeout(
            [
                "action": "quick_report",
                "latitude": latitude,
                "longitude": longitude,
            ]
        ) { response in
            let success = response["ok"] as? Bool ?? false
            if success {
                self.updateDebug("relay ok")
                return QuickReportReply(
                    ok: true,
                    reportId: response["reportId"] as? String ?? "",
                    municipality: response["municipality"] as? String ?? "",
                    convertedToConfirmation: response["convertedToConfirmation"] as? Bool ?? false
                )
            }
            let errorCode = response["errorCode"] as? String ?? response["error"] as? String ?? "quick_report_failed"
            let errorDetail = response["errorDetail"] as? String ?? response["error"] as? String ?? errorCode
            self.updateDebug("relay error=\(errorCode)")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 2,
                userInfo: [
                    NSLocalizedDescriptionKey: errorDetail,
                    "appErrorCode": errorCode,
                ]
            )
        }

        return reply
    }

    func requestPhoneLocationCoordinate() async throws -> CLLocationCoordinate2D {
        guard WCSession.default.isReachable else {
            updateDebug("phone_coordinate error=phone_unavailable")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 1,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.phoneUnavailable),
                    "appErrorCode": "phone_unavailable",
                ]
            )
        }

        updateDebug("phone_coordinate relay")
        return try await sendMessageWithTimeout(
            ["action": "phone_coordinate"],
            timeoutSeconds: 6
        ) { response in
            let success = response["ok"] as? Bool ?? false
            if success,
               let latitude = response["latitude"] as? Double,
               let longitude = response["longitude"] as? Double {
                self.updateDebug("phone_coordinate ok")
                return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
            }

            let errorCode = response["errorCode"] as? String ?? response["error"] as? String ?? "location_unavailable"
            let errorDetail = response["errorDetail"] as? String ?? response["error"] as? String ?? errorCode
            self.updateDebug("phone_coordinate error=\(errorCode)")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 2,
                userInfo: [
                    NSLocalizedDescriptionKey: errorDetail,
                    "appErrorCode": errorCode,
                ]
            )
        }
    }

    func sendQuickReportUsingPhoneLocation() async throws -> QuickReportReply {
        guard WCSession.default.isReachable else {
            updateDebug("phone_location error=phone_unavailable")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 1,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.phoneUnavailable),
                    "appErrorCode": "phone_unavailable",
                ]
            )
        }

        updateDebug("phone_location relay")
        let reply = try await sendMessageWithTimeout(
            ["action": "quick_report_phone_location"]
        ) { response in
            let success = response["ok"] as? Bool ?? false
            if success {
                self.updateDebug("phone_location ok")
                return QuickReportReply(
                    ok: true,
                    reportId: response["reportId"] as? String ?? "",
                    municipality: response["municipality"] as? String ?? "",
                    convertedToConfirmation: response["convertedToConfirmation"] as? Bool ?? false
                )
            }
            let errorCode = response["errorCode"] as? String ?? response["error"] as? String ?? "quick_report_failed"
            let errorDetail = response["errorDetail"] as? String ?? response["error"] as? String ?? errorCode
            self.updateDebug("phone_location error=\(errorCode)")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 2,
                userInfo: [
                    NSLocalizedDescriptionKey: errorDetail,
                    "appErrorCode": errorCode,
                ]
            )
        }

        return reply
    }

    private func sendQuickReportDirectly(latitude: Double, longitude: Double) async throws -> QuickReportReply {
        let configuredBase = storedApiBaseUrl ?? "https://cacaradar.es/api"
        let apiBase = configuredBase.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: "\(apiBase)/reports/quick") else {
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 400,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.invalidApiUrl),
                    "appErrorCode": "invalid_api_url",
                ]
            )
        }

        func refreshedAccessToken() async throws -> String {
            guard let refreshToken = storedRefreshToken else {
                updateDebug("direct refresh missing_refresh")
                throw NSError(
                    domain: "PhoneSessionBridge",
                    code: 401,
                    userInfo: [
                        NSLocalizedDescriptionKey: copy.text(.missingAccessToken),
                        "appErrorCode": "missing_access_token",
                    ]
                )
            }
            updateDebug("direct refresh start")
            return try await refreshAccessToken(apiBase: apiBase, refreshToken: refreshToken)
        }

        let initialToken = try await {
            if let accessToken = storedAccessToken {
                return accessToken
            }
            return try await refreshedAccessToken()
        }()

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 15
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("ios", forHTTPHeaderField: "X-Platform")
        request.setValue("1", forHTTPHeaderField: "X-Native-App")

        func performRequest(with bearerToken: String) async throws -> (Data, HTTPURLResponse) {
            request.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization")
            request.httpBody = try JSONSerialization.data(withJSONObject: [
                "latitude": latitude,
                "longitude": longitude,
                "source": "apple_watch",
            ])

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw NSError(
                    domain: "PhoneSessionBridge",
                    code: 500,
                    userInfo: [
                        NSLocalizedDescriptionKey: copy.text(.invalidResponse),
                        "appErrorCode": "invalid_response",
                    ]
                )
            }
            return (data, http)
        }

        var (data, http) = try await performRequest(with: initialToken)
        updateDebug("direct status=\(http.statusCode)")
        if http.statusCode == 401, storedRefreshToken != nil {
            let refreshedToken = try await refreshedAccessToken()
            updateDebug("direct refreshed retry")
            (data, http) = try await performRequest(with: refreshedToken)
            updateDebug("direct retry status=\(http.statusCode)")
        }

        guard (200...299).contains(http.statusCode) else {
            let payload = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
            let detail = payload["detail"] as? String
            let appErrorCode: String
            switch http.statusCode {
            case 401:
                appErrorCode = "missing_access_token"
            case 403:
                appErrorCode = "restricted_account"
            case 429:
                appErrorCode = "report_cooldown"
            default:
                appErrorCode = "quick_report_failed"
            }
            throw NSError(
                domain: "PhoneSessionBridge",
                code: http.statusCode,
                userInfo: [
                    NSLocalizedDescriptionKey: detail ?? appErrorCode,
                    "appErrorCode": appErrorCode,
                ]
            )
        }

        let payload = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
        updateDebug("direct ok")
        return QuickReportReply(
            ok: true,
            reportId: payload["id"] as? String ?? "",
            municipality: payload["municipality"] as? String ?? "",
            convertedToConfirmation: payload["converted_to_confirmation"] as? Bool ?? false
        )
    }

    private func refreshAccessToken(apiBase: String, refreshToken: String) async throws -> String {
        guard let refreshUrl = URL(string: "\(apiBase)/auth/refresh") else {
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 400,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.invalidApiUrl),
                    "appErrorCode": "invalid_api_url",
                ]
            )
        }

        var request = URLRequest(url: refreshUrl)
        request.httpMethod = "POST"
        request.timeoutInterval = 15
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("ios", forHTTPHeaderField: "X-Platform")
        request.setValue("1", forHTTPHeaderField: "X-Native-App")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "refresh_token": refreshToken,
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 500,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.invalidResponse),
                    "appErrorCode": "invalid_response",
                ]
            )
        }
        guard (200...299).contains(http.statusCode),
              let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let accessToken = payload["access_token"] as? String,
              !accessToken.isEmpty else {
            updateDebug("refresh error status=\(http.statusCode)")
            throw NSError(
                domain: "PhoneSessionBridge",
                code: http.statusCode,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.missingAccessToken),
                    "appErrorCode": "missing_access_token",
                ]
            )
        }

        WatchSecureStorage.write(accessToken, service: WatchSecureStorage.accessService)
        WatchSecureStorage.write(refreshToken, service: WatchSecureStorage.refreshService)
        updateDebug("refresh ok")
        return accessToken
    }

    func localizedMessage(for error: Error) -> String {
        let appErrorCode = (error as NSError).userInfo["appErrorCode"] as? String
        switch appErrorCode {
        case "phone_unavailable":
            return copy.text(.phoneUnavailable)
        case "missing_access_token":
            return copy.text(.missingAccessToken)
        case "invalid_api_url":
            return copy.text(.invalidApiUrl)
        case "invalid_response":
            return copy.text(.invalidResponse)
        case "report_cooldown":
            return copy.text(.reportCooldown)
        case "restricted_account":
            return copy.text(.restrictedAccount)
        case "location_permission_denied":
            return copy.text(.locationDenied)
        case "location_unavailable":
            return copy.text(.locationUnavailable)
        default:
            let message = (error as NSError).localizedDescription
            if message == "The operation couldn’t be completed." || message == "The operation could not be completed." {
                return copy.text(.quickReportFailed)
            }
            return message
        }
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        reachable = session.isReachable
        updateDebug("activation state=\(activationState.rawValue) reachable=\(session.isReachable)")
        apply(applicationContext: session.receivedApplicationContext)
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        reachable = session.isReachable
        updateDebug("reachability=\(session.isReachable)")
        if session.isReachable {
            Task { await refreshCompanionContext() }
        }
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String : Any]) {
        DispatchQueue.main.async {
            self.apply(applicationContext: applicationContext)
        }
    }

    private func updatePreferredLanguage(_ language: String) {
        preferredLanguage = language
        UserDefaults.standard.set(language, forKey: Self.preferredLanguageKey)
    }

    private func apply(applicationContext: [String: Any]) {
        var authStateForDebug = authenticated
        if let preferredLanguage = applicationContext["preferredLanguage"] as? String {
            updatePreferredLanguage(preferredLanguage)
        }
        if let accessToken = applicationContext["accessToken"] as? String, !accessToken.isEmpty {
            WatchSecureStorage.write(accessToken, service: WatchSecureStorage.accessService)
        }
        if let refreshToken = applicationContext["refreshToken"] as? String, !refreshToken.isEmpty {
            WatchSecureStorage.write(refreshToken, service: WatchSecureStorage.refreshService)
        }
        if let apiBaseUrl = applicationContext["apiBaseUrl"] as? String, !apiBaseUrl.isEmpty {
            UserDefaults.standard.set(apiBaseUrl, forKey: Self.apiBaseUrlKey)
        }
        if let authenticated = applicationContext["authenticated"] as? Bool {
            self.authenticated = authenticated
            authStateForDebug = authenticated
            UserDefaults.standard.set(authenticated, forKey: Self.authenticatedKey)
            if !authenticated {
                WatchSecureStorage.clear(service: WatchSecureStorage.accessService)
                WatchSecureStorage.clear(service: WatchSecureStorage.refreshService)
                UserDefaults.standard.removeObject(forKey: Self.apiBaseUrlKey)
            }
        } else {
            self.authenticated = hasSyncedAuthContext
            authStateForDebug = self.authenticated
        }
        updateDebug("apply auth=\(authStateForDebug) synced=\(hasSyncedAuthContext)")
    }

    private func updateDebug(_ message: String) {
        DispatchQueue.main.async {
            self.runtimeDebug = message
        }
    }
}

struct QuickReportReply {
    let ok: Bool
    let reportId: String
    let municipality: String
    let convertedToConfirmation: Bool
}
