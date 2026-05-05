import { defineStore } from 'pinia'
import { login as apiLogin, loginToRegion, logout as apiLogout } from '@/api/auth'
import { REGIONS, getCurrentRegion, setCurrentRegion } from '@/api/client'

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
  },

  actions: {
    /**
     * 智能并行登录: 同时尝试 CN + SG
     */
    async login(username, password) {
      const ids = ['cn', 'sg']
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
      const remembered = localStorage.getItem('region')
      const winner =
        ok.find(x => x.id === remembered) ||
        ok.find(x => x.id === 'cn') ||
        ok[0]
      setCurrentRegion(winner.id)
      this.regionId = winner.id
      // 兼容旧 key
      localStorage.setItem('access_token', winner.token)
      localStorage.setItem('user', JSON.stringify(winner.user))
      return { activeRegion: winner.id, available: ok.map(x => x.id) }
    },

    async logout() {
      try { await apiLogout() } catch {}
      const region = this.regionId
      this.tokens[region] = null
      this.users[region] = null
      localStorage.removeItem(`access_token_${region}`)
      localStorage.removeItem(`user_${region}`)
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
