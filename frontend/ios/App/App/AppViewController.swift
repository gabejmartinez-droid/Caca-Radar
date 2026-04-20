import Capacitor
import CapApp_SPM

class AppViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        super.capacitorDidLoad()

        if bridge?.plugin(withName: "GoogleAuth") == nil {
            bridge?.registerPluginInstance(GoogleAuthPlugin())
        }
    }
}
