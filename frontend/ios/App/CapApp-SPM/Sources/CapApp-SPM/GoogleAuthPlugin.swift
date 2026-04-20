import Capacitor
import Foundation
import GoogleSignIn
import UIKit

@objc(GoogleAuthPlugin)
public class GoogleAuthPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "GoogleAuthPlugin"
    public let jsName = "GoogleAuth"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "signOut", returnType: CAPPluginReturnPromise)
    ]

    @objc func signIn(_ call: CAPPluginCall) {
        guard let serverClientId = call.getString("serverClientId"), !serverClientId.isEmpty else {
            call.reject("Missing serverClientId")
            return
        }

        guard let iosClientId = call.getString("iosClientId"), !iosClientId.isEmpty else {
            call.reject("Missing iosClientId")
            return
        }

        guard let presentingViewController = bridge?.viewController else {
            call.reject("Unable to find presenting view controller")
            return
        }

        DispatchQueue.main.async {
            let configuration = GIDConfiguration(clientID: iosClientId, serverClientID: serverClientId)
            GIDSignIn.sharedInstance.configuration = configuration

            GIDSignIn.sharedInstance.signIn(withPresenting: presentingViewController) { result, error in
                if let error {
                    call.reject("Google sign-in failed", nil, error)
                    return
                }

                guard let user = result?.user else {
                    call.reject("Google sign-in did not return a user")
                    return
                }

                guard let idToken = user.idToken?.tokenString, !idToken.isEmpty else {
                    call.reject("Google sign-in did not return an ID token")
                    return
                }

                let profile = user.profile
                let response: [String: Any?] = [
                    "idToken": idToken,
                    "email": profile?.email,
                    "displayName": profile?.name,
                    "photoUrl": profile?.imageURL(withDimension: 256)?.absoluteString
                ]
                call.resolve(response.compactMapValues { $0 })
            }
        }
    }

    @objc func signOut(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            GIDSignIn.sharedInstance.signOut()
            call.resolve()
        }
    }
}
