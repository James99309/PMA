// JS 端代理 → 原生 DocumentScanner plugin (iOS only, VisionKit)
// 用法:
//   import { DocumentScanner } from '@/plugins/documentScanner'
//   const ok = await DocumentScanner.isAvailable()  // {available: true/false}
//   const r = await DocumentScanner.scan()          // {pages: [{dataUrl}]}
//
// 老版本 App 没装这个原生插件 → registerPlugin 返回 proxy, 调方法时
// reject. 调用方应 try/catch 并 fallback 到手动裁剪流程。
import { registerPlugin } from '@capacitor/core'

export const DocumentScanner = registerPlugin('DocumentScanner', {
  // web 平台没有 VisionKit, 直接拒绝让调用方 fallback
  web: () => ({
    isAvailable: () => Promise.resolve({ available: false }),
    scan: () => Promise.reject(new Error('not supported on web')),
  }),
})
