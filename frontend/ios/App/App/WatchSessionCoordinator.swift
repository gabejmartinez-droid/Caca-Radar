import Foundation
import WatchConnectivity

private enum WatchCompanionStorage {
    static let accessTokenKey = "companion.accessToken"
    static let apiBaseUrlKey = "companion.apiBaseUrl"
}

final class WatchSessionCoordinator: NSObject, WCSessionDelegate {
    static let shared = WatchSessionCoordinator()

    private override init() {
        super.init()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) {
        session.activate()
    }

    func session(_ session: WCSession, didReceiveMessage message: [String : Any], replyHandler: @escaping ([String : Any]) -> Void) {
        guard let action = message["action"] as? String, action == "quick_report" else {
            replyHandler(["ok": false, "error": "unsupported_action"])
            return
        }

        guard let latitude = message["latitude"] as? Double,
              let longitude = message["longitude"] as? Double else {
            replyHandler(["ok": false, "error": "missing_coordinates"])
            return
        }

        Task {
            do {
                let result = try await sendQuickReport(latitude: latitude, longitude: longitude)
                replyHandler(result)
            } catch {
                replyHandler([
                    "ok": false,
                    "error": error.localizedDescription,
                ])
            }
        }
    }

    private func sendQuickReport(latitude: Double, longitude: Double) async throws -> [String: Any] {
        let defaults = UserDefaults.standard
        guard let token = defaults.string(forKey: WatchCompanionStorage.accessTokenKey), !token.isEmpty else {
            throw NSError(domain: "WatchSessionCoordinator", code: 401, userInfo: [NSLocalizedDescriptionKey: "missing_access_token"])
        }

        let configuredBase = defaults.string(forKey: WatchCompanionStorage.apiBaseUrlKey)?.trimmingCharacters(in: .whitespacesAndNewlines)
        let apiBase = (configuredBase?.isEmpty == false ? configuredBase! : "https://cacaradar.es/api").trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: "\(apiBase)/reports/quick") else {
            throw NSError(domain: "WatchSessionCoordinator", code: 400, userInfo: [NSLocalizedDescriptionKey: "invalid_api_url"])
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "latitude": latitude,
            "longitude": longitude,
            "source": "apple_watch",
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw NSError(domain: "WatchSessionCoordinator", code: 500, userInfo: [NSLocalizedDescriptionKey: "invalid_response"])
        }

        guard (200...299).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw NSError(domain: "WatchSessionCoordinator", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: detail ?? "quick_report_failed"])
        }

        let payload = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
        return [
            "ok": true,
            "reportId": payload["id"] as? String ?? "",
            "municipality": payload["municipality"] as? String ?? "",
            "convertedToConfirmation": payload["converted_to_confirmation"] as? Bool ?? false,
        ]
    }
}
