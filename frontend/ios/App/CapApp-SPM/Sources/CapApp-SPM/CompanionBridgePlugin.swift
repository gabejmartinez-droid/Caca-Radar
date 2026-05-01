import Capacitor
import Foundation

enum CompanionBridgeStorage {
    static let accessTokenKey = "companion.accessToken"
    static let refreshTokenKey = "companion.refreshToken"
    static let apiBaseUrlKey = "companion.apiBaseUrl"
}

@objc(CompanionBridgePlugin)
public class CompanionBridgePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "CompanionBridgePlugin"
    public let jsName = "CompanionBridge"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "syncAuthState", returnType: CAPPluginReturnPromise),
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

        call.resolve()
    }

    @objc func clearAuthState(_ call: CAPPluginCall) {
        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: CompanionBridgeStorage.accessTokenKey)
        defaults.removeObject(forKey: CompanionBridgeStorage.refreshTokenKey)
        defaults.removeObject(forKey: CompanionBridgeStorage.apiBaseUrlKey)
        defaults.synchronize()

        call.resolve()
    }
}
