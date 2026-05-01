import CoreLocation
import SwiftUI

enum WatchLocationError: LocalizedError {
    case permissionDenied
    case locationUnavailable
}

final class WatchLocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var continuation: CheckedContinuation<CLLocationCoordinate2D, Error>?
    private var waitingForAuthorization = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
    }

    func requestCurrentLocation() async throws -> CLLocationCoordinate2D {
        let status = manager.authorizationStatus
        if status == .denied || status == .restricted {
            throw WatchLocationError.permissionDenied
        }

        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation

            if status == .notDetermined {
                waitingForAuthorization = true
                manager.requestWhenInUseAuthorization()
            } else {
                manager.requestLocation()
            }
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard waitingForAuthorization else { return }

        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            waitingForAuthorization = false
            manager.requestLocation()
        case .denied, .restricted:
            waitingForAuthorization = false
            continuation?.resume(throwing: WatchLocationError.permissionDenied)
            continuation = nil
        default:
            break
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else {
            continuation?.resume(throwing: WatchLocationError.locationUnavailable)
            continuation = nil
            return
        }
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
    @State private var statusText = PhoneSessionBridge.defaultLanguage() == "en"
        ? "Tap to report poop here."
        : "Pulsa para reportar caca aquí."
    @State private var isSubmitting = false

    var body: some View {
        let copy = bridge.copy

        VStack(spacing: 12) {
            Text(copy.text(.appTitle))
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
                    Text(isSubmitting ? copy.text(.sending) : copy.text(.reportNow))
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
            .disabled(isSubmitting || !bridge.reachable)

            if !bridge.reachable {
                Text(copy.text(.phoneUnavailable))
                    .font(.caption2)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.yellow)
            }
        }
        .padding()
        .background(Color.black)
        .onChange(of: bridge.preferredLanguage) {
            if !isSubmitting {
                statusText = bridge.copy.text(.tapToReport)
            }
        }
    }

    @MainActor
    private func submitQuickReport() async {
        isSubmitting = true
        defer { isSubmitting = false }

        let copy = bridge.copy
        statusText = copy.text(.waitingForLocation)

        do {
            let coordinate = try await locationManager.requestCurrentLocation()
            let result = try await bridge.sendQuickReport(latitude: coordinate.latitude, longitude: coordinate.longitude)
            if result.convertedToConfirmation {
                statusText = String(format: copy.text(.reportConfirmed), result.municipality)
            } else {
                statusText = String(format: copy.text(.reportSent), result.municipality)
            }
        } catch WatchLocationError.permissionDenied {
            statusText = copy.text(.locationDenied)
        } catch WatchLocationError.locationUnavailable {
            statusText = copy.text(.locationUnavailable)
        } catch {
            statusText = bridge.localizedMessage(for: error)
        }
    }
}
