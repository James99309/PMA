<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProjects, getProjectOwners } from '@/api/projects'
import FilterSheet from '@/components/FilterSheet.vue'
import { saveListState, loadListState } from '@/utils/listStateCache'

const { t } = useI18n()

const router = useRouter()
const projects = ref([])
const total = ref(0)
const totalAmount = ref(0)
// backend-formatted total (single source: dictionary_helpers.format_money);
// null/empty when result mixes currencies → hide total
const totalAmountDisplay = ref('')
const loading = ref(false)
const search = ref('')
const page = ref(1)
const showFilter = ref(false)
const searchFocused = ref(false)
const showSortMenu = ref(false)
const sortMenuTop = ref(0)
const sortTabsEl = ref(null)
const filters = ref({})
const sortBy = ref('updated_at')
const allOwners = ref([])

const now = new Date()
const quarter = `${now.getFullYear()} · Q${Math.ceil((now.getMonth() + 1) / 3)}`

// 严格对齐 unified-lists / customer-screens StageDot tone map
const STAGE_COLOR = {
  discover:   '#7A7570',  // ink-3
  embed:      '#7A7570',
  pre_tender: '#7A7570',
  tendering:  '#D97757',  // accent
  awarded:    '#D97757',
  quoted:     '#D97757',
  signed:     '#1A1A1A',  // ink
  lost:       '#C2BBB3',  // ink-4
  paused:     '#C2BBB3',
}

// 字典 label 改 computed, 跟随 i18n locale 切换
const STAGE_LABEL_MAP = computed(() => ({
  '': t('project.stageOpt.'),
  discover: t('project.stageOpt.discover'),
  embed: t('project.stageOpt.embed'),
  pre_tender: t('project.stageOpt.pre_tender'),
  tendering: t('project.stageOpt.tendering'),
  awarded: t('project.stageOpt.awarded'),
  quoted: t('project.stageOpt.quoted'),
  signed: t('project.stageOpt.signed'),
  lost: t('project.stageOpt.lost'),
  paused: t('project.stageOpt.paused'),
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

const ACTIVITY_LABEL_MAP = computed(() => ({
  highly_active: t('project.activityOpt.highly_active'),
  active: t('project.activityOpt.active'),
  normal: t('project.activityOpt.normal'),
  to_follow: t('project.activityOpt.to_follow'),
  dormant: t('project.activityOpt.dormant'),
  churned: t('project.activityOpt.churned'),
  frozen: t('project.activityOpt.frozen'),
}))

const SORT_OPTIONS = computed(() => [
  { value: 'amount_desc', label: t('project.sortAmountDesc'), tab: 'amount' },
  { value: 'amount_asc',  label: t('project.sortAmountAsc'),  tab: 'amount' },
  { value: 'updated_at',  label: t('project.sortRecent'),     tab: 'recent' },
  { value: 'created_at',  label: t('project.sortCreated'),    tab: 'recent' },
  { value: 'stage',       label: t('project.sortStage'),      tab: 'stage'  },
])

const SORT_TABS = computed(() => [
  { tab: 'recent', label: t('project.sortByRecent') },
  { tab: 'amount', label: t('project.sortByAmount') },
  { tab: 'stage',  label: t('project.sortByStage') },
])

const activeSortTab = computed(() =>
  SORT_OPTIONS.value.find(o => o.value === sortBy.value)?.tab || 'recent'
)

function tabDisplayLabel(tab) {
  if (activeSortTab.value !== tab.tab) return tab.label
  const arrow = sortBy.value === 'amount_asc' ? ' ↑' : ' ↓'
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

// Active filter chips for display
const activeFilterChips = computed(() => {
  const chips = []
  const f = filters.value
  if (f.stage)      chips.push({ key: 'stage',      label: STAGE_LABEL_MAP.value[f.stage] || f.stage })
  if (f.activity)   chips.push({ key: 'activity',   label: ACTIVITY_LABEL_MAP.value[f.activity] || f.activity })
  if (f.amount_min != null || f.amount_max != null) {
    const mn = f.amount_min || 0
    const mx = f.amount_max
    if (mx != null) chips.push({ key: 'amount', label: t('project.amountRange', { min: mn, max: mx }) })
    else chips.push({ key: 'amount', label: t('project.amountMin', { min: mn }) })
  }
  if (f.owner_names?.length) chips.push({
    key: 'owner_names',
    label: f.owner_names.length === 1 ? f.owner_names[0] : t('project.ownerN', { n: f.owner_names.length }),
  })
  if (f.region)     chips.push({ key: 'region',     label: f.region })
  if (f.industry)   chips.push({ key: 'industry',   label: INDUSTRY_LABEL_MAP.value[f.industry] || f.industry })
  return chips
})

const activeFilterCount = computed(() => activeFilterChips.value.length)

// V2: owner options 来自后端 /mobile/projects/owners(复用 web _get_project_owner_options),
// 覆盖当前用户全部可见项目的 owner,不再受首页加载数据所限。
const ownerOptions = computed(() => allOwners.value)

function removeChip(chip) {
  const f = { ...filters.value }
  if (chip.key === 'amount') {
    delete f.amount_min
    delete f.amount_max
  } else {
    delete f[chip.key]
  }
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

function formatAmount(amount) {
  if (!amount) return '—'
  return t('project.amountWan', { amount: amount.toFixed(2) })
}

function ownerCity(p) {
  return [p.owner_name, p.city].filter(Boolean).join(' · ')
}

// Map frontend sort values to backend param
function backendSort(val) {
  if (val === 'amount_desc') return 'amount'
  if (val === 'amount_asc')  return 'amount_asc'
  return val
}

async function load(reset = false) {
  if (reset) { page.value = 1; projects.value = [] }
  loading.value = true
  try {
    const res = await getProjects({
      search: search.value,
      page: page.value,
      per_page: 20,
      sort: backendSort(sortBy.value),
      ...filters.value,
    })
    const data = res.data.data
    total.value = data.total
    totalAmount.value = data.total_amount || 0
    totalAmountDisplay.value = data.total_amount_display || ''
    projects.value = reset ? data.items : [...projects.value, ...data.items]
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (projects.value.length < total.value) {
    page.value++
    load()
  }
}

function applyFilters(f) {
  filters.value = f
  load(true)
}

// restore last filter/search/sort so detail → back keeps the filtered list
const _s = loadListState('projects')
if (_s) {
  search.value = _s.search || ''
  filters.value = _s.filters || {}
  sortBy.value = _s.sortBy || 'updated_at'
}
onBeforeUnmount(() => {
  saveListState('projects', {
    search: search.value, filters: filters.value, sortBy: sortBy.value,
  })
})

onMounted(() => {
  load(true)
  getProjectOwners()
    .then(res => {
      const list = res?.data?.data || []
      allOwners.value = list.map(o => ({ name: o.label }))
    })
    .catch(e => console.warn('load project owners failed', e))
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
            style="font-size: 32px; font-weight: 500; letter-spacing: -0.4px; color: var(--color-ink);">{{ t('project.title') }}</h1>
        </div>
        <button @click="router.push('/projects/new')"
          class="w-9 h-9 rounded-full inline-flex items-center justify-center"
          style="background: var(--color-ink); color: #fff; font-size: 20px; font-weight: 300;">+</button>
      </div>
      <div class="text-[12px] mt-1.5" style="color: var(--color-ink-3);">
        {{ t('project.listTotal', { n: total }) }}<template v-if="totalAmountDisplay"> · {{ t('project.listTotalAmount', { amount: totalAmountDisplay }) }}</template>
      </div>

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
          <input v-model="search" type="search" :placeholder="t('project.searchPh')"
            @focus="searchFocused = true" @blur="searchFocused = false"
            @keyup.enter="load(true)"
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

    <!-- FilterBanner 已激活筛选条 — 对齐 unified-lists FilterBanner -->
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

    <!-- SortRow — 对齐 unified-lists.SortRow -->
    <div ref="sortTabsEl" class="flex items-center gap-3.5 px-6 pb-2.5 shrink-0">
      <button v-for="tab in SORT_TABS" :key="tab.tab" @click="openSortMenu"
        class="text-[12px] active:opacity-70"
        :style="{
          color: activeSortTab === tab.tab ? 'var(--color-ink-2)' : 'var(--color-ink-3)',
          fontWeight: activeSortTab === tab.tab ? 600 : 400,
        }">
        {{ tabDisplayLabel(tab) }}
      </button>
      <span class="ml-auto text-[12px]" style="color: var(--color-ink-3);">{{ total }} {{ t('project.items') }}</span>
    </div>

    <!-- 列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading && projects.length === 0" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 rounded-full animate-spin"
          style="border-color: var(--color-accent); border-top-color: transparent;" />
      </div>

      <div v-else-if="projects.length === 0"
        class="flex flex-col items-center justify-center h-40 text-[13px]"
        style="color: var(--color-ink-3);">{{ t('project.listEmpty') }}</div>

      <div v-else style="background: var(--color-card);">
        <!-- ProjectRow — 对齐 unified-lists.ProjectRow -->
        <div v-for="(p, i) in projects" :key="p.id"
          @click="router.push(`/projects/${p.id}`)"
          class="px-6 py-3.5 cursor-pointer active:bg-bg flex flex-col gap-1.5"
          :style="i < projects.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
          <!-- title + amount -->
          <div class="flex items-baseline justify-between gap-3">
            <div class="font-serif flex-1 min-w-0 truncate"
              style="font-size: 16px; font-weight: 500; color: var(--color-ink); line-height: 1.3;">
              {{ p.name }}
            </div>
            <div class="text-[15px] font-semibold tabular whitespace-nowrap">
              <template v-if="p.amount_display">{{ p.amount_display }}</template>
              <span v-else class="text-[13px]" style="color: var(--color-ink-3);">—</span>
            </div>
          </div>
          <!-- meta line: stage + owner·region + date -->
          <div class="flex items-center gap-3 text-[12px]" style="color: var(--color-ink-3);">
            <span class="inline-flex items-center gap-1.5 font-medium shrink-0"
              :style="{ color: STAGE_COLOR[p.current_stage] || 'var(--color-ink-3)' }">
              <span class="w-[5px] h-[5px] rounded-[3px]"
                :style="{ background: STAGE_COLOR[p.current_stage] || 'var(--color-ink-3)' }" />
              {{ p.stage_label }}
            </span>
            <span class="truncate">{{ ownerCity(p) }}</span>
            <span class="ml-auto tabular shrink-0">{{ formatDate(p.updated_at) }}</span>
          </div>
        </div>

        <div v-if="projects.length < total" class="py-5 text-center"
          style="border-top: 1px solid var(--color-divider);">
          <button @click="loadMore" :disabled="loading"
            class="text-[13px] font-medium disabled:opacity-40"
            style="color: var(--color-accent);">
            {{ loading ? t('common.loading') : t('project.loadMore') }}
          </button>
        </div>
      </div>
    </div>

    <FilterSheet
      v-model="showFilter"
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
            class="flex items-center justify-between w-full px-5 py-3.5 text-[14px] font-medium active:bg-bg transition-colors"
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
.search-drop-enter-active,
.search-drop-leave-active {
  transition: max-height 0.22s ease, opacity 0.18s ease;
  max-height: 80px;
}
.search-drop-enter-from,
.search-drop-leave-to {
  max-height: 0;
  opacity: 0;
}
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
