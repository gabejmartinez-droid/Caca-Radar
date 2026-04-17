import UIKit
import Capacitor

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        print("CacaRadarNative: SceneDelegate willConnectTo")
        guard let windowScene = scene as? UIWindowScene else {
            print("CacaRadarNative: SceneDelegate missing UIWindowScene")
            return
        }

        let window = UIWindow(windowScene: windowScene)
        print("CacaRadarNative: Creating CAPBridgeViewController")
        let storyboard = UIStoryboard(name: "Main", bundle: nil)
        guard let rootViewController = storyboard.instantiateInitialViewController() else {
            print("CacaRadarNative: Main storyboard did not return a root view controller")
            return
        }
        print("CacaRadarNative: Created root view controller: \(type(of: rootViewController))")
        print("CacaRadarNative: Loading root view")
        rootViewController.loadViewIfNeeded()
        print("CacaRadarNative: Root view loaded")
        window.rootViewController = rootViewController
        print("CacaRadarNative: Assigned root view controller")
        self.window = window
        print("CacaRadarNative: Retained scene window")
        print("CacaRadarNative: Making window key and visible")
        window.makeKeyAndVisible()
        print("CacaRadarNative: CAPBridgeViewController visible")
    }

    func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
        for context in URLContexts {
            _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, open: context.url, options: [:])
        }
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, continue: userActivity, restorationHandler: { _ in })
    }
}
