<!--
  ExpenseListView · 报销列表
  对齐 ProjectListView/CustomerListView 标准布局:
  - PageHead: 季度小字 + 32px 标题 + FAB; 共 N 单 · ¥X 待审批
  - 搜索 (圆角胶囊 38px, focused accent border) + 筛选按钮 (38x38 红点)
  - SortRow (最近/金额/状态)
  - 行: 标题 16 serif + 金额 15 tabular; meta(状态彩点 + 申请人 + 当前节点 + 日期)
-->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useExpenseStore } from '@/stores/expense'
import { listExpenses, deleteExpense } from '@/api/expense'
import SwipeRowAction from '@/components/common/SwipeRowAction.vue'

async function onDelete(it) {
  if (it.status !== 'draft') {
    alert('只有草稿状态的报销单可以删除')
    return
  }
  if (!confirm(`确认删除「${it.title || '未命名报销'}」?`)) return
  try {
    await deleteExpense(it.id)
    items.value = items.value.filter(x => x.id !== it.id)
    total.value = Math.max(0, total.value - 1)
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.message || e.message))
  }
}

const router = useRouter()
const store = useExpenseStore()

const items = ref([])
const total = ref(0)
const summary = ref({ month_total: 0, pending_count: 0, total_count: 0, currency: 'CNY' })
const page = ref(1)
const loading = ref(false)
const search = ref('')
const searchFocused = ref(false)
const showFilter = ref(false)
const filters = ref({})  // { status: 'pending' }
const sortBy = ref('updated_at')
const showSortMenu = ref(false)
const sortMenuTop = ref(0)
const sortTabsEl = ref(null)

const now = new Date()
const quarter = `${now.getFullYear()} · Q${Math.ceil((now.getMonth() + 1) / 3)}`

// 状态颜色 — 对齐 _STATUS_META 后端
const STATUS_COLOR = {
  draft:    '#7A7570',  // ink-3
  pending:  '#C77B22',  // warn
  approved: '#2F7A4F',  // green
  rejected: '#B5453A',  // red
  awaiting_payment: '#C77B22',
  paid:     '#3A6FB7',  // blue
}
const STATUS_LABEL = {
  draft: '草稿', pending: '审批中', approved: '已通过',
  rejected: '已驳回', awaiting_payment: '待支付', paid: '已支付',
}

// Sort options
const SORT_OPTIONS = [
  { value: 'updated_at',    label: '最近活跃',     tab: 'recent' },
  { value: 'created_at',    label: '创建时间',     tab: 'recent' },
  { value: 'amount_desc',   label: '金额 高 → 低', tab: 'amount' },
  { value: 'amount_asc',    label: '金额 低 → 高', tab: 'amount' },
  { value: 'status',        label: '状态',         tab: 'status' },
]
const SORT_TABS = [
  { tab: 'recent', label: '最近活跃' },
  { tab: 'amount', label: '金额' },
  { tab: 'status', label: '状态' },
]
const activeSortTab = computed(() =>
  SORT_OPTIONS.find(o => o.value === sortBy.value)?.tab || 'recent'
)
function tabDisplayLabel(tab) {
  if (activeSortTab.value !== tab.tab) return tab.label
  const arrow = sortBy.value === 'amount_asc' ? ' ↑' : ' ↓'
  return tab.label + arrow
}
function openSortMenu() {
  if (sortTabsEl.value) {
    sortMenuTop.value = sortTabsEl.value.getBoundingClientRect().bottom + 4
  }
  showSortMenu.value = true
}
function selectSort(val) {
  sortBy.value = val
  showSortMenu.value = false
  load(true)
}

// Filter chips
const STATUS_FILTER_OPTIONS = [
  { value: '',         label: '全部' },
  { value: 'draft',    label: '草稿' },
  { value: 'pending',  label: '审批中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
  { value: 'paid',     label: '已支付' },
]
const activeFilterChips = computed(() => {
  const chips = []
  const f = filters.value
  if (f.status) chips.push({ key: 'status', label: STATUS_LABEL[f.status] || f.status })
  return chips
})
const activeFilterCount = computed(() => activeFilterChips.value.length)
function removeChip(chip) {
  const f = { ...filters.value }
  delete f[chip.key]
  applyFilters(f)
}
function clearAllFilters() { applyFilters({}) }
function applyFilters(f) { filters.value = f; load(true) }

// 内联快速筛选 sheet
const showStatusFilter = ref(false)
function pickStatus(val) {
  applyFilters({ ...filters.value, ...(val ? { status: val } : { status: undefined }) })
  showStatusFilter.value = false
}

function fmtAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function currencySymbol(code) {
  const m = { CNY: '¥', USD: '$', HKD: 'HK$', TWD: 'NT$', SGD: 'S$', MYR: 'RM', IDR: 'Rp', THB: '฿', VND: '₫' }
  return m[code] || code
}
function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date()
  if (d.toDateString() === today.toDateString()) return d.toTimeString().slice(0, 5)
  if (d.getFullYear() === today.getFullYear()) {
    return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')}`
  }
  return iso.slice(0, 10)
}

// 排序映射到后端
function backendSort(val) {
  if (val === 'amount_desc') return 'amount'
  if (val === 'amount_asc')  return 'amount_asc'
  return val
}

async function load(reset = false) {
  if (reset) { page.value = 1; items.value = [] }
  loading.value = true
  try {
    const r = await listExpenses({
      scope: 'mine',
      search: search.value || undefined,
      status: filters.value.status || undefined,
      sort: backendSort(sortBy.value),
      page: page.value,
      per_page: 20,
    })
    const d = r.data?.data || {}
    items.value = reset ? (d.items || []) : [...items.value, ...(d.items || [])]
    total.value = d.total || 0
    summary.value = d.summary || summary.value
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (items.value.length < total.value) {
    page.value++
    load()
  }
}

onMounted(() => {
  store.loadReference()
  load(true)
})
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- ─── PageHead 严格对齐 ProjectListView ─────────────── -->
    <div class="px-6 pt-3.5 shrink-0">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-[11px] font-medium uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1.2px;">{{ quarter }}</div>
          <h1 class="font-serif m-0 mt-1"
            style="font-size: 32px; font-weight: 500; letter-spacing: -0.4px; color: var(--color-ink);">报销</h1>
        </div>
        <button @click="router.push('/expense/new')"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center"
          style="background: var(--color-ink); color: #fff; font-size: 20px; font-weight: 300;">+</button>
      </div>
      <div class="text-[12px] mt-1.5" style="color: var(--color-ink-3);">
        共 {{ total }} 单
        <template v-if="summary.month_total">
          · 本月 ¥{{ fmtAmount(summary.month_total) }}
        </template>
        <template v-if="summary.pending_count > 0">
          · <span style="color: var(--color-ex-warn); font-weight: 600;">{{ summary.pending_count }}</span> 待审批
        </template>
      </div>

      <!-- 搜索 + 筛选 -->
      <div class="flex gap-2 mt-3.5 mb-3">
        <div class="flex-1 h-[38px] rounded-full flex items-center gap-2 px-3.5 transition-colors"
          :style="{
            background: searchFocused ? 'var(--color-card)' : 'rgba(0,0,0,0.04)',
            border: searchFocused ? '1.5px solid var(--color-accent)' : '1px solid transparent',
          }">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" :stroke="searchFocused ? 'var(--color-accent)' : 'var(--color-ink-3)'" stroke-width="1.4" />
            <path d="M11 11l3 3" :stroke="searchFocused ? 'var(--color-accent)' : 'var(--color-ink-3)'" stroke-width="1.4" stroke-linecap="round" />
          </svg>
          <input v-model="search" type="search" placeholder="搜索报销主题"
            @focus="searchFocused = true" @blur="searchFocused = false"
            @keyup.enter="load(true)"
            class="flex-1 bg-transparent text-[14px] outline-none font-serif"
            style="color: var(--color-ink);" />
          <button v-if="search" @click="search = ''; load(true)"
            class="text-[12px] font-medium" style="color: var(--color-accent);">取消</button>
        </div>
        <button @click="showStatusFilter = true"
          class="w-[38px] h-[38px] rounded-full flex items-center justify-center relative"
          :style="{ background: activeFilterCount > 0 ? 'var(--color-accent-soft)' : 'rgba(0,0,0,0.04)' }">
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
            <path d="M2 4h14l-5 6v5l-4-2v-3L2 4z"
              :stroke="activeFilterCount > 0 ? 'var(--color-accent)' : 'var(--color-ink-2)'"
              stroke-width="1.4" stroke-linejoin="round"
              :fill="activeFilterCount > 0 ? 'var(--color-accent-soft)' : 'none'" />
          </svg>
          <span v-if="activeFilterCount > 0"
            class="absolute w-[7px] h-[7px] rounded-full"
            style="top: 7px; right: 7px; background: var(--color-accent); border: 1.5px solid var(--color-bg);" />
        </button>
      </div>
    </div>

    <!-- FilterBanner -->
    <div v-if="activeFilterCount > 0" class="mx-6 mb-3 px-3 py-2.5 rounded-xl flex items-center gap-2"
      style="background: var(--color-accent-bg);">
      <span class="text-[12px] font-serif italic" style="color: var(--color-ink-2);">已按</span>
      <div class="flex flex-wrap gap-1.5 flex-1">
        <button v-for="chip in activeFilterChips" :key="chip.key" @click="removeChip(chip)"
          class="inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full text-[12px] font-medium text-white active:opacity-70"
          style="background: var(--color-ink);">
          {{ chip.label }}
          <svg width="9" height="9" viewBox="0 0 10 10">
            <path d="M2 2l6 6M8 2l-6 6" stroke="#fff" stroke-width="1.4" stroke-linecap="round" />
          </svg>
        </button>
      </div>
      <button @click="clearAllFilters" class="text-[12px] font-semibold active:opacity-60"
        style="color: var(--color-accent);">清除</button>
    </div>

    <!-- SortRow -->
    <div ref="sortTabsEl" class="flex items-center gap-3.5 px-6 pb-2.5 shrink-0">
      <button v-for="tab in SORT_TABS" :key="tab.tab" @click="openSortMenu"
        class="text-[12px] active:opacity-70"
        :style="{
          color: activeSortTab === tab.tab ? 'var(--color-ink-2)' : 'var(--color-ink-3)',
          fontWeight: activeSortTab === tab.tab ? 600 : 400,
        }">
        {{ tabDisplayLabel(tab) }}
      </button>
      <span class="ml-auto text-[12px]" style="color: var(--color-ink-3);">{{ total }} 条</span>
    </div>

    <!-- 列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading && items.length === 0" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 rounded-full animate-spin"
          style="border-color: var(--color-accent); border-top-color: transparent;" />
      </div>

      <div v-else-if="items.length === 0"
        class="flex flex-col items-center justify-center h-40 text-[13px]"
        style="color: var(--color-ink-3);">暂无报销单</div>

      <div v-else style="background: var(--color-card);">
        <SwipeRowAction
          v-for="(it, i) in items"
          :key="it.id"
          :disabled="it.status !== 'draft'"
          :actions="[{ label: '删除', color: 'red', handler: () => onDelete(it) }]"
        >
          <div
            @click="router.push(`/expense/${it.id}`)"
            class="px-6 py-3.5 cursor-pointer flex flex-col gap-1.5"
            :style="[
              i < items.length - 1 ? { borderBottom: '1px solid var(--color-divider)' } : {},
              { background: 'var(--color-card)' },
            ]">
            <!-- 标题 + 金额 -->
            <div class="flex items-baseline justify-between gap-3">
              <div class="font-serif flex-1 min-w-0 truncate"
                style="font-size: 16px; font-weight: 500; color: var(--color-ink); line-height: 1.3;">
                {{ it.title || '未命名报销' }}
              </div>
              <div class="text-[15px] font-semibold tabular whitespace-nowrap"
                style="color: var(--color-ink);">
                {{ currencySymbol(it.currency) }}{{ fmtAmount(it.amount) }}
              </div>
            </div>
            <!-- meta: 状态 + 单号·明细 + 当前节点 + 日期 -->
            <div class="flex items-center gap-3 text-[12px]" style="color: var(--color-ink-3);">
              <span class="inline-flex items-center gap-1.5 font-medium shrink-0"
                :style="{ color: STATUS_COLOR[it.status] || 'var(--color-ink-3)' }">
                <span class="w-[5px] h-[5px] rounded-[3px]"
                  :style="{ background: STATUS_COLOR[it.status] || 'var(--color-ink-3)' }" />
                {{ STATUS_LABEL[it.status] || it.status }}
              </span>
              <span class="truncate">
                {{ it.expense_number }}
                <template v-if="it.detail_count"> · {{ it.detail_count }} 项</template>
                <template v-if="it.current_node"> · 当前 {{ it.current_node }}</template>
              </span>
              <span class="ml-auto tabular shrink-0">{{ formatDate(it.apply_at) }}</span>
            </div>
          </div>
        </SwipeRowAction>

        <div v-if="items.length < total" class="py-5 text-center"
          style="border-top: 1px solid var(--color-divider);">
          <button @click="loadMore" :disabled="loading"
            class="text-[13px] font-medium disabled:opacity-40"
            style="color: var(--color-accent);">
            {{ loading ? '加载中…' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 状态快速筛选 sheet -->
    <Teleport to="body">
      <div v-if="showStatusFilter" class="fixed inset-0 z-50"
        style="background: rgba(0,0,0,0.32);"
        @click.self="showStatusFilter = false">
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl"
          style="background: var(--color-bg); padding-bottom: env(safe-area-inset-bottom);">
          <div style="width: 36px; height: 4px; background: var(--color-divider); border-radius: 2px; margin: 10px auto 6px;" />
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div class="text-[15px] font-semibold">按状态筛选</div>
            <div class="text-[13px] active:opacity-60" style="color: var(--color-ink-3);"
              @click="showStatusFilter = false">取消</div>
          </div>
          <div>
            <div v-for="opt in STATUS_FILTER_OPTIONS" :key="opt.value"
              class="flex items-center justify-between px-5 py-3.5 active:opacity-60"
              :style="{
                background: 'var(--color-card)',
                borderTop: '1px solid var(--color-divider)',
              }"
              @click="pickStatus(opt.value)">
              <span class="text-[14px]" style="color: var(--color-ink);">{{ opt.label }}</span>
              <svg v-if="(filters.status || '') === opt.value" width="16" height="16" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2.5"
                style="color: var(--color-accent);">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 排序下拉 -->
    <Teleport to="body">
      <div v-if="showSortMenu" class="fixed inset-0 z-40" @click="showSortMenu = false">
        <div class="absolute left-4 right-4 bg-white rounded-2xl shadow-2xl overflow-hidden"
          :style="{ top: sortMenuTop + 'px' }"
          @click.stop>
          <button v-for="(opt, i) in SORT_OPTIONS" :key="opt.value"
            @click="selectSort(opt.value)"
            class="flex items-center justify-between w-full px-5 py-3.5 text-[14px] font-medium active:opacity-60"
            :style="{
              color: sortBy === opt.value ? 'var(--color-accent)' : 'var(--color-ink)',
              borderBottom: i < SORT_OPTIONS.length - 1 ? '1px solid var(--color-divider)' : 'none',
            }">
            <span>{{ opt.label }}</span>
            <svg v-if="sortBy === opt.value" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
