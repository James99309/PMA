import axios from 'axios'
import client from './client'
import { REGIONS } from './client'

// 普通登录 (走当前 region 的 baseURL, 兼容旧调用)
export const login = (username, password) =>
  client.post('/auth/login', { username, password })

// 指定 region 登录 (用对应 region 的 baseURL, 不依赖当前 client 状态)
export const loginToRegion = (regionId, username, password) => {
  const region = REGIONS[regionId]
  if (!region) throw new Error(`unknown region: ${regionId}`)
  return axios.post(
    `${region.baseUrl}/api/v1/auth/login`,
    { username, password },
    { headers: { 'Content-Type': 'application/json' }, timeout: 15000 },
  )
}

export const logout = () =>
  client.post('/auth/logout')
