// 报销模块 Pinia store — 列表 + 详情缓存 + 草稿持久化
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/expense'

export const useExpenseStore = defineStore('expense', () => {
  // ── 列表态 ────────────────────────────────────────────
  const items = ref([])
  const summary = ref({ month_total: 0, pending_count: 0, total_count: 0, currency: 'CNY' })
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const pages = ref(1)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const r = await api.listExpenses({ scope: 'mine', ...params })
      const d = r.data?.data || {}
      items.value = d.items || []
      summary.value = d.summary || summary.value
      total.value = d.total || 0
      page.value = d.page || 1
      perPage.value = d.per_page || 20
      pages.value = d.pages || 1
    } finally {
      loading.value = false
    }
  }

  // ── 详情缓存 ──────────────────────────────────────────
  const detailCache = ref({})  // {id: detail}

  async function fetchDetail(id, forceRefresh = false) {
    if (!forceRefresh && detailCache.value[id]) return detailCache.value[id]
    const r = await api.getExpense(id)
    const d = r.data?.data
    if (d) detailCache.value[id] = d
    return d
  }

  function patchDetail(id, patch) {
    if (detailCache.value[id]) {
      detailCache.value[id] = { ...detailCache.value[id], ...patch }
    }
  }

  function clearDetail(id) {
    delete detailCache.value[id]
  }

  // ── 参考字典(科目/货币) ───────────────────────────────
  const categories = ref([])
  const statuses = ref([])
  const currencies = ref([])

  async function loadReference() {
    if (categories.value.length === 0) {
      try {
        const r = await api.getCategories()
        categories.value = r.data?.data?.categories || []
        statuses.value = r.data?.data?.statuses || []
      } catch {}
    }
    if (currencies.value.length === 0) {
      try {
        const r = await api.getCurrencies()
        currencies.value = r.data?.data?.currencies || []
      } catch {}
    }
  }

  function categoryLabel(key) {
    return categories.value.find(c => c.key === key)?.label || key
  }

  function currencySymbol(code) {
    return currencies.value.find(c => c.code === code)?.symbol || code
  }

  // ── 编辑草稿(进 ExpenseEditView 时用) ────────────────
  const editingDraft = ref(null)
  function startDraft(initial = {}) {
    editingDraft.value = {
      title: '',
      description: '',
      currency: 'CNY',
      no_link: false,
      customer_id: null,
      customer_name: '',
      project_id: null,
      project_name: '',
      ...initial,
    }
  }
  function clearDraft() { editingDraft.value = null }

  // ── OCR 待处理发票队列(连拍场景) ─────────────────────
  // 每张发票: {idx, blob, dataUrl(预览), file_url?, fields?, confidence?, status: 'pending'|'ocr'|'done'|'failed'}
  const pendingReceipts = ref([])
  const currentReceiptExpenseId = ref(null)

  function clearPendingReceipts() {
    pendingReceipts.value = []
    currentReceiptExpenseId.value = null
  }

  function addPendingReceipt(receipt) {
    receipt.idx = pendingReceipts.value.length
    receipt.status = receipt.status || 'pending'
    pendingReceipts.value.push(receipt)
  }

  function updatePendingReceipt(idx, patch) {
    if (pendingReceipts.value[idx]) {
      pendingReceipts.value[idx] = { ...pendingReceipts.value[idx], ...patch }
    }
  }

  return {
    // list
    items, summary, total, page, perPage, pages, loading,
    fetchList,
    // detail
    detailCache, fetchDetail, patchDetail, clearDetail,
    // reference
    categories, statuses, currencies,
    loadReference, categoryLabel, currencySymbol,
    // draft
    editingDraft, startDraft, clearDraft,
    // OCR pending receipts
    pendingReceipts, currentReceiptExpenseId,
    clearPendingReceipts, addPendingReceipt, updatePendingReceipt,
  }
})
