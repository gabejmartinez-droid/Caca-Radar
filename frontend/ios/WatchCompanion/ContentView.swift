import CoreLocation
import SwiftUI

final class WatchLocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var continuation: CheckedContinuation<CLLocationCoordinate2D, Error>?

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
    }

    func requestCurrentLocation() async throws -> CLLocationCoordinate2D {
        if manager.authorizationStatus == .notDetermined {
            manager.requestWhenInUseAuthorization()
        }
        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            manager.requestLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else { return }
        continuation?.resume(returning: location.coordinate)
        continuation = nil
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        continuation?.resume(throwing: error)
        continuation = nil
    }
}

struct ContentView: View {
    @StateObject private var bridge = PhoneSessionBridge()
    @StateObject private var locationManager = WatchLocationManager()
    @State private var statusText = "Pulsa para reportar caca aquí"
    @State private var isSubmitting = false

    var body: some View {
        VStack(spacing: 12) {
            Text("Caca Radar")
                .font(.headline)
                .foregroundStyle(.white)

            Text(statusText)
                .font(.footnote)
                .multilineTextAlignment(.center)
                .foregroundStyle(.white.opacity(0.85))

            Button {
                Task { await submitQuickReport() }
            } label: {
                HStack {
                    Image(systemName: "location.fill")
                    Text(isSubmitting ? "Enviando..." : "Reportar ahora")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
            .disabled(isSubmitting || !bridge.reachable)

            if !bridge.reachable {
                Text("Abre la app en el iPhone o acércalo al reloj.")
                    .font(.caption2)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.yellow)
            }
        }
        .padding()
        .background(Color.black)
    }

    @MainActor
    private func submitQuickReport() async {
        isSubmitting = true
        defer { isSubmitting = false }

        do {
            let coordinate = try await locationManager.requestCurrentLocation()
            let result = try await bridge.sendQuickReport(latitude: coordinate.latitude, longitude: coordinate.longitude)
            if result.convertedToConfirmation {
                statusText = "Se confirmó un aviso existente en \(result.municipality)."
            } else {
                statusText = "Aviso enviado en \(result.municipality)."
            }
        } catch {
            statusText = error.localizedDescription
        }
    }
}
