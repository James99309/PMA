// 自定义 Capacitor Bridge ViewController, 用于显式注册 App target 内的本地插件
// (Capacitor 8 SPM 工程下, CAP_PLUGIN 宏自动注册不可靠, 必须手动注册)
import UIKit
import Capacitor

class CustomBridgeViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        super.capacitorDidLoad()
        // 注册 App target 内的本地插件 (DocumentScannerPlugin)
        bridge?.registerPluginInstance(DocumentScannerPlugin())
    }
}
