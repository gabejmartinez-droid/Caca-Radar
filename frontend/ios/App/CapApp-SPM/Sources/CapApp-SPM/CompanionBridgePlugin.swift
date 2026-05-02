import Capacitor
import Foundation

enum CompanionBridgeStorage {
    static let accessTokenKey = "companion.accessToken"
    static let refreshTokenKey = "companion.refreshToken"
    static let apiBaseUrlKey = "companion.apiBaseUrl"
    static let preferredLanguageKey = "companion.preferredLanguage"
    static let didUpdateNotification = Notification.Name("CompanionBridgeDidUpdate")
}

@objc(CompanionBridgePlugin)
public class CompanionBridgePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "CompanionBridgePlugin"
    public let jsName = "CompanionBridge"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "syncAuthState", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "syncPreferences", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clearAuthState", returnType: CAPPluginReturnPromise),
    ]

    @objc func syncAuthState(_ call: CAPPluginCall) {
        let accessToken = call.getString("accessToken") ?? ""
        let refreshToken = call.getString("refreshToken") ?? ""
        let apiBaseUrl = call.getString("apiBaseUrl") ?? ""

        let defaults = UserDefaults.standard
        defaults.set(accessToken, forKey: CompanionBridgeStorage.accessTokenKey)
        defaults.set(refreshToken, forKey: CompanionBridgeStorage.refreshTokenKey)
        defaults.set(apiBaseUrl, forKey: CompanionBridgeStorage.apiBaseUrlKey)
        defaults.synchronize()
        NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)

        call.resolve()
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
        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: CompanionBridgeStorage.accessTokenKey)
        defaults.removeObject(forKey: CompanionBridgeStorage.refreshTokenKey)
        defaults.removeObject(forKey: CompanionBridgeStorage.apiBaseUrlKey)
        defaults.synchronize()
        NotificationCenter.default.post(name: CompanionBridgeStorage.didUpdateNotification, object: nil)

        call.resolve()
    }
}
