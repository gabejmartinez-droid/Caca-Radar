import CoreLocation
import Foundation
import WatchConnectivity

private enum WatchCompanionStorage {
    static let accessTokenKey = "companion.accessToken"
    static let refreshTokenKey = "companion.refreshToken"
    static let apiBaseUrlKey = "companion.apiBaseUrl"
    static let preferredLanguageKey = "companion.preferredLanguage"
}

final class WatchSessionCoordinator: NSObject, WCSessionDelegate {
    static let shared = WatchSessionCoordinator()
    private let phoneLocationProvider = PhoneQuickReportLocationProvider()

    private override init() {
        super.init()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        pushCompanionContext()
    }
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) {
        session.activate()
    }

    func pushCompanionContext() {
        guard WCSession.isSupported() else { return }
        try? WCSession.default.updateApplicationContext(currentCompanionContext())
    }

    func session(_ session: WCSession, didReceiveMessage message: [String : Any], replyHandler: @escaping ([String : Any]) -> Void) {
        guard let action = message["action"] as? String else {
            replyHandler(["ok": false, "error": "unsupported_action"])
            return
        }

        Task {
            do {
                let result: [String: Any]
                switch action {
                case "companion_context":
                    pushCompanionContext()
                    replyHandler(currentCompanionContext())
                    return
                case "quick_report":
                    guard let latitude = message["latitude"] as? Double,
                          let longitude = message["longitude"] as? Double else {
                        replyHandler(["ok": false, "error": "missing_coordinates"])
                        return
                    }
                    result = try await sendQuickReport(latitude: latitude, longitude: longitude)
                case "quick_report_phone_location":
                    let coordinate = try await phoneLocationProvider.requestCurrentLocation()
                    result = try await sendQuickReport(latitude: coordinate.latitude, longitude: coordinate.longitude)
                default:
                    replyHandler(["ok": false, "error": "unsupported_action"])
                    return
                }
                replyHandler(result)
            } catch {
                let nsError = error as NSError
                replyHandler([
                    "ok": false,
                    "error": nsError.userInfo["appErrorCode"] as? String ?? nsError.localizedDescription,
                    "errorCode": nsError.userInfo["appErrorCode"] as? String ?? "quick_report_failed",
                    "errorDetail": nsError.localizedDescription,
                ])
            }
        }
    }

    private func currentCompanionContext() -> [String: Any] {
        let defaults = UserDefaults.standard
        let preferredLanguage = defaults.string(forKey: WatchCompanionStorage.preferredLanguageKey) ?? "es"
        let accessToken = defaults.string(forKey: WatchCompanionStorage.accessTokenKey) ?? ""
        let refreshToken = defaults.string(forKey: WatchCompanionStorage.refreshTokenKey) ?? ""
        let apiBaseUrl = defaults.string(forKey: WatchCompanionStorage.apiBaseUrlKey) ?? ""
        let hasAccessToken = !accessToken.isEmpty
        let hasRefreshToken = !refreshToken.isEmpty

        return [
            "preferredLanguage": preferredLanguage,
            "authenticated": hasAccessToken || hasRefreshToken,
            "accessToken": accessToken,
            "apiBaseUrl": apiBaseUrl,
        ]
    }

    private func sendQuickReport(latitude: Double, longitude: Double) async throws -> [String: Any] {
        let defaults = UserDefaults.standard
        let refreshToken = defaults.string(forKey: WatchCompanionStorage.refreshTokenKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        let configuredBase = defaults.string(forKey: WatchCompanionStorage.apiBaseUrlKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        let apiBase = (configuredBase?.isEmpty == false ? configuredBase! : "https://cacaradar.es/api").trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: "\(apiBase)/reports/quick") else {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: 400,
                userInfo: [
                    NSLocalizedDescriptionKey: "invalid_api_url",
                    "appErrorCode": "invalid_api_url",
                ]
            )
        }

        var token = defaults.string(forKey: WatchCompanionStorage.accessTokenKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        if token?.isEmpty != false {
            guard let refreshToken, !refreshToken.isEmpty else {
                throw NSError(
                    domain: "WatchSessionCoordinator",
                    code: 401,
                    userInfo: [
                        NSLocalizedDescriptionKey: "missing_access_token",
                        "appErrorCode": "missing_access_token",
                    ]
                )
            }
            token = try await refreshAccessToken(apiBase: apiBase, refreshToken: refreshToken)
        }

        func performRequest(with bearerToken: String) async throws -> (Data, HTTPURLResponse) {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization")
            request.httpBody = try JSONSerialization.data(withJSONObject: [
                "latitude": latitude,
                "longitude": longitude,
                "source": "apple_watch",
            ])

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw NSError(
                    domain: "WatchSessionCoordinator",
                    code: 500,
                    userInfo: [
                        NSLocalizedDescriptionKey: "invalid_response",
                        "appErrorCode": "invalid_response",
                    ]
                )
            }
            return (data, http)
        }

        let initialToken = token ?? ""
        var payloadData: Data
        var http: HTTPURLResponse

        do {
            (payloadData, http) = try await performRequest(with: initialToken)
        } catch {
            throw error
        }

        if http.statusCode == 401, let refreshToken, !refreshToken.isEmpty {
            let refreshedToken = try await refreshAccessToken(apiBase: apiBase, refreshToken: refreshToken)
            (payloadData, http) = try await performRequest(with: refreshedToken)
        }

        guard (200...299).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any])?["detail"] as? String
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
                domain: "WatchSessionCoordinator",
                code: http.statusCode,
                userInfo: [
                    NSLocalizedDescriptionKey: detail ?? appErrorCode,
                    "appErrorCode": appErrorCode,
                ]
            )
        }

        let payload = (try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any]) ?? [:]
        return [
            "ok": true,
            "reportId": payload["id"] as? String ?? "",
            "municipality": payload["municipality"] as? String ?? "",
            "convertedToConfirmation": payload["converted_to_confirmation"] as? Bool ?? false,
        ]
    }

    private func refreshAccessToken(apiBase: String, refreshToken: String) async throws -> String {
        guard let refreshUrl = URL(string: "\(apiBase)/auth/refresh") else {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: 400,
                userInfo: [
                    NSLocalizedDescriptionKey: "invalid_api_url",
                    "appErrorCode": "invalid_api_url",
                ]
            )
        }

        var request = URLRequest(url: refreshUrl)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "refresh_token": refreshToken,
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: 500,
                userInfo: [
                    NSLocalizedDescriptionKey: "invalid_response",
                    "appErrorCode": "invalid_response",
                ]
            )
        }
        guard (200...299).contains(http.statusCode),
              let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let accessToken = payload["access_token"] as? String,
              !accessToken.isEmpty else {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: http.statusCode,
                userInfo: [
                    NSLocalizedDescriptionKey: "missing_access_token",
                    "appErrorCode": "missing_access_token",
                ]
            )
        }

        let defaults = UserDefaults.standard
        defaults.set(accessToken, forKey: WatchCompanionStorage.accessTokenKey)
        defaults.set(apiBase, forKey: WatchCompanionStorage.apiBaseUrlKey)
        defaults.synchronize()
        pushCompanionContext()
        return accessToken
    }
}

private final class PhoneQuickReportLocationProvider: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var continuation: CheckedContinuation<CLLocationCoordinate2D, Error>?
    private var waitingForAuthorization = false
    private var timeoutTask: Task<Void, Never>?
    private let staleLocationThreshold: TimeInterval = 120
    private let requestTimeout: TimeInterval = 12

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
    }

    func requestCurrentLocation() async throws -> CLLocationCoordinate2D {
        let status = manager.authorizationStatus
        if status == .denied || status == .restricted {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: 403,
                userInfo: [
                    NSLocalizedDescriptionKey: "location_permission_denied",
                    "appErrorCode": "location_permission_denied",
                ]
            )
        }
        if !CLLocationManager.locationServicesEnabled() {
            throw NSError(
                domain: "WatchSessionCoordinator",
                code: 500,
                userInfo: [
                    NSLocalizedDescriptionKey: "location_unavailable",
                    "appErrorCode": "location_unavailable",
                ]
            )
        }
        if let cachedLocation = currentUsableLocation() {
            return cachedLocation.coordinate
        }

        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            self.startTimeout()

            if status == .notDetermined {
                waitingForAuthorization = true
                manager.requestWhenInUseAuthorization()
            } else {
                startLocationAcquisition()
            }
        }
    }

    private func startLocationAcquisition() {
        manager.startUpdatingLocation()
        manager.requestLocation()
    }

    private func currentUsableLocation() -> CLLocation? {
        guard let location = manager.location else { return nil }
        guard location.horizontalAccuracy > 0 else { return nil }
        guard abs(location.timestamp.timeIntervalSinceNow) <= staleLocationThreshold else { return nil }
        return location
    }

    private func finish(with result: Result<CLLocationCoordinate2D, Error>) {
        timeoutTask?.cancel()
        timeoutTask = nil
        waitingForAuthorization = false
        manager.stopUpdatingLocation()

        guard let continuation else { return }
        self.continuation = nil
        continuation.resume(with: result)
    }

    private func startTimeout() {
        timeoutTask?.cancel()
        timeoutTask = Task { [weak self] in
            guard let self else { return }
            try? await Task.sleep(nanoseconds: UInt64(requestTimeout * 1_000_000_000))
            guard !Task.isCancelled else { return }
            if let cachedLocation = self.currentUsableLocation() {
                self.finish(with: .success(cachedLocation.coordinate))
            } else {
                self.finish(with: .failure(NSError(
                    domain: "WatchSessionCoordinator",
                    code: 408,
                    userInfo: [
                        NSLocalizedDescriptionKey: "location_unavailable",
                        "appErrorCode": "location_unavailable",
                    ]
                )))
            }
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard waitingForAuthorization else { return }

        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            startLocationAcquisition()
        case .denied, .restricted:
            finish(with: .failure(NSError(
                domain: "WatchSessionCoordinator",
                code: 403,
                userInfo: [
                    NSLocalizedDescriptionKey: "location_permission_denied",
                    "appErrorCode": "location_permission_denied",
                ]
            )))
        default:
            break
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last(where: { $0.horizontalAccuracy > 0 }) ?? locations.last else {
            finish(with: .failure(NSError(
                domain: "WatchSessionCoordinator",
                code: 500,
                userInfo: [
                    NSLocalizedDescriptionKey: "location_unavailable",
                    "appErrorCode": "location_unavailable",
                ]
            )))
            return
        }
        finish(with: .success(location.coordinate))
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        let nsError = error as NSError
        if nsError.domain == kCLErrorDomain,
           nsError.code == CLError.locationUnknown.rawValue {
            return
        }
        finish(with: .failure(NSError(
            domain: "WatchSessionCoordinator",
            code: nsError.code,
            userInfo: [
                NSLocalizedDescriptionKey: "location_unavailable",
                "appErrorCode": "location_unavailable",
            ]
        )))
    }
}
