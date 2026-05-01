import Foundation
import WatchConnectivity

final class PhoneSessionBridge: NSObject, ObservableObject, WCSessionDelegate {
    @Published var reachable = false

    override init() {
        super.init()
        activate()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
        reachable = session.isReachable
    }

    func sendQuickReport(latitude: Double, longitude: Double) async throws -> QuickReportReply {
        guard WCSession.default.isReachable else {
            throw NSError(domain: "PhoneSessionBridge", code: 1, userInfo: [NSLocalizedDescriptionKey: "El iPhone no está disponible"])
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
                        let error = response["error"] as? String ?? "No se pudo enviar el reporte"
                        continuation.resume(throwing: NSError(domain: "PhoneSessionBridge", code: 2, userInfo: [NSLocalizedDescriptionKey: error]))
                    }
                },
                errorHandler: { error in
                    continuation.resume(throwing: error)
                }
            )
        }

        return reply
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        reachable = session.isReachable
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        reachable = session.isReachable
    }
}

struct QuickReportReply {
    let ok: Bool
    let reportId: String
    let municipality: String
    let convertedToConfirmation: Bool
}
