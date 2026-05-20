import { defineStore } from 'pinia'
import { login as apiLogin, loginToRegion, logout as apiLogout } from '@/api/auth'
import { REGIONS, getCurrentRegion, setCurrentRegion } from '@/api/client'
import { setLocale } from '@/locales'
import { setupPushNotifications, unregisterPushNotifications } from '@/utils/push'

// 多区域 token / user 存储 (Federation Lite)
//   localStorage:
//     region                — 'cn' | 'sg' (当前活跃区域)
//     access_token_cn       — CN token
//     access_token_sg       — SG token
//     user_cn / user_sg     — 各区域 user 资料
//
// 兼容旧 key (access_token / user) — 首次升级时迁移到新 key, 标 region=cn

function migrateLegacyKeys() {
  const legacyToken = localStorage.getItem('access_token')
  const legacyUser = localStorage.getItem('user')
  if (legacyToken && !localStorage.getItem('access_token_cn')) {
    localStorage.setItem('access_token_cn', legacyToken)
  }
  if (legacyUser && !localStorage.getItem('user_cn')) {
    localStorage.setItem('user_cn', legacyUser)
  }
  if (!localStorage.getItem('region') && legacyToken) {
    localStorage.setItem('region', 'cn')
  }
}
migrateLegacyKeys()

export const useAuthStore = defineStore('auth', {
  state: () => {
    const region = getCurrentRegion().id
    return {
      regionId: region,
      // 两边 token / user 都存 reactive state, getter 才能正确响应
      tokens: {
        cn: localStorage.getItem('access_token_cn') || null,
        sg: localStorage.getItem('access_token_sg') || null,
      },
      users: {
        cn: JSON.parse(localStorage.getItem('user_cn') || 'null'),
        sg: JSON.parse(localStorage.getItem('user_sg') || 'null'),
      },
    }
  },

  getters: {
    token:      s => s.tokens[s.regionId] || null,
    user:       s => s.users[s.regionId] || null,
    isLoggedIn: s => !!s.tokens[s.regionId],
    userName:   s => {
      const u = s.users[s.regionId]
      return u?.real_name || u?.username || ''
    },
    region:     s => REGIONS[s.regionId] || REGIONS.cn,
    hasOtherRegionToken: s => {
      const other = s.regionId === 'cn' ? 'sg' : 'cn'
      return !!s.tokens[other]
    },
    // 本位区: 用户是 native (is_mirror=false) 那一区; 没找到则退回当前区
    homeRegionId: s => {
      for (const id of ['cn', 'sg']) {
        if (s.users[id] && s.users[id].is_mirror === false) return id
      }
      return s.regionId
    },
    // 是否切到非本位的对区
    isAway: s => {
      const home = (() => {
        for (const id of ['cn', 'sg']) {
          if (s.users[id] && s.users[id].is_mirror === false) return id
        }
        return s.regionId
      })()
      return home !== s.regionId
    },
  },

  actions: {
    /**
     * 智能并行登录: 同时尝试 CN + SG
     *
     * 安全要点: 登录前必须清掉两区所有残留 token —— 否则同一台设备前次登录的
     * 用户残留 token 会被新用户继承, 导致"Patrick 登录后能切到 liuwei"的串号 bug
     */
    async login(username, password) {
      const ids = ['cn', 'sg']
      // 清前次会话残留 (本地 + reactive state)
      ids.forEach(id => {
        localStorage.removeItem(`access_token_${id}`)
        localStorage.removeItem(`user_${id}`)
        this.tokens[id] = null
        this.users[id] = null
      })
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')

      const results = await Promise.allSettled(
        ids.map(id => loginToRegion(id, username, password))
      )
      const ok = []
      let lastErr = null
      results.forEach((r, i) => {
        const id = ids[i]
        if (r.status === 'fulfilled') {
          const { token, user } = r.value.data.data
          localStorage.setItem(`access_token_${id}`, token)
          localStorage.setItem(`user_${id}`, JSON.stringify(user))
          // 同步 reactive state
          this.tokens[id] = token
          this.users[id] = user
          ok.push({ id, token, user })
        } else {
          lastErr = r.reason
        }
      })
      if (!ok.length) {
        throw lastErr || new Error('登录失败')
      }
      // 默认进入用户的"主区"(非 mirror 那一区, 即 user.is_mirror=false 的区)
      // liuwei 在 CN 是本地用户, 在 SG 是镜像 → 默认进 CN
      // 主区不存在(双 mirror 或 API 没返回 is_mirror)时, 退回 remembered → cn → 任一
      const remembered = localStorage.getItem('region')
      const homeRegion = ok.find(x => x.user && x.user.is_mirror === false)
      const winner =
        homeRegion ||
        ok.find(x => x.id === remembered) ||
        ok.find(x => x.id === 'cn') ||
        ok[0]
      setCurrentRegion(winner.id)
      this.regionId = winner.id
      // 兼容旧 key
      localStorage.setItem('access_token', winner.token)
      localStorage.setItem('user', JSON.stringify(winner.user))
      // i18n: SG 区一律英文 (覆盖个人 language_preference); 其它区按用户偏好
      if (winner.id === 'sg') {
        setLocale('en')
      } else {
        const pref = winner.user?.language_preference
        if (pref === 'zh' || pref === 'en') setLocale(pref)
      }
      // iOS push notifications: 拿 device token 并上报后端 (失败不影响登录)
      setupPushNotifications().catch(e => console.warn('[push] setup failed:', e?.message))
      return { activeRegion: winner.id, available: ok.map(x => x.id) }
    },

    async logout() {
      try { await apiLogout() } catch {}
      // 清 APNs push token (后端 & 本地 listener)
      try { await unregisterPushNotifications() } catch {}
      // 安全: 退出时必须清两区全部 token —— 防止下个用户继承上个用户的另一区会话
      const ids = ['cn', 'sg']
      ids.forEach(id => {
        this.tokens[id] = null
        this.users[id] = null
        localStorage.removeItem(`access_token_${id}`)
        localStorage.removeItem(`user_${id}`)
      })
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    },

    /**
     * 切换到另一个区域 (用 reactive tokens 判断)
     */
    switchRegion(targetRegionId) {
      if (!REGIONS[targetRegionId]) return false
      if (targetRegionId === this.regionId) return true
      if (!this.tokens[targetRegionId]) return false
      setCurrentRegion(targetRegionId)
      this.regionId = targetRegionId
      // 同步旧 key 给暂未升级的代码
      localStorage.setItem('access_token', this.tokens[targetRegionId])
      localStorage.setItem('user', JSON.stringify(this.users[targetRegionId]))
      return true
    },
  },
})
