import Foundation
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
                .reportNow: "Report now",
                .phoneUnavailable: "Open the iPhone app or bring it closer to the watch.",
                .reportSent: "Report sent in %@.",
                .reportConfirmed: "Existing report confirmed in %@.",
                .waitingForLocation: "Getting your location…",
                .locationDenied: "Allow location access on the watch to send reports.",
                .locationUnavailable: "We couldn't get your location.",
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
                .reportNow: "Jetzt melden",
                .phoneUnavailable: "Öffne die iPhone-App oder bringe das iPhone näher an die Uhr.",
                .reportSent: "Meldung in %@ gesendet.",
                .reportConfirmed: "Bestehende Meldung in %@ bestätigt.",
                .waitingForLocation: "Standort wird ermittelt…",
                .locationDenied: "Erlaube den Standortzugriff auf der Uhr, um Meldungen zu senden.",
                .locationUnavailable: "Der Standort konnte nicht ermittelt werden.",
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
                .reportNow: "Nu melden",
                .phoneUnavailable: "Open de iPhone-app of houd de iPhone dichter bij het horloge.",
                .reportSent: "Melding verzonden in %@.",
                .reportConfirmed: "Bestaande melding bevestigd in %@.",
                .waitingForLocation: "Locatie ophalen…",
                .locationDenied: "Geef locatie-toegang op het horloge om meldingen te versturen.",
                .locationUnavailable: "We konden je locatie niet ophalen.",
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
                .reportNow: "Zgłoś teraz",
                .phoneUnavailable: "Otwórz aplikację na iPhonie lub zbliż iPhone'a do zegarka.",
                .reportSent: "Zgłoszenie wysłane w %@.",
                .reportConfirmed: "Istniejące zgłoszenie potwierdzone w %@.",
                .waitingForLocation: "Pobieranie lokalizacji…",
                .locationDenied: "Zezwól zegarkowi na dostęp do lokalizacji, aby wysyłać zgłoszenia.",
                .locationUnavailable: "Nie udało się pobrać lokalizacji.",
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
                .reportNow: "Повідомити",
                .phoneUnavailable: "Відкрийте застосунок на iPhone або піднесіть iPhone ближче до годинника.",
                .reportSent: "Звіт надіслано в %@.",
                .reportConfirmed: "Наявний звіт підтверджено в %@.",
                .waitingForLocation: "Отримуємо геопозицію…",
                .locationDenied: "Дозвольте доступ до геопозиції на годиннику, щоб надсилати звіти.",
                .locationUnavailable: "Не вдалося отримати вашу геопозицію.",
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
                .reportNow: "Сообщить",
                .phoneUnavailable: "Откройте приложение на iPhone или поднесите iPhone ближе к часам.",
                .reportSent: "Сообщение отправлено в %@.",
                .reportConfirmed: "Существующее сообщение подтверждено в %@.",
                .waitingForLocation: "Получаем геопозицию…",
                .locationDenied: "Разрешите доступ к геопозиции на часах, чтобы отправлять сообщения.",
                .locationUnavailable: "Не удалось получить вашу геопозицию.",
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
                .reportNow: "Informa ara",
                .phoneUnavailable: "Obre l'app a l'iPhone o acosta'l més al rellotge.",
                .reportSent: "Avís enviat a %@.",
                .reportConfirmed: "Avís existent confirmat a %@.",
                .waitingForLocation: "Obtenint la ubicació…",
                .locationDenied: "Permet l'accés a la ubicació al rellotge per enviar avisos.",
                .locationUnavailable: "No hem pogut obtenir la teva ubicació.",
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
                .reportNow: "Informa ara",
                .phoneUnavailable: "Obri l'app a l'iPhone o acosta'l més al rellotge.",
                .reportSent: "Avís enviat a %@.",
                .reportConfirmed: "Avís existent confirmat a %@.",
                .waitingForLocation: "Obtenint la ubicació…",
                .locationDenied: "Permet l'accés a la ubicació al rellotge per a enviar avisos.",
                .locationUnavailable: "No hem pogut obtindre la teua ubicació.",
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
                .reportNow: "Jakinarazi orain",
                .phoneUnavailable: "Ireki iPhone aplikazioa edo hurbildu iPhonea erlojuara.",
                .reportSent: "Abisua %@ herrian bidali da.",
                .reportConfirmed: "Lehendik zegoen abisua %@ herrian baieztatu da.",
                .waitingForLocation: "Kokapena lortzen…",
                .locationDenied: "Baimendu kokapena erlojuan abisuak bidaltzeko.",
                .locationUnavailable: "Ezin izan dugu zure kokapena lortu.",
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
                .reportNow: "Reportar ahora",
                .phoneUnavailable: "Abre la app en el iPhone o acércalo al reloj.",
                .reportSent: "Aviso enviado en %@.",
                .reportConfirmed: "Se confirmó un aviso existente en %@.",
                .waitingForLocation: "Buscando tu ubicación…",
                .locationDenied: "Permite la ubicación en el reloj para enviar avisos.",
                .locationUnavailable: "No pudimos obtener tu ubicación.",
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

    private static let preferredLanguageKey = "watch_preferred_language"

    override init() {
        super.init()
        activate()
    }

    static func defaultLanguage() -> String {
        UserDefaults.standard.string(forKey: preferredLanguageKey)
            ?? Locale.preferredLanguages.first?.split(separator: "-").first.map(String.init)
            ?? "es"
    }

    var copy: WatchCopy {
        WatchCopyCatalog.language(preferredLanguage)
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
        reachable = session.isReachable
        if let preferredLanguage = session.receivedApplicationContext["preferredLanguage"] as? String {
            updatePreferredLanguage(preferredLanguage)
        }
    }

    func sendQuickReport(latitude: Double, longitude: Double) async throws -> QuickReportReply {
        guard WCSession.default.isReachable else {
            throw NSError(
                domain: "PhoneSessionBridge",
                code: 1,
                userInfo: [
                    NSLocalizedDescriptionKey: copy.text(.phoneUnavailable),
                    "appErrorCode": "phone_unavailable",
                ]
            )
        }

        let reply = try await withCheckedThrowingContinuation { continuation in
            WCSession.default.sendMessage(
                [
                    "action": "quick_report",
                    "latitude": latitude,
                    "longitude": longitude,
                ],
                replyHandler: { response in
                    let success = response["ok"] as? Bool ?? false
                    if success {
                        continuation.resume(returning: QuickReportReply(
                            ok: true,
                            reportId: response["reportId"] as? String ?? "",
                            municipality: response["municipality"] as? String ?? "",
                            convertedToConfirmation: response["convertedToConfirmation"] as? Bool ?? false
                        ))
                    } else {
                        let errorCode = response["errorCode"] as? String ?? response["error"] as? String ?? "quick_report_failed"
                        let errorDetail = response["errorDetail"] as? String ?? response["error"] as? String ?? errorCode
                        continuation.resume(throwing: NSError(
                            domain: "PhoneSessionBridge",
                            code: 2,
                            userInfo: [
                                NSLocalizedDescriptionKey: errorDetail,
                                "appErrorCode": errorCode,
                            ]
                        ))
                    }
                },
                errorHandler: { error in
                    continuation.resume(throwing: error)
                }
            )
        }

        return reply
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
        if let preferredLanguage = session.receivedApplicationContext["preferredLanguage"] as? String {
            updatePreferredLanguage(preferredLanguage)
        }
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        reachable = session.isReachable
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String : Any]) {
        if let preferredLanguage = applicationContext["preferredLanguage"] as? String {
            DispatchQueue.main.async {
                self.updatePreferredLanguage(preferredLanguage)
            }
        }
    }

    private func updatePreferredLanguage(_ language: String) {
        preferredLanguage = language
        UserDefaults.standard.set(language, forKey: Self.preferredLanguageKey)
    }
}

struct QuickReportReply {
    let ok: Bool
    let reportId: String
    let municipality: String
    let convertedToConfirmation: Bool
}
