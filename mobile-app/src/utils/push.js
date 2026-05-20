// Push Notifications setup — 仅 native iOS, web/Android 自动 noop
// 调用时机: login 成功后, 或 App 启动时(若已登录)
//
// 流程:
//   1. requestPermissions: 弹系统通知权限弹窗 (用户首次拒绝则永远收不到 push)
//   2. register: 注册到 APNs, 拿 device token (回调 'registration' event)
//   3. POST device token 到 /mobile/push/register
//   4. 监听 pushNotificationReceived(前台收到) + pushNotificationActionPerformed(用户点通知)
//
// 多区 (cn/sg) 用户: device token 只上报到 ACTIVE region (login 后 winner region)
// 切区时不重新注册(简化), 但切到的区也需要拿到 token → 由后续切区操作触发同步

import { Capacitor } from '@capacitor/core'
import client from '@/api/client'

let _initialized = false

export async function setupPushNotifications() {
  if (_initialized) return
  if (!Capacitor.isNativePlatform?.()) {
    console.log('[push] 非 native 平台, 跳过')
    return
  }
  if (Capacitor.getPlatform() !== 'ios') {
    console.log('[push] 暂未实现 Android FCM, 跳过')
    return
  }
  try {
    const { PushNotifications } = await import('@capacitor/push-notifications')
    // 1. 权限
    const perm = await PushNotifications.checkPermissions()
    let granted = perm.receive === 'granted'
    if (!granted) {
      const req = await PushNotifications.requestPermissions()
      granted = req.receive === 'granted'
    }
    if (!granted) {
      console.warn('[push] 用户拒绝通知权限')
      return
    }
    // 2. 监听 — 必须在 register 之前注册, 避免错过 token 回调
    await PushNotifications.removeAllListeners()
    await PushNotifications.addListener('registration', async ({ value }) => {
      console.log('[push] device token:', value?.slice(0, 12) + '...')
      try {
        await client.post('/mobile/push/register', { push_token: value, platform: 'ios' })
        console.log('[push] token 已上报后端')
      } catch (e) {
        console.warn('[push] 上报 token 失败:', e?.message)
      }
    })
    await PushNotifications.addListener('registrationError', (err) => {
      console.warn('[push] APNs registration error:', err)
    })
    await PushNotifications.addListener('pushNotificationReceived', (notification) => {
      // 前台收到 (App 打开时), iOS 默认不弹横幅, 可选自己 toast
      console.log('[push] 前台收到:', notification?.title, notification?.body)
    })
    await PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      // 用户点了 lock screen / 通知中心的 push, App 启动到前台
      const data = action?.notification?.data
      console.log('[push] 用户点击通知:', data)
      _handleNotificationTap(data)
    })
    // 3. 注册 (触发 registration 事件)
    await PushNotifications.register()
    _initialized = true
  } catch (e) {
    console.warn('[push] 初始化失败:', e?.message || e)
  }
}

function _handleNotificationTap(data) {
  if (!data) return
  // 简化路由: chat_message → 跳对应会话
  if (data.type === 'chat_message' && data.conversation_id) {
    // 用 hash route 避免与现有 router 冲突, 主流程响应即可
    import('@/router').then(({ default: router }) => {
      router.push(`/chat/${data.conversation_id}`).catch(() => {})
    })
  } else if (data.type === 'approval' && data.instance_id) {
    import('@/router').then(({ default: router }) => {
      router.push(`/approval/${data.instance_id}`).catch(() => {})
    })
  }
}

// 注销 push (logout 时调) — 通知后端清除 token, 然后忘掉本地 listener
export async function unregisterPushNotifications() {
  if (!Capacitor.isNativePlatform?.()) return
  try {
    await client.post('/mobile/push/unregister', {})
  } catch {}
  try {
    const { PushNotifications } = await import('@capacitor/push-notifications')
    await PushNotifications.removeAllListeners()
  } catch {}
  _initialized = false
}
