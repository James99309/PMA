// Capacitor plugin macros — 把 Swift 类暴露给 JS 桥
#import <Foundation/Foundation.h>
#import <Capacitor/Capacitor.h>

CAP_PLUGIN(DocumentScannerPlugin, "DocumentScanner",
    CAP_PLUGIN_METHOD(isAvailable, CAPPluginReturnPromise);
    CAP_PLUGIN_METHOD(scan,        CAPPluginReturnPromise);
)
