// DocumentScannerPlugin — 用 VisionKit 做名片自动边缘检测 + 透视校正
// 调用方: JS 端 import { DocumentScanner } from '@/plugins/documentScanner'
//        const r = await DocumentScanner.scan()
//        // r.pages: [{ dataUrl: 'data:image/jpeg;base64,...' }]
import Foundation
import Capacitor
import VisionKit
import UIKit

@objc(DocumentScannerPlugin)
public class DocumentScannerPlugin: CAPPlugin, VNDocumentCameraViewControllerDelegate {

    private var savedCall: CAPPluginCall?

    @objc public override func load() {
        // no-op
    }

    @objc func isAvailable(_ call: CAPPluginCall) {
        let supported = VNDocumentCameraViewController.isSupported
        call.resolve(["available": supported])
    }

    @objc func scan(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard VNDocumentCameraViewController.isSupported else {
                call.reject("Document scanner not supported on this device")
                return
            }
            self.savedCall = call
            let scanner = VNDocumentCameraViewController()
            scanner.delegate = self
            scanner.modalPresentationStyle = .fullScreen
            self.bridge?.viewController?.present(scanner, animated: true, completion: nil)
        }
    }

    public func documentCameraViewController(_ controller: VNDocumentCameraViewController,
                                             didFinishWith scan: VNDocumentCameraScan) {
        let quality = (savedCall?.getDouble("quality") ?? 0.88)
        let maxLong = (savedCall?.getInt("maxLong") ?? 1600)

        var pages: [[String: String]] = []
        for i in 0..<scan.pageCount {
            var image = scan.imageOfPage(at: i)
            // 长边限制压缩
            if maxLong > 0 {
                let longSide = max(image.size.width, image.size.height)
                if longSide > CGFloat(maxLong) {
                    let s = CGFloat(maxLong) / longSide
                    let newSize = CGSize(width: image.size.width * s, height: image.size.height * s)
                    UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
                    image.draw(in: CGRect(origin: .zero, size: newSize))
                    if let resized = UIGraphicsGetImageFromCurrentImageContext() {
                        image = resized
                    }
                    UIGraphicsEndImageContext()
                }
            }
            if let data = image.jpegData(compressionQuality: CGFloat(quality)) {
                let b64 = data.base64EncodedString()
                pages.append(["dataUrl": "data:image/jpeg;base64,\(b64)"])
            }
        }
        controller.dismiss(animated: true) {
            self.savedCall?.resolve(["pages": pages])
            self.savedCall = nil
        }
    }

    public func documentCameraViewControllerDidCancel(_ controller: VNDocumentCameraViewController) {
        controller.dismiss(animated: true) {
            self.savedCall?.reject("cancelled")
            self.savedCall = nil
        }
    }

    public func documentCameraViewController(_ controller: VNDocumentCameraViewController,
                                             didFailWithError error: Error) {
        controller.dismiss(animated: true) {
            self.savedCall?.reject("Scan failed: \(error.localizedDescription)")
            self.savedCall = nil
        }
    }
}
