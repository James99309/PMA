// 报销模块 API client — 对应后端 mobile_expense.py
import client from './client'

// 把后端返回的 invoice_image 相对 URL 转成可被 <img> 直接 src 的全 URL
// (附 ?token=JWT 让 chat 文件端点直通鉴权; 同 MessageAttachment.fullUrl)
let _baseHost = null
function getBaseHost() {
  if (_baseHost == null) _baseHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
  return _baseHost
}
export function imageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  const sep = url.includes('?') ? '&' : '?'
  const token = localStorage.getItem('access_token') || ''
  return `${getBaseHost()}${url}${sep}token=${encodeURIComponent(token)}`
}

// 取明细的第一张发票缩略图 URL (无图返回 '')
export function lineThumbUrl(line) {
  return imageUrl(line?.invoice_images?.[0]?.url)
}

export const listExpenses = (params = {}) => client.get('/mobile/expense', { params })
export const getExpense = (id) => client.get(`/mobile/expense/${id}`)
export const createExpense = (payload) => client.post('/mobile/expense', payload)
export const updateExpense = (id, payload) => client.put(`/mobile/expense/${id}`, payload)
export const deleteExpense = (id) => client.delete(`/mobile/expense/${id}`)

export const addLine = (id, payload) => client.post(`/mobile/expense/${id}/lines`, payload)
export const updateLine = (id, lid, payload) => client.put(`/mobile/expense/${id}/lines/${lid}`, payload)
export const deleteLine = (id, lid) => client.delete(`/mobile/expense/${id}/lines/${lid}`)

export const submitExpense = (id, templateId = null) =>
  client.post(`/mobile/expense/${id}/submit`, templateId ? { template_id: templateId } : {})
export const recallExpense = (id, reason = '') => client.post(`/mobile/expense/${id}/recall`, { reason })
export const resubmitExpense = (id) => client.post(`/mobile/expense/${id}/resubmit`)
export const autoTitle = (id) => client.post(`/mobile/expense/${id}/auto-title`, {})

export const getFlow = (id) => client.get(`/mobile/expense/${id}/flow`)

export const getCategories = () => client.get('/mobile/expense/categories')
export const getCurrencies = () => client.get('/mobile/expense/currencies')
export const getExchangeRate = (from, to) =>
  client.get('/mobile/expense/exchange-rate', { params: { from, to } })

// 发票上传 + OCR — multipart
export const uploadInvoice = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return client.post('/mobile/expense/upload-invoice', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
