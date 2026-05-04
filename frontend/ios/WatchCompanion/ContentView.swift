import CoreLocation
import SwiftUI

enum WatchLocationError: LocalizedError {
    case permissionDenied
    case locationUnavailable
    case timeout
}

private enum CoordinatedLocationSource {
    case watch
    case phone
}

private enum CoordinatedLocationResult {
    case success(CLLocationCoordinate2D, CoordinatedLocationSource)
    case failure(Error)
}

final class WatchLocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var continuation: CheckedContinuation<CLLocationCoordinate2D, Error>?
    private var waitingForAuthorization = false
    private var timeoutTask: Task<Void, Never>?
    private let staleLocationThreshold: TimeInterval = 300
    private let requestTimeout: TimeInterval = 3

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

        return try await withTaskCancellationHandler(operation: {
            try await withCheckedThrowingContinuation { continuation in
                self.continuation = continuation
                self.startTimeout()

                if status == .notDetermined {
                    waitingForAuthorization = true
                    manager.requestWhenInUseAuthorization()
                } else {
                    startLocationAcquisition()
                }
            }
        }, onCancel: { [weak self] in
            self?.cancelPendingRequest()
        })
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

    private func cancelPendingRequest() {
        timeoutTask?.cancel()
        timeoutTask = nil
        waitingForAuthorization = false
        manager.stopUpdatingLocation()
        guard let continuation else { return }
        self.continuation = nil
        continuation.resume(throwing: CancellationError())
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
    @State private var statusText = PhoneSessionBridge.defaultAuthenticated()
        ? (PhoneSessionBridge.defaultLanguage() == "en"
            ? "Tap to report poop here."
            : "Pulsa para reportar caca aquí.")
        : (PhoneSessionBridge.defaultLanguage() == "en"
            ? "Open Caca Radar on the iPhone and sign in again."
            : "Abre Caca Radar en el iPhone e inicia sesión de nuevo.")
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
        }
        .padding()
        .background(Color.black)
        .onChange(of: bridge.preferredLanguage) {
            if !isSubmitting {
                statusText = idleStatusText()
            }
        }
        .onChange(of: bridge.reachable) {
            if !isSubmitting {
                statusText = idleStatusText()
            }
        }
        .onChange(of: bridge.authenticated) {
            if !isSubmitting {
                statusText = idleStatusText()
            }
        }
        .task {
            statusText = idleStatusText()
            _ = await bridge.refreshCompanionContext()
            if !isSubmitting {
                statusText = idleStatusText()
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
            let coordinate = try await fastestAvailableCoordinate()
            statusText = copy.text(.sending)
            let result = try await bridge.sendQuickReport(latitude: coordinate.latitude, longitude: coordinate.longitude)
            apply(result: result, copy: copy)
        } catch {
            statusText = bridge.localizedMessage(for: error)
        }
    }

    private func fastestAvailableCoordinate() async throws -> CLLocationCoordinate2D {
        if !bridge.reachable {
            return try await locationManager.requestCurrentLocation()
        }

        var failures: [Error] = []

        return try await withThrowingTaskGroup(of: CoordinatedLocationResult.self) { group in
            group.addTask {
                do {
                    let coordinate = try await self.locationManager.requestCurrentLocation()
                    return .success(coordinate, .watch)
                } catch {
                    return .failure(error)
                }
            }

            group.addTask {
                do {
                    let coordinate = try await self.bridge.requestPhoneLocationCoordinate()
                    return .success(coordinate, .phone)
                } catch {
                    return .failure(error)
                }
            }

            while let result = try await group.next() {
                switch result {
                case .success(let coordinate, let source):
                    group.cancelAll()
                    await MainActor.run {
                        if case .phone = source {
                            self.statusText = self.bridge.copy.text(.usingPhoneLocation)
                        }
                    }
                    return coordinate
                case .failure(let error):
                    if !(error is CancellationError) {
                        failures.append(error)
                    }
                }
            }

            throw preferredLocationError(from: failures)
        }
    }

    private func preferredLocationError(from failures: [Error]) -> Error {
        for failure in failures {
            if let watchError = failure as? WatchLocationError,
               case .permissionDenied = watchError {
                return watchError
            }
            let appErrorCode = (failure as NSError).userInfo["appErrorCode"] as? String
            if appErrorCode == "location_permission_denied" {
                return failure
            }
        }

        for failure in failures {
            if let watchError = failure as? WatchLocationError {
                return watchError
            }
            let appErrorCode = (failure as NSError).userInfo["appErrorCode"] as? String
            if appErrorCode == "location_unavailable" || appErrorCode == "phone_unavailable" {
                return failure
            }
        }

        return failures.first ?? WatchLocationError.locationUnavailable
    }

    @MainActor
    private func apply(result: QuickReportReply, copy: WatchCopy) {
        if result.convertedToConfirmation {
            statusText = String(format: copy.text(.reportConfirmed), result.municipality)
        } else {
            statusText = String(format: copy.text(.reportSent), result.municipality)
        }
    }

    @MainActor
    private func idleStatusText() -> String {
        let copy = bridge.copy
        if bridge.canSubmitReport {
            return copy.text(.tapToReport)
        }
        if bridge.authenticated {
            return copy.text(.phoneUnavailable)
        }
        return bridge.reachable ? copy.text(.tapToReport) : copy.text(.missingAccessToken)
    }
}
