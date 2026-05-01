import SwiftUI

@main
struct CacaRadarWatchApp: App {
    @WKApplicationDelegateAdaptor(ExtensionDelegate.self) private var extensionDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
