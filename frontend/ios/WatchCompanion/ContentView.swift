import CoreLocation
import SwiftUI

enum WatchLocationError: LocalizedError {
    case permissionDenied
    case locationUnavailable
    case timeout
}

final class WatchLocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var continuation: CheckedContinuation<CLLocationCoordinate2D, Error>?
    private var waitingForAuthorization = false
    private var timeoutTask: Task<Void, Never>?
    private let staleLocationThreshold: TimeInterval = 90
    private let requestTimeout: TimeInterval = 12

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
        if !CLLocationManager.locationServicesEnabled() {
            throw WatchLocationError.locationUnavailable
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

        switch result {
        case .success(let coordinate):
            continuation.resume(returning: coordinate)
        case .failure(let error):
            continuation.resume(throwing: error)
        }
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
                self.finish(with: .failure(WatchLocationError.timeout))
            }
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard waitingForAuthorization else { return }

        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            startLocationAcquisition()
        case .denied, .restricted:
            finish(with: .failure(WatchLocationError.permissionDenied))
        default:
            break
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last(where: { $0.horizontalAccuracy > 0 }) ?? locations.last else {
            finish(with: .failure(WatchLocationError.locationUnavailable))
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
        finish(with: .failure(error))
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
                .font(.system(.footnote, design: .rounded).weight(.medium))
                .multilineTextAlignment(.center)
                .lineLimit(5)
                .minimumScaleFactor(0.72)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity)
                .foregroundStyle(.white.opacity(0.85))

            Button {
                Task { await submitQuickReport() }
            } label: {
                HStack {
                    Image(systemName: "location.fill")
                    Text(isSubmitting ? copy.text(.sending) : copy.text(.reportNow))
                        .lineLimit(2)
                        .minimumScaleFactor(0.78)
                        .multilineTextAlignment(.center)
                }
                .font(.system(.body, design: .rounded).weight(.semibold))
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
            .disabled(isSubmitting || !bridge.canSubmitReport)

            if !bridge.canSubmitReport {
                Text(copy.text(.phoneUnavailable))
                    .font(.caption2)
                    .multilineTextAlignment(.center)
                    .lineLimit(4)
                    .minimumScaleFactor(0.72)
                    .fixedSize(horizontal: false, vertical: true)
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
        } catch WatchLocationError.timeout {
            statusText = copy.text(.locationUnavailable)
        } catch WatchLocationError.locationUnavailable {
            statusText = copy.text(.locationUnavailable)
        } catch {
            statusText = bridge.localizedMessage(for: error)
        }
    }
}
