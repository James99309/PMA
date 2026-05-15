import axios from 'axios'

// ─── 多区域配置 (Federation Lite) ───────────────────────────────────
// 编译时 fallback 用 .env.production 的 VITE_API_BASE_URL（向后兼容）
// 运行时优先读 localStorage.region，按 REGIONS 表查 baseUrl
const FALLBACK = import.meta.env.VITE_API_BASE_URL ?? 'https://pma.jamesgpone.win'

export const REGIONS = {
  cn: {
    id: 'cn',
    label: '中国',
    flag: '🇨🇳',
    baseUrl: import.meta.env.VITE_API_BASE_URL_CN || 'https://pma-test.jamesgpone.win',
  },
  sg: {
    id: 'sg',
    label: '新加坡',
    flag: '🇸🇬',
    baseUrl: import.meta.env.VITE_API_BASE_URL_SG || 'https://pma-test-sg.jamesgpone.win',
  },
}

// 自动检测默认区域：localStorage > device locale > fallback CN
function detectRegion() {
  const saved = localStorage.getItem('region')
  if (saved && REGIONS[saved]) return saved
  // 简单按时区猜
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    if (/Singapore|Kuala_Lumpur|Jakarta|Bangkok/.test(tz)) return 'sg'
  } catch {}
  return 'cn'
}

export function getCurrentRegion() {
  return REGIONS[detectRegion()] || REGIONS.cn
}

export function setCurrentRegion(regionId) {
  if (!REGIONS[regionId]) return false
  localStorage.setItem('region', regionId)
  // 切换 axios baseURL（即时生效，无需 reload）
  client.defaults.baseURL = `${REGIONS[regionId].baseUrl}/api/v1`
  return true
}

const client = axios.create({
  baseURL: `${(REGIONS[detectRegion()] || { baseUrl: FALLBACK }).baseUrl}/api/v1`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 自动附加 JWT token（按当前区域读对应的 token）+ Accept-Language
client.interceptors.request.use(config => {
  const region = localStorage.getItem('region') || 'cn'
  // 优先按区域分桶的 token，回退到旧的统一 access_token（向后兼容）
  const token = localStorage.getItem(`access_token_${region}`) || localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // i18n: 后端按此 header 返回业务标签的对应语言 (zh-CN / en)
  const lang = localStorage.getItem('lang') || 'zh'
  config.headers['Accept-Language'] = lang === 'en' ? 'en' : 'zh-CN'
  return config
})

// 401 自动跳登录（仅清当前区域 token）
client.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const region = localStorage.getItem('region') || 'cn'
      localStorage.removeItem(`access_token_${region}`)
      localStorage.removeItem('access_token')   // 兼容旧 key
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export default client
