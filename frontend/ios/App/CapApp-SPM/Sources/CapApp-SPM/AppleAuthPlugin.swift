import AuthenticationServices
import Capacitor
import Foundation
import UIKit

@objc(AppleAuthPlugin)
public class AppleAuthPlugin: CAPPlugin, CAPBridgedPlugin, ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
    public let identifier = "AppleAuthPlugin"
    public let jsName = "AppleAuth"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise)
    ]

    private var activeCall: CAPPluginCall?

    @objc func signIn(_ call: CAPPluginCall) {
        guard activeCall == nil else {
            call.reject("Apple sign-in is already in progress")
            return
        }

        guard #available(iOS 13.0, *) else {
            call.reject("Apple sign-in requires iOS 13 or later")
            return
        }

        let provider = ASAuthorizationAppleIDProvider()
        let request = provider.createRequest()
        request.requestedScopes = [.fullName, .email]

        let controller = ASAuthorizationController(authorizationRequests: [request])
        controller.delegate = self
        controller.presentationContextProvider = self
        activeCall = call

        DispatchQueue.main.async {
            controller.performRequests()
        }
    }

    public func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        if let window = bridge?.viewController?.view.window {
            return window
        }
        return ASPresentationAnchor()
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        guard let call = activeCall else { return }
        activeCall = nil

        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            call.reject("Apple sign-in did not return an Apple ID credential")
            return
        }

        guard let identityTokenData = credential.identityToken,
              let identityToken = String(data: identityTokenData, encoding: .utf8),
              !identityToken.isEmpty else {
            call.reject("Apple sign-in did not return an identity token")
            return
        }

        let authorizationCode = credential.authorizationCode.flatMap { String(data: $0, encoding: .utf8) } ?? ""
        let givenName = credential.fullName?.givenName ?? ""
        let familyName = credential.fullName?.familyName ?? ""
        let fullName = [givenName, familyName].filter { !$0.isEmpty }.joined(separator: " ")

        call.resolve([
            "identityToken": identityToken,
            "authorizationCode": authorizationCode,
            "email": credential.email ?? "",
            "givenName": givenName,
            "familyName": familyName,
            "fullName": fullName,
            "user": credential.user
        ])
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        guard let call = activeCall else { return }
        activeCall = nil

        let nsError = error as NSError
        if nsError.domain == ASAuthorizationError.errorDomain && nsError.code == ASAuthorizationError.canceled.rawValue {
            call.reject("Apple sign-in was cancelled", "CANCELED", error)
            return
        }

        call.reject("Apple sign-in failed", nil, error)
    }
}
