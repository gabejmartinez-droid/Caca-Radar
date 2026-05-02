import Capacitor
import Foundation
import Security

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

    public static func persistAuthState(accessToken: String, refreshToken: String, apiBaseUrl: String) throws {
        try persistKeychainValue(accessToken, service: accessService)
        try persistKeychainValue(refreshToken, service: refreshService)

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
            "refreshToken": readRefreshToken() ?? "",
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
        CAPPluginMethod(name: "syncPreferences", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clearAuthState", returnType: CAPPluginReturnPromise),
    ]

    @objc func syncAuthState(_ call: CAPPluginCall) {
        let accessToken = call.getString("accessToken") ?? ""
        let refreshToken = call.getString("refreshToken") ?? ""
        let apiBaseUrl = call.getString("apiBaseUrl") ?? ""

        do {
            try CompanionBridgeStorage.persistAuthState(
                accessToken: accessToken,
                refreshToken: refreshToken,
                apiBaseUrl: apiBaseUrl
            )
            NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)
            call.resolve()
        } catch {
            call.reject("Failed to store auth state securely", nil, error)
        }
    }

    @objc func getAuthState(_ call: CAPPluginCall) {
        call.resolve(JSObject(dictionary: CompanionBridgeStorage.currentAuthState()))
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
}
