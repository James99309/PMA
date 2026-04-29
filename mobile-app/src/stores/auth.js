import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),

  getters: {
    isLoggedIn: s => !!s.token,
    userName: s => s.user?.real_name || s.user?.username || '',
  },

  actions: {
    async login(username, password) {
      const res = await apiLogin(username, password)
      const { token, user } = res.data.data
      this.token = token
      this.user = user
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },

    async logout() {
      try { await apiLogout() } catch {}
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    },
  },
})
