import axios from 'axios'

// dev: 空字符串 → 走 Vite proxy（/api/v1 → localhost:5012）
// prod: 生产域名
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'https://pma.jamesgpone.win'

const client = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 自动附加 JWT token
client.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 自动跳登录
client.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export default client
