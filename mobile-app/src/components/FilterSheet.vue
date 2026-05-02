<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useDictionariesStore } from '@/stores/dictionaries'

const props = defineProps({
  modelValue:   { type: Boolean, default: false },
  variant:      { type: String,  default: 'project' }, // 'project' | 'customer'
  ownerOptions: { type: Array,   default: () => [] },
  filters:      { type: Object,  default: () => ({}) },
})

const emit = defineEmits(['update:modelValue', 'apply'])

const AMOUNT_MAX = 300

// 阶段选项 = 字典 + "全部"
const dictStore = useDictionariesStore()
onMounted(() => { dictStore.ensure('project_stage') })
const STAGE_OPTIONS = computed(() => [
  { value: '', label: '全部' },
  ...dictStore.list('project_stage').map(d => ({ value: d.key, label: d.label })),
])

const COMPANY_TYPE_OPTIONS = [
  { value: '',            label: '全部' },
  { value: 'user',        label: '用户' },
  { value: 'designer',    label: '顾问' },
  { value: 'contractor',  label: '总包' },
  { value: 'integrator',  label: '集成' },
  { value: 'dealer',      label: '经销' },
  { value: 'distributor', label: '分销' },
  { value: 'partner',     label: '伙伴' },
  { value: 'supplier',    label: '供应商' },
  { value: 'other',       label: '其他' },
]

// ─── 客户专属维度 —— tier 因后端无字段已删；状态对齐 activity_tracker.ACTIVITY_STATUS
const STATUS_OPTIONS = [
  { value: 'highly_active', label: '高度活跃' },
  { value: 'active',        label: '活跃' },
  { value: 'normal',        label: '正常' },
  { value: 'to_follow',     label: '待跟进' },
  { value: 'dormant',       label: '休眠' },
  { value: 'churned',       label: '流失' },
]

const OPEN_COUNT_OPTIONS = [
  { value: 'has',     label: '有进行中', min: 1 },
  { value: 'gte2',    label: '≥ 2 个',  min: 2 },
  { value: 'gte5',    label: '≥ 5 个',  min: 5 },
  { value: 'none',    label: '无',      max: 0 },
]

const REGION_OPTIONS = [
  { value: '上海' }, { value: '南京' }, { value: '广州' }, { value: '深圳' },
  { value: '杭州' }, { value: '成都' }, { value: '北京' }, { value: '苏州' },
]

const VALUE_MAX = 800  // 客户累计价值上限（万元）

// 活跃度 6 级 —— 配色与 ProjectDetailView ACTIVITY_COLORS 完全一致
const ACTIVITY_OPTIONS = [
  { value: 'highly_active', label: '高度活跃', dot: '#166534' },
  { value: 'active',        label: '活跃',     dot: '#1E40AF' },
  { value: 'normal',        label: '正常',     dot: '#0369A1' },
  { value: 'to_follow',     label: '待跟进',   dot: '#A16207' },
  { value: 'dormant',       label: '休眠',     dot: '#C2410C' },
  { value: 'churned',       label: '流失',     dot: '#4B5563' },
]

const INDUSTRY_OPTIONS = [
  { value: 'manufacturing',      label: '制造' },
  { value: 'datacenter',         label: '数据' },
  { value: 'chemical',           label: '化工' },
  { value: 'energy',             label: '能源' },
  { value: 'transportation',     label: '交通' },
  { value: 'tunnel_underground', label: '隧道' },
  { value: 'real_estate',        label: '地产' },
  { value: 'hospitality',        label: '酒店' },
  { value: 'government',         label: '政府' },
  { value: 'education',          label: '教育' },
  { value: 'healthcare',         label: '医疗' },
  { value: 'technology',         label: '科技' },
  { value: 'semiconductor',      label: '半导体' },
  { value: 'shipbuilding',       label: '造船' },
  { value: 'finance',            label: '金融' },
  { value: 'other',              label: '其他' },
]

const AVATAR_COLORS = ['#D97757','#60A5FA','#4ADE80','#F59E0B','#A78BFA','#EC4899','#14B8A6','#F97316']
function ownerColor(idx) { return AVATAR_COLORS[idx % AVATAR_COLORS.length] }

// Histogram bar heights (bell-curve shape, for project amount slider)
const BAR_HEIGHTS = [8, 18, 32, 52, 72, 88, 100, 94, 78, 58, 38, 22, 13, 8, 4]
function isBarInRange(i) {
  const barCenter = ((i + 0.5) / BAR_HEIGHTS.length) * AMOUNT_MAX
  return barCenter >= local.value.amount_min && barCenter <= local.value.amount_max
}

const minPct = computed(() => (local.value.amount_min / AMOUNT_MAX) * 100)
const maxPct = computed(() => (local.value.amount_max / AMOUNT_MAX) * 100)
const minRangeZ = computed(() => local.value.amount_min > AMOUNT_MAX * 0.7 ? 5 : 3)
const maxRangeZ = computed(() => local.value.amount_min > AMOUNT_MAX * 0.7 ? 3 : 5)

function onMinChange(e) {
  const val = parseInt(e.target.value)
  if (val < local.value.amount_max - 10) local.value.amount_min = val
}
function onMaxChange(e) {
  const val = parseInt(e.target.value)
  if (val > local.value.amount_min + 10) local.value.amount_max = val
}

const amountLabel = computed(() => {
  const mn = local.value.amount_min
  const mx = local.value.amount_max
  if (mn === 0 && mx >= AMOUNT_MAX) return '不限'
  if (mx >= AMOUNT_MAX) return `¥${mn}万以上`
  if (mn === 0) return `≤¥${mx}万`
  return `¥${mn}万~¥${mx}万`
})

// Local filter state — initialized immediately so first render has correct values
function initLocal() {
  const f = props.filters || {}
  if (props.variant === 'customer') {
    return {
      status:      f.status      || '',
      value_min:   f.value_min   ?? 0,
      value_max:   f.value_max   ?? VALUE_MAX,
      open_bucket: f.open_bucket || '',
      region:      f.region      || '',
      industry:    f.industry    || '',
    }
  }
  return { stage: f.stage || '', owner_names: Array.isArray(f.owner_names) ? [...f.owner_names] : [], amount_min: f.amount_min ?? 0, amount_max: f.amount_max ?? AMOUNT_MAX, activity: f.activity || '', region: f.region || '', industry: f.industry || '' }
}

const local = ref(initLocal())

// Re-sync when sheet opens (picks up any filter changes made externally)
watch(() => props.modelValue, (v) => { if (v) local.value = initLocal() })

const pendingCount = computed(() => {
  let n = 0
  if (props.variant === 'customer') {
    if (local.value.status)      n++
    if (local.value.value_min > 0 || local.value.value_max < VALUE_MAX) n++
    if (local.value.open_bucket) n++
    if (local.value.region)      n++
    if (local.value.industry)    n++
  } else {
    if (local.value.stage) n++
    if (local.value.owner_names?.length) n++
    if (local.value.amount_min > 0 || local.value.amount_max < AMOUNT_MAX) n++
    if (local.value.activity) n++
    if (local.value.region) n++
    if (local.value.industry) n++
  }
  return n
})

function blankState() {
  if (props.variant === 'customer') {
    return {
      status: '', value_min: 0, value_max: VALUE_MAX,
      open_bucket: '', region: '', industry: '',
    }
  }
  return { stage: '', owner_names: [], amount_min: 0, amount_max: AMOUNT_MAX, activity: '', region: '', industry: '' }
}

function reset() { local.value = blankState(); showAllOwners.value = false }

const showAllOwners = ref(false)

function toggleOwner(name) {
  if (!local.value.owner_names) local.value.owner_names = []
  const idx = local.value.owner_names.indexOf(name)
  if (idx >= 0) local.value.owner_names.splice(idx, 1)
  else local.value.owner_names.push(name)
}

function apply() {
  const r = { ...local.value }
  Object.keys(r).forEach(k => {
    if (r[k] === '' || r[k] === null) delete r[k]
  })
  if (props.variant === 'customer') {
    if ((r.value_min ?? 0) <= 0) delete r.value_min
    if ((r.value_max ?? VALUE_MAX) >= VALUE_MAX) delete r.value_max
  } else {
    if ((r.amount_min ?? 0) <= 0) delete r.amount_min
    if ((r.amount_max ?? AMOUNT_MAX) >= AMOUNT_MAX) delete r.amount_max
    if (!r.owner_names?.length) delete r.owner_names  // 空数组 → 不发
  }
  emit('apply', r)
  emit('update:modelValue', false)
}

// 累计客户价值滑块（与项目金额复用 onMin/onMax 机制）
const valueMinPct = computed(() => (local.value.value_min / VALUE_MAX) * 100)
const valueMaxPct = computed(() => (local.value.value_max / VALUE_MAX) * 100)
const valueMinZ = computed(() => local.value.value_min > VALUE_MAX * 0.7 ? 5 : 3)
const valueMaxZ = computed(() => local.value.value_min > VALUE_MAX * 0.7 ? 3 : 5)
function onValueMinChange(e) {
  const val = parseInt(e.target.value)
  if (val < local.value.value_max - 20) local.value.value_min = val
}
function onValueMaxChange(e) {
  const val = parseInt(e.target.value)
  if (val > local.value.value_min + 20) local.value.value_max = val
}

function close() { emit('update:modelValue', false) }
</script>

<template>
  <Teleport to="body">
    <Transition name="filter-sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/30" @click="close" />

        <div class="relative bg-[#F7F5F2] rounded-t-3xl max-h-[90vh] min-h-[40vh] flex flex-col shadow-2xl">
          <!-- 把手 -->
          <div class="flex justify-center pt-3 pb-1 shrink-0">
            <div class="w-9 h-1 bg-[#D0CBC4] rounded-full" />
          </div>

          <!-- 标题栏 -->
          <div class="grid grid-cols-3 items-center px-5 py-3 shrink-0">
            <button @click="reset"
              class="text-[14px] font-medium active:opacity-60 text-left transition-colors"
              :class="pendingCount > 0 ? 'text-[#D97757]' : 'text-[#7A7570]'">
              重置
            </button>
            <div class="text-center">
              <p class="font-serif text-[18px] font-semibold text-[#1A1A1A] leading-tight">筛选</p>
              <p class="text-[11px] mt-0.5" :class="pendingCount > 0 ? 'text-[#7A7570]' : 'text-transparent'">
                {{ pendingCount }} 个条件
              </p>
            </div>
            <div class="flex justify-end">
              <button @click="apply"
                class="bg-[#1A1A1A] text-white text-[13px] font-semibold px-4 py-1.5 rounded-full active:bg-[#333]">
                完成
              </button>
            </div>
          </div>

          <!-- 内容 -->
          <div class="overflow-y-auto flex-1 px-5 space-y-6 pb-8">

            <!-- ── PROJECT: 阶段 ── -->
            <div v-if="variant === 'project'">
              <div class="flex items-center justify-between mb-2.5">
                <p class="text-[11px] font-semibold text-[#7A7570] tracking-wider">阶段</p>
                <p class="text-[11px] text-[#7A7570]">{{ local.stage ? '选择 1 个' : '未选' }}</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in STAGE_OPTIONS" :key="opt.value"
                  @click="local.stage = opt.value"
                  class="px-3.5 py-1.5 rounded-full border text-[13px] font-medium transition-colors active:opacity-70"
                  :class="local.stage === opt.value
                    ? 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                    : 'bg-white text-[#4A4540] border-[#E0DDD9]'">
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- ── CUSTOMER 5 维筛选（去 tier 后）── -->
            <!-- 1. 状态 -->
            <div v-if="variant === 'customer'">
              <p class="text-[11px] font-semibold uppercase mb-2.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">状态</p>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in STATUS_OPTIONS" :key="opt.value"
                  @click="local.status = local.status === opt.value ? '' : opt.value"
                  class="px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors active:opacity-70"
                  :style="local.status === opt.value
                    ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
                    : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)' }">
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- 3. 累计价值 双滑块 -->
            <div v-if="variant === 'customer'">
              <p class="text-[11px] font-semibold uppercase mb-2.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">累计价值</p>
              <div class="flex justify-between text-[13px] tabular mb-2"
                style="color: var(--color-ink-2);">
                <span>¥ {{ local.value_min }} 万</span>
                <span>¥ {{ local.value_max >= VALUE_MAX ? VALUE_MAX + '+' : local.value_max }} 万</span>
              </div>
              <div class="range-slider-wrap">
                <div class="range-track-bg" />
                <div class="range-track-fill"
                  :style="{ left: valueMinPct + '%', right: (100 - valueMaxPct) + '%' }" />
                <input type="range" min="0" :max="VALUE_MAX" step="20"
                  :value="local.value_min" @input="onValueMinChange"
                  class="range-input" :style="{ zIndex: valueMinZ }" />
                <input type="range" min="0" :max="VALUE_MAX" step="20"
                  :value="local.value_max" @input="onValueMaxChange"
                  class="range-input" :style="{ zIndex: valueMaxZ }" />
              </div>
            </div>

            <!-- 4. 进行中项目 -->
            <div v-if="variant === 'customer'">
              <p class="text-[11px] font-semibold uppercase mb-2.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">进行中项目</p>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in OPEN_COUNT_OPTIONS" :key="opt.value"
                  @click="local.open_bucket = local.open_bucket === opt.value ? '' : opt.value"
                  class="px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors active:opacity-70"
                  :style="local.open_bucket === opt.value
                    ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
                    : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)' }">
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- 5. 地区（chips 替代之前的 input）-->
            <div v-if="variant === 'customer'">
              <p class="text-[11px] font-semibold uppercase mb-2.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">地区</p>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in REGION_OPTIONS" :key="opt.value"
                  @click="local.region = local.region === opt.value ? '' : opt.value"
                  class="px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors active:opacity-70"
                  :style="local.region === opt.value
                    ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
                    : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)' }">
                  {{ opt.value }}
                </button>
              </div>
            </div>

            <!-- ── 负责人 (project only) ── -->
            <div v-if="variant === 'project' && ownerOptions.length > 0">
              <div class="flex items-center justify-between mb-3">
                <p class="text-[11px] font-semibold text-[#7A7570] tracking-wider">负责人</p>
                <p class="text-[11px] text-[#7A7570]">
                  {{ local.owner_names?.length ? `已选 ${local.owner_names.length}` : '多选·未选' }}
                </p>
              </div>
              <div class="flex flex-wrap gap-4">
                <button v-for="(owner, idx) in (showAllOwners ? ownerOptions : ownerOptions.slice(0, 7))"
                  :key="owner.name"
                  @click="toggleOwner(owner.name)" type="button"
                  class="flex flex-col items-center gap-1 active:opacity-70">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center text-[14px] font-bold text-white transition-all"
                    :style="{ background: local.owner_names?.includes(owner.name) ? '#D97757' : ownerColor(idx) }"
                    :class="local.owner_names?.includes(owner.name) ? 'ring-2 ring-offset-1 ring-[#D97757]' : ''">
                    {{ owner.name[0] }}
                  </div>
                  <span class="text-[11px] text-[#7A7570] max-w-[40px] text-center truncate">
                    {{ owner.name.slice(0, 2) }}
                  </span>
                </button>
                <button v-if="!showAllOwners && ownerOptions.length > 7"
                  @click="showAllOwners = true" type="button"
                  class="flex flex-col items-center gap-1 active:opacity-70">
                  <div class="w-10 h-10 rounded-full bg-[#ECEAE7] flex items-center justify-center text-[12px] font-medium text-[#7A7570]">
                    +{{ ownerOptions.length - 7 }}
                  </div>
                  <span class="text-[11px] text-[#7A7570]">更多</span>
                </button>
                <button v-if="showAllOwners && ownerOptions.length > 7"
                  @click="showAllOwners = false" type="button"
                  class="flex flex-col items-center gap-1 active:opacity-70">
                  <div class="w-10 h-10 rounded-full bg-[#ECEAE7] flex items-center justify-center text-[14px] font-medium text-[#7A7570]">
                    ‹
                  </div>
                  <span class="text-[11px] text-[#7A7570]">收起</span>
                </button>
              </div>
            </div>

            <!-- ── PROJECT: 金额范围 ── -->
            <div v-if="variant === 'project'">
              <div class="flex items-center justify-between mb-3">
                <p class="text-[11px] font-semibold text-[#7A7570] tracking-wider">金额范围</p>
                <p class="text-[11px] text-[#7A7570]">{{ amountLabel }}</p>
              </div>
              <div class="flex items-end gap-0.5 h-12 mb-2 px-1">
                <div v-for="(h, i) in BAR_HEIGHTS" :key="i"
                  class="flex-1 rounded-t-sm transition-colors"
                  :class="isBarInRange(i) ? 'bg-[#D97757]' : 'bg-[#D0CBC4]'"
                  :style="{ height: h + '%' }" />
              </div>
              <div class="range-slider-wrap">
                <div class="range-track-bg" />
                <div class="range-track-fill"
                  :style="{ left: minPct + '%', right: (100 - maxPct) + '%' }" />
                <input type="range" min="0" :max="AMOUNT_MAX" step="10"
                  :value="local.amount_min" @input="onMinChange"
                  class="range-input" :style="{ zIndex: minRangeZ }" />
                <input type="range" min="0" :max="AMOUNT_MAX" step="10"
                  :value="local.amount_max" @input="onMaxChange"
                  class="range-input" :style="{ zIndex: maxRangeZ }" />
              </div>
              <div class="flex justify-between mt-2 px-1">
                <span class="text-[11px] text-[#9CA3AF]">¥0</span>
                <span class="text-[11px] text-[#9CA3AF]">¥100万</span>
                <span class="text-[11px] text-[#9CA3AF]">¥300万+</span>
              </div>
            </div>

            <!-- ── PROJECT: 活跃度（6 级，3x2 网格）── -->
            <div v-if="variant === 'project'">
              <p class="text-[11px] font-semibold text-[#7A7570] tracking-wider mb-2.5">活跃度</p>
              <div class="grid grid-cols-3 gap-2">
                <button v-for="opt in ACTIVITY_OPTIONS" :key="opt.value"
                  @click="local.activity = local.activity === opt.value ? '' : opt.value"
                  class="flex items-center justify-center gap-1.5 py-2.5 rounded-2xl border text-[12px] font-medium transition-colors active:opacity-70"
                  :class="local.activity === opt.value
                    ? 'bg-[#1A1A1A] text-white border-[#1A1A1A]'
                    : 'bg-white text-[#4A4540] border-[#E0DDD9]'">
                  <span class="w-1.5 h-1.5 rounded-full"
                    :style="{ background: local.activity === opt.value ? 'white' : opt.dot }" />
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- ── 地区 (project only - input 形式) ── -->
            <div v-if="variant === 'project'">
              <div class="flex items-center justify-between mb-2.5">
                <p class="text-[11px] font-semibold text-[#7A7570] tracking-wider">地区</p>
                <p class="text-[11px] text-[#7A7570]">{{ local.region || '未选' }}</p>
              </div>
              <div class="flex items-center justify-between bg-white rounded-xl px-4 py-3 border border-[#E0DDD9]">
                <input v-model="local.region" type="text" placeholder="选择地区或城市"
                  class="flex-1 bg-transparent text-[14px] text-[#1A1A1A] outline-none placeholder-[#C2BBB3]" />
                <svg class="w-4 h-4 text-[#C2BBB3] shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 18l6-6-6-6" />
                </svg>
              </div>
            </div>

            <!-- 6. 行业（both — chips）-->
            <div class="pb-2">
              <p class="text-[11px] font-semibold uppercase mb-2.5"
                style="color: var(--color-ink-3); letter-spacing: 1px;">行业</p>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in INDUSTRY_OPTIONS" :key="opt.value"
                  @click="local.industry = local.industry === opt.value ? '' : opt.value"
                  class="px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors active:opacity-70"
                  :style="local.industry === opt.value
                    ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
                    : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)' }">
                  {{ opt.label }}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.filter-sheet-enter-active,
.filter-sheet-leave-active { transition: opacity 0.22s ease; }
.filter-sheet-enter-active .relative,
.filter-sheet-leave-active .relative { transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1); }
.filter-sheet-enter-from,
.filter-sheet-leave-to { opacity: 0; }
.filter-sheet-enter-from .relative,
.filter-sheet-leave-to .relative { transform: translateY(100%); }

.range-slider-wrap {
  position: relative;
  height: 32px;
  padding: 0 4px;
}
.range-track-bg {
  position: absolute;
  left: 4px; right: 4px;
  top: 50%; height: 4px;
  transform: translateY(-50%);
  background: #E0DDD9;
  border-radius: 2px;
}
.range-track-fill {
  position: absolute;
  top: 50%; height: 4px;
  transform: translateY(-50%);
  background: #D97757;
  border-radius: 2px;
}
.range-input {
  -webkit-appearance: none;
  appearance: none;
  position: absolute;
  left: 0; top: 0;
  width: 100%; height: 100%;
  background: transparent;
  outline: none;
  pointer-events: none;
}
.range-input::-webkit-slider-runnable-track { background: transparent; height: 4px; }
.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  pointer-events: all;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: white;
  border: 2.5px solid #D97757;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  cursor: pointer;
  margin-top: -9px;
}
</style>
