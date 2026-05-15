<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCustomers } from '@/api/customers'

const { t } = useI18n()
import FilterSheet from '@/components/FilterSheet.vue'
import Highlight from '@/components/common/Highlight.vue'

const router = useRouter()
const customers = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const page = ref(1)
const showFilter = ref(false)
const showAddSheet = ref(false)   // + 按钮弹出的"扫名片 / 手动新建"sheet
const searchFocused = ref(false)
const showSortMenu = ref(false)
const sortMenuTop = ref(0)
const sortTabsEl = ref(null)
const filters = ref({})
const sortBy = ref('updated_at')

const now = new Date()
const quarter = `${now.getFullYear()} · Q${Math.ceil((now.getMonth() + 1) / 3)}`

// 字典 label 改 computed (跟 i18n locale)
const TYPE_LABEL_MAP = computed(() => ({
  user: t('customer.role.user'), designer: t('customer.role.designer'),
  contractor: t('customer.role.contractor'), integrator: t('customer.role.integrator'),
  dealer: t('customer.role.dealer'), distributor: t('customer.role.distributor'),
  partner: t('customer.role.partner'), supplier: t('customer.role.supplier'),
  other: t('customer.role.other'),
}))

const INDUSTRY_LABEL_MAP = computed(() => ({
  manufacturing: t('project.industry.manufacturing'),
  datacenter: t('project.industry.datacenter'),
  chemical: t('project.industry.chemical'),
  energy: t('project.industry.energy'),
  transportation: t('project.industry.transportation'),
  tunnel_underground: t('project.industry.tunnel_underground'),
  real_estate: t('project.industry.real_estate'),
  hospitality: t('project.industry.hospitality'),
  government: t('project.industry.government'),
  education: t('project.industry.education'),
  healthcare: t('project.industry.healthcare'),
  technology: t('project.industry.technology'),
  semiconductor: t('project.industry.semiconductor'),
  shipbuilding: t('project.industry.shipbuilding'),
  finance: t('project.industry.finance'),
  other: t('project.industry.other'),
}))

const SORT_OPTIONS = computed(() => [
  { value: 'updated_at', label: t('customer.sortRecent'),  tab: 'recent' },
  { value: 'created_at', label: t('customer.sortCreated'), tab: 'recent' },
  { value: 'name_asc',   label: t('customer.sortNameAsc'),  tab: 'name'   },
  { value: 'name_desc',  label: t('customer.sortNameDesc'), tab: 'name'   },
])

const SORT_TABS = computed(() => [
  { tab: 'recent', label: t('customer.sortByRecent') },
  { tab: 'name',   label: t('customer.sortByName') },
])

const activeSortTab = computed(() =>
  SORT_OPTIONS.value.find(o => o.value === sortBy.value)?.tab || 'recent'
)

function tabDisplayLabel(tab) {
  if (activeSortTab.value !== tab.tab) return tab.label
  const arrow = sortBy.value === 'name_asc' ? ' ↑' : ' ↓'
  return tab.label + arrow
}

function openSortMenu() {
  if (sortTabsEl.value) {
    const rect = sortTabsEl.value.getBoundingClientRect()
    sortMenuTop.value = rect.bottom + 4
  }
  showSortMenu.value = true
}

function selectSort(val) {
  sortBy.value = val
  showSortMenu.value = false
  load(true)
}

// "活跃态" 状态集合 —— 显示绿点 (检查 zh + en 两套, status 由后端按 lang 返回)
const ACTIVE_STATUSES = computed(() => new Set([
  t('customer.activeFlag.highly_active'), t('customer.activeFlag.active'), t('customer.activeFlag.normal'),
  // 兜底中文(老 cache 数据可能仍是中文)
  '高度活跃', '活跃', '正常',
]))

const OPEN_BUCKET_LABEL = computed(() => ({
  has: t('customer.openBucket.has'), gte2: t('customer.openBucket.gte2'),
  gte5: t('customer.openBucket.gte5'), none: t('customer.openBucket.none'),
}))

const activeFilterChips = computed(() => {
  const chips = []
  const f = filters.value
  if (f.status)      chips.push({ key: 'status',      label: f.status })
  if (f.value_min != null || f.value_max != null) {
    const mn = f.value_min || 0
    const mx = f.value_max
    chips.push({ key: 'value', label: mx != null ? t('project.amountRange', { min: mn, max: mx }) : t('project.amountMin', { min: mn }) })
  }
  if (f.open_bucket) chips.push({ key: 'open_bucket', label: OPEN_BUCKET_LABEL.value[f.open_bucket] || f.open_bucket })
  if (f.region)      chips.push({ key: 'region',      label: f.region })
  if (f.industry)    chips.push({ key: 'industry',    label: INDUSTRY_LABEL_MAP.value[f.industry] || f.industry })
  return chips
})

const activeFilterCount = computed(() => activeFilterChips.value.length)

// Derive owners from loaded data
const ownerOptions = computed(() => {
  const map = new Map()
  customers.value.forEach(c => {
    if (c.owner_name && !map.has(c.owner_name)) {
      map.set(c.owner_name, { name: c.owner_name })
    }
  })
  return Array.from(map.values()).slice(0, 8)
})

function removeChip(chip) {
  const f = { ...filters.value }
  if (chip.key === 'value') { delete f.value_min; delete f.value_max }
  else delete f[chip.key]
  applyFilters(f)
}

function clearAllFilters() {
  applyFilters({})
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}

function backendSort(val) {
  if (val === 'name_asc')  return 'name'
  if (val === 'name_desc') return 'name_desc'
  return val
}

async function load(reset = false) {
  if (reset) { page.value = 1; customers.value = [] }
  loading.value = true
  try {
    const res = await getCustomers({
      search: search.value,
      page: page.value,
      per_page: 20,
      sort: backendSort(sortBy.value),
      ...filters.value,
    })
    const data = res.data.data
    total.value = data.total
    customers.value = reset ? data.items : [...customers.value, ...data.items]
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (customers.value.length < total.value) {
    page.value++
    load()
  }
}

function applyFilters(f) {
  filters.value = f
  load(true)
}

// ─── 最近搜索 (localStorage 持久化) ────────────────────────────
const RECENT_KEY = 'pma.customers.recentSearches'
const recentSearches = ref([])

function loadRecent() {
  try {
    recentSearches.value = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]').slice(0, 5)
  } catch { recentSearches.value = [] }
}

function saveRecent(q) {
  if (!q || !q.trim()) return
  const list = [q, ...recentSearches.value.filter(s => s !== q)].slice(0, 5)
  recentSearches.value = list
  localStorage.setItem(RECENT_KEY, JSON.stringify(list))
}

function pickRecent(q) {
  search.value = q
  load(true)
}

function clearRecent() {
  recentSearches.value = []
  localStorage.removeItem(RECENT_KEY)
}

function submitSearch() {
  saveRecent(search.value.trim())
  load(true)
}

onMounted(() => {
  loadRecent()
  load(true)
})
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- ─── PageHead 严格对齐 unified-lists.PageHead ─────────────── -->
    <div class="px-6 pt-3.5 shrink-0">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-[11px] font-medium uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1.2px;">{{ quarter }}</div>
          <h1 class="font-serif m-0 mt-1"
            style="font-size: 32px; font-weight: 500; letter-spacing: -0.4px; color: var(--color-ink);">{{ t('customer.title') }}</h1>
        </div>
        <button @click="showAddSheet = true"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center"
          style="background: var(--color-ink); color: #fff; font-size: 20px; font-weight: 300;">+</button>
      </div>
      <div class="text-[12px] mt-1.5" style="color: var(--color-ink-3);">{{ t('customer.listTotal', { n: total }) }}</div>

      <!-- 搜索 + 筛选 行 -->
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
          <input v-model="search" type="search" :placeholder="t('customer.searchPh')"
            @focus="searchFocused = true" @blur="searchFocused = false"
            @keyup.enter="submitSearch"
            class="flex-1 bg-transparent text-[14px] outline-none font-serif"
            style="color: var(--color-ink);" />
          <button v-if="search" @click="search = ''; load(true)"
            class="text-[12px] font-medium" style="color: var(--color-accent);">{{ t('common.cancel') }}</button>
        </div>
        <button @click="showFilter = true"
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
      <span class="text-[12px] font-serif italic" style="color: var(--color-ink-2);">{{ t('project.filteredBy') }}</span>
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
        style="color: var(--color-accent);">{{ t('project.clearFilter') }}</button>
    </div>

    <!-- SortRow / 搜索匹配数 二选一 -->
    <div v-if="search.trim()"
      class="px-6 pb-2 text-[11px] font-semibold uppercase shrink-0"
      style="color: var(--color-ink-3); letter-spacing: 1px;">
      {{ t('customer.matchN', { n: total }) }}
    </div>
    <div v-else ref="sortTabsEl" class="flex items-center gap-3.5 px-6 pb-2.5 shrink-0">
      <button v-for="tab in SORT_TABS" :key="tab.tab" @click="openSortMenu"
        class="text-[12px] active:opacity-70"
        :style="{
          color: activeSortTab === tab.tab ? 'var(--color-ink-2)' : 'var(--color-ink-3)',
          fontWeight: activeSortTab === tab.tab ? 600 : 400,
        }">
        {{ tabDisplayLabel(tab) }}
      </button>
      <span class="ml-auto text-[12px]" style="color: var(--color-ink-3);">{{ total }} {{ t('customer.items') }}</span>
    </div>

    <!-- 列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading && customers.length === 0" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 rounded-full animate-spin"
          style="border-color: var(--color-accent); border-top-color: transparent;" />
      </div>

      <div v-else-if="customers.length === 0"
        class="flex flex-col items-center justify-center h-40 text-[13px]"
        style="color: var(--color-ink-3);">{{ t('customer.listEmpty') }}</div>

      <div v-else style="background: var(--color-card);">
        <!-- CustomerRow — 严格对齐 unified-lists.CustomerRow -->
        <div v-for="(c, i) in customers" :key="c.id"
          @click="router.push(`/customers/${c.id}`)"
          class="px-6 py-3.5 cursor-pointer active:bg-bg flex gap-3 items-start"
          :style="i < customers.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">

          <!-- 42 圆角方头像（首字符）-->
          <div class="shrink-0 inline-flex items-center justify-center font-serif font-medium"
            :style="{
              width: '42px', height: '42px', borderRadius: '12px',
              background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
              fontSize: '17px',
            }">
            {{ c.name?.charAt(0) || '?' }}
          </div>

          <!-- 主信息 -->
          <div class="flex-1 min-w-0">
            <!-- title + amount -->
            <div class="flex items-baseline justify-between gap-3">
              <div class="font-serif truncate"
                style="font-size: 16px; font-weight: 500; color: var(--color-ink); line-height: 1.3;">
                <Highlight :text="c.name" :query="search.trim()" />
              </div>
              <div class="text-[15px] font-semibold tabular whitespace-nowrap">
                <template v-if="c.value > 0">
                  {{ t('project.amountWan', { amount: c.value.toFixed(2) }) }}
                </template>
                <span v-else class="text-[13px]" style="color: var(--color-ink-3);">—</span>
              </div>
            </div>

            <!-- 联系人 italic 衬线 -->
            <div v-if="c.primary_contact_name" class="text-[12px] mt-0.5 font-serif italic truncate"
              style="color: var(--color-ink-3);">{{ c.primary_contact_name }}</div>

            <!-- 状态 + 地区 + 进行中 + lastTouch -->
            <div class="flex items-center gap-3 text-[12px] mt-1" style="color: var(--color-ink-3);">
              <span v-if="c.status" class="inline-flex items-center gap-1.5 font-medium shrink-0"
                :style="{ color: ACTIVE_STATUSES.has(c.status) ? 'var(--color-green)' : 'var(--color-ink-3)' }">
                <span class="w-[5px] h-[5px] rounded-[3px]"
                  :style="{ background: ACTIVE_STATUSES.has(c.status) ? 'var(--color-green)' : 'var(--color-ink-4)' }" />
                {{ c.status }}
              </span>
              <span class="truncate">
                {{ [c.city || c.region, c.open_count != null ? t('customer.openCount', { n: c.open_count }) : null].filter(Boolean).join(' · ') }}
              </span>
              <span class="ml-auto tabular shrink-0">{{ c.last_touch || formatDate(c.updated_at) }}</span>
            </div>
          </div>
        </div>

        <div v-if="customers.length < total" class="py-5 text-center"
          style="border-top: 1px solid var(--color-divider);">
          <button @click="loadMore" :disabled="loading"
            class="text-[13px] font-medium disabled:opacity-40"
            style="color: var(--color-accent);">
            {{ loading ? t('common.loading') : t('customer.loadMore') }}
          </button>
        </div>
      </div>

      <!-- 最近搜索（搜索框 focused + empty 时显示，对齐 customer-screens.CustomersSearch line 296-309）-->
      <div v-if="searchFocused && !search.trim() && recentSearches.length"
        class="mt-5 px-6">
        <div class="flex items-center justify-between mb-2">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('customer.recentSearch') }}</div>
          <button @click="clearRecent" class="text-[11px] active:opacity-60"
            style="color: var(--color-accent);">{{ t('customer.clearSearch') }}</button>
        </div>
        <div class="flex flex-wrap gap-2 pb-5">
          <button v-for="(term, i) in recentSearches" :key="i"
            @click="pickRecent(term)"
            class="inline-flex items-center gap-1.5 px-3 py-[5px] rounded-full text-[12px]"
            style="background: var(--color-card); color: var(--color-ink-2); border: 1px solid var(--color-divider-strong);">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path d="M5 1.5v3l2 1" stroke="var(--color-ink-3)" stroke-width="1.2" stroke-linecap="round" />
              <circle cx="5" cy="5" r="3.5" stroke="var(--color-ink-3)" stroke-width="1.2" />
            </svg>
            {{ term }}
          </button>
        </div>
      </div>
    </div>

    <FilterSheet
      v-model="showFilter"
      variant="customer"
      :owner-options="ownerOptions"
      :filters="filters"
      @apply="applyFilters" />

    <!-- 排序下拉菜单 -->
    <Teleport to="body">
      <div v-if="showSortMenu" class="fixed inset-0 z-40" @click="showSortMenu = false">
        <div class="absolute left-4 right-4 bg-white rounded-2xl shadow-2xl overflow-hidden"
          :style="{ top: sortMenuTop + 'px' }"
          @click.stop>
          <button
            v-for="(opt, i) in SORT_OPTIONS" :key="opt.value"
            @click="selectSort(opt.value)"
            class="flex items-center justify-between w-full px-5 py-3.5 text-[14px] font-medium active:bg-bg"
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

    <!-- + 按钮: 新增客户方式选择 -->
    <Teleport to="body">
      <Transition name="add-sheet">
        <div v-if="showAddSheet" class="fixed inset-0 z-50">
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.4);"
            @click="showAddSheet = false" />
          <div class="absolute left-0 right-0 bottom-0 pb-7 pt-2.5"
            style="background: var(--color-bg); border-top-left-radius: 18px; border-top-right-radius: 18px;">
            <div class="mx-auto" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin-bottom: 14px;"></div>
            <div class="px-6 pb-1">
              <div class="font-serif" style="font-size: 20px; line-height: 1.25; color: var(--color-ink); letter-spacing: -0.3px;">
                {{ t('customer.addCustomer') }}
              </div>
              <div class="mt-1.5 mb-4" style="font-size: 13px; color: var(--color-ink-3); line-height: 1.55;">
                {{ t('customer.chooseMethod') }}
              </div>
            </div>
            <!-- 扫名片 (主推, 高亮) -->
            <button @click="showAddSheet = false; router.push('/customers/scan')"
              class="block w-full mx-4 mb-2.5 rounded-2xl px-4 py-3.5 text-left active:opacity-80"
              style="width: calc(100% - 32px); background: linear-gradient(135deg, rgba(217,119,87,0.08), rgba(251,176,64,0.06)); border: 1.5px solid rgba(217,119,87,0.4);">
              <div class="flex items-center gap-3">
                <div class="shrink-0 inline-flex items-center justify-center"
                  style="width: 40px; height: 40px; border-radius: 12px; background: var(--color-accent); color: #fff;">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <rect x="3" y="6" width="18" height="13" rx="2" stroke-linejoin="round" />
                    <circle cx="12" cy="12.5" r="3.5" />
                    <path d="M9 6V5a1 1 0 011-1h4a1 1 0 011 1v1" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-1.5">
                    <span class="font-serif" style="font-size: 16px; font-weight: 600; color: var(--color-ink);">{{ t('customer.scanCard') }}</span>
                    <span class="text-[9px] font-bold px-1.5 py-px rounded"
                      style="color: #fff; background: var(--color-accent); letter-spacing: 0.3px;">AI</span>
                  </div>
                  <div class="text-[12px] mt-1" style="color: var(--color-ink-3); line-height: 1.5;">
                    {{ t('customer.scanCardHint') }}
                  </div>
                </div>
                <span style="font-size: 18px; color: var(--color-ink-3);">›</span>
              </div>
            </button>
            <!-- 手动新建 -->
            <button @click="showAddSheet = false; router.push('/customers/new')"
              class="block w-full mx-4 mb-3 rounded-2xl px-4 py-3.5 text-left active:opacity-80"
              style="width: calc(100% - 32px); background: var(--color-card); border: 1px solid var(--color-divider);">
              <div class="flex items-center gap-3">
                <div class="shrink-0 inline-flex items-center justify-center"
                  style="width: 40px; height: 40px; border-radius: 12px; background: var(--color-bg); color: var(--color-ink-2);">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path d="M12 5v14M5 12h14" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-serif" style="font-size: 16px; font-weight: 500; color: var(--color-ink);">{{ t('customer.manualCreate') }}</div>
                  <div class="text-[12px] mt-1" style="color: var(--color-ink-3);">
                    {{ t('customer.manualCreateHint') }}
                  </div>
                </div>
                <span style="font-size: 18px; color: var(--color-ink-3);">›</span>
              </div>
            </button>
            <button @click="showAddSheet = false"
              class="block w-full mx-4 mt-2 py-3 rounded-xl text-[14px] active:opacity-70"
              style="width: calc(100% - 32px); background: transparent; border: 1px solid var(--color-divider-strong); color: var(--color-ink-2);">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.search-drop-enter-active,
.search-drop-leave-active {
  transition: max-height 0.22s ease, opacity 0.18s ease;
  max-height: 80px;
}
.search-drop-enter-from,
.search-drop-leave-to { max-height: 0; opacity: 0; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
.add-sheet-enter-active, .add-sheet-leave-active { transition: opacity .18s ease, transform .22s ease; }
.add-sheet-enter-from, .add-sheet-leave-to { opacity: 0; }
.add-sheet-enter-from > div:last-child, .add-sheet-leave-to > div:last-child { transform: translateY(20px); }
</style>
