import Capacitor
import Foundation
import Security
import WebKit

public enum CompanionBridgeStorage {
    public static let accessTokenKey = "companion.accessToken"
    public static let refreshTokenKey = "companion.refreshToken"
    public static let apiBaseUrlKey = "companion.apiBaseUrl"
    public static let preferredLanguageKey = "companion.preferredLanguage"
    public static let didUpdateNotification = Notification.Name("CompanionBridgeDidUpdate")

    private static let accessService = "com.jefe.cacaradar.auth.access"
    private static let refreshService = "com.jefe.cacaradar.auth.refresh"
    private static let keychainAccount = "primary"

    public static func readAccessToken() -> String? {
        readKeychainValue(service: accessService)
    }

    public static func readRefreshToken() -> String? {
        readKeychainValue(service: refreshService)
    }

    public static func readApiBaseUrl() -> String? {
        UserDefaults.standard.string(forKey: apiBaseUrlKey)
    }

    public static func readPreferredLanguage() -> String? {
        UserDefaults.standard.string(forKey: preferredLanguageKey)
    }

    public static func persistAuthState(
        accessToken: String,
        refreshToken: String?,
        apiBaseUrl: String,
        preserveStoredRefreshToken: Bool = false
    ) throws {
        try persistKeychainValue(accessToken, service: accessService)
        let nextRefreshToken = refreshToken?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if !preserveStoredRefreshToken || !nextRefreshToken.isEmpty {
            try persistKeychainValue(nextRefreshToken, service: refreshService)
        }

        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: accessTokenKey)
        defaults.removeObject(forKey: refreshTokenKey)
        if apiBaseUrl.isEmpty {
            defaults.removeObject(forKey: apiBaseUrlKey)
        } else {
            defaults.set(apiBaseUrl, forKey: apiBaseUrlKey)
        }
        defaults.synchronize()
    }

    public static func clearAuthState() throws {
        try clearKeychainValue(service: accessService)
        try clearKeychainValue(service: refreshService)
        UserDefaults.standard.removeObject(forKey: accessTokenKey)
        UserDefaults.standard.removeObject(forKey: refreshTokenKey)
        UserDefaults.standard.removeObject(forKey: apiBaseUrlKey)
        UserDefaults.standard.synchronize()
    }

    public static func currentAuthState() -> [String: String] {
        [
            "accessToken": readAccessToken() ?? "",
            "apiBaseUrl": readApiBaseUrl() ?? "",
        ]
    }

    private static func baseQuery(service: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: keychainAccount,
        ]
    }

    private static func persistKeychainValue(_ value: String, service: String) throws {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            try clearKeychainValue(service: service)
            return
        }

        let data = Data(trimmed.utf8)
        var attributes = baseQuery(service: service)
        let updateStatus = SecItemUpdate(
            attributes as CFDictionary,
            [
                kSecValueData as String: data,
                kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
            ] as CFDictionary
        )
        if updateStatus == errSecSuccess {
            return
        }
        if updateStatus != errSecItemNotFound {
            throw keychainError(status: updateStatus, service: service)
        }

        attributes[kSecValueData as String] = data
        attributes[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        let addStatus = SecItemAdd(attributes as CFDictionary, nil)
        if addStatus != errSecSuccess {
            throw keychainError(status: addStatus, service: service)
        }
    }

    private static func readKeychainValue(service: String) -> String? {
        var query = baseQuery(service: service)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess else {
            return nil
        }
        guard let data = item as? Data else {
            return nil
        }
        let token = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return token?.isEmpty == false ? token : nil
    }

    private static func clearKeychainValue(service: String) throws {
        let status = SecItemDelete(baseQuery(service: service) as CFDictionary)
        if status != errSecSuccess && status != errSecItemNotFound {
            throw keychainError(status: status, service: service)
        }
    }

    private static func keychainError(status: OSStatus, service: String) -> NSError {
        let message = SecCopyErrorMessageString(status, nil) as String? ?? "Keychain error"
        return NSError(
            domain: "CompanionBridgeStorage",
            code: Int(status),
            userInfo: [
                NSLocalizedDescriptionKey: "\(message) (\(service))",
            ]
        )
    }
}

@objc(CompanionBridgePlugin)
public class CompanionBridgePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "CompanionBridgePlugin"
    public let jsName = "CompanionBridge"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "syncAuthState", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getAuthState", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "bootstrapSessionFromCookies", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "refreshAccessToken", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "syncPreferences", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clearAuthState", returnType: CAPPluginReturnPromise),
    ]

    @objc func syncAuthState(_ call: CAPPluginCall) {
        let accessToken = call.getString("accessToken") ?? ""
        let refreshToken = call.getString("refreshToken")
        let apiBaseUrl = call.getString("apiBaseUrl") ?? ""
        let preserveStoredRefreshToken = call.getBool("preserveStoredRefreshToken") ?? false

        do {
            try CompanionBridgeStorage.persistAuthState(
                accessToken: accessToken,
                refreshToken: refreshToken,
                apiBaseUrl: apiBaseUrl,
                preserveStoredRefreshToken: preserveStoredRefreshToken
            )
            NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)
            call.resolve()
        } catch {
            call.reject("Failed to store auth state securely", nil, error)
        }
    }

    @objc func getAuthState(_ call: CAPPluginCall) {
        let authState = CompanionBridgeStorage.currentAuthState()
        var payload = JSObject()
        payload["accessToken"] = authState["accessToken"] ?? ""
        payload["apiBaseUrl"] = authState["apiBaseUrl"] ?? ""
        call.resolve(payload)
    }

    @objc func bootstrapSessionFromCookies(_ call: CAPPluginCall) {
        let apiBaseUrl = normalizedApiBaseUrl(call.getString("apiBaseUrl"))
        guard let apiUrl = URL(string: apiBaseUrl), let host = apiUrl.host else {
            call.reject("Invalid API base URL")
            return
        }

        let cookieStore = bridge?.webView?.configuration.websiteDataStore.httpCookieStore
            ?? WKWebsiteDataStore.default().httpCookieStore
        cookieStore.getAllCookies { cookies in
            let matchingCookies = cookies.filter { cookie in
                guard let cookieHost = cookie.domain.trimmingCharacters(in: .whitespacesAndNewlines).lowercased().split(separator: ":").first else {
                    return false
                }
                return host.lowercased().hasSuffix(cookieHost.hasPrefix(".") ? String(cookieHost.dropFirst()) : String(cookieHost))
            }
            let cookieAccessToken = matchingCookies.first(where: { $0.name == "access_token" })?.value ?? ""
            let cookieRefreshToken = matchingCookies.first(where: { $0.name == "refresh_token" })?.value ?? ""
            let accessToken = cookieAccessToken.isEmpty ? (CompanionBridgeStorage.readAccessToken() ?? "") : cookieAccessToken
            let refreshToken = cookieRefreshToken.isEmpty ? (CompanionBridgeStorage.readRefreshToken() ?? "") : cookieRefreshToken

            do {
                try CompanionBridgeStorage.persistAuthState(
                    accessToken: accessToken,
                    refreshToken: cookieRefreshToken.isEmpty ? nil : refreshToken,
                    apiBaseUrl: apiBaseUrl,
                    preserveStoredRefreshToken: cookieRefreshToken.isEmpty
                )
                NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)
                var payload = JSObject()
                payload["accessToken"] = accessToken
                payload["synced"] = !refreshToken.isEmpty
                call.resolve(payload)
            } catch {
                call.reject("Failed to bootstrap session from cookies", nil, error)
            }
        }
    }

    @objc func refreshAccessToken(_ call: CAPPluginCall) {
        let apiBaseUrl = normalizedApiBaseUrl(call.getString("apiBaseUrl"))
        Task {
            do {
                let refreshedToken = try await refreshNativeAccessToken(apiBaseUrl: apiBaseUrl)
                NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)
                var payload = JSObject()
                payload["accessToken"] = refreshedToken
                call.resolve(payload)
            } catch {
                call.reject("Failed to refresh native access token", nil, error)
            }
        }
    }

    @objc func syncPreferences(_ call: CAPPluginCall) {
        let preferredLanguage = call.getString("preferredLanguage") ?? ""

        let defaults = UserDefaults.standard
        defaults.set(preferredLanguage, forKey: CompanionBridgeStorage.preferredLanguageKey)
        defaults.synchronize()
        NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)

        call.resolve()
    }

    @objc func clearAuthState(_ call: CAPPluginCall) {
        do {
            try CompanionBridgeStorage.clearAuthState()
            NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)
            call.resolve()
        } catch {
            call.reject("Failed to clear auth state", nil, error)
        }
    }

    private func normalizedApiBaseUrl(_ rawValue: String?) -> String {
        let trimmed = (rawValue ?? CompanionBridgeStorage.readApiBaseUrl() ?? "https://cacaradar.es/api")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let withoutTrailingSlash = trimmed.replacingOccurrences(of: "/+$", with: "", options: .regularExpression)
        if withoutTrailingSlash.isEmpty {
            return "https://cacaradar.es/api"
        }
        if withoutTrailingSlash.hasSuffix("/api") {
            return withoutTrailingSlash
        }
        return withoutTrailingSlash + "/api"
    }

    private func refreshNativeAccessToken(apiBaseUrl: String) async throws -> String {
        guard let refreshToken = CompanionBridgeStorage.readRefreshToken(), !refreshToken.isEmpty else {
            throw NSError(domain: "CompanionBridgePlugin", code: 401, userInfo: [NSLocalizedDescriptionKey: "No refresh token available"])
        }
        guard let url = URL(string: apiBaseUrl + "/auth/refresh") else {
            throw NSError(domain: "CompanionBridgePlugin", code: 400, userInfo: [NSLocalizedDescriptionKey: "Invalid API base URL"])
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("1", forHTTPHeaderField: "X-Native-App")
        request.setValue("ios", forHTTPHeaderField: "X-Platform")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "refresh_token": refreshToken,
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            throw NSError(domain: "CompanionBridgePlugin", code: 401, userInfo: [NSLocalizedDescriptionKey: "Refresh request failed"])
        }
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let accessToken = json["access_token"] as? String,
            !accessToken.isEmpty
        else {
            throw NSError(domain: "CompanionBridgePlugin", code: 500, userInfo: [NSLocalizedDescriptionKey: "No access token returned"])
        }

        try CompanionBridgeStorage.persistAuthState(
            accessToken: accessToken,
            refreshToken: nil,
            apiBaseUrl: apiBaseUrl,
            preserveStoredRefreshToken: true
        )
        return accessToken
    }
}
