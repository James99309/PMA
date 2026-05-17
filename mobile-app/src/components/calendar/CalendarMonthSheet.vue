<!--
  CalendarMonthSheet - month grid heatmap (work calendar).
  Bottom sheet: Mon-first grid, per-day dominant work-type colour dot,
  legend from backend (localized labels). Internal month nav; picking a
  day emits { date, ym } so parent syncs anchor + selected. Data from
  /mobile/worklog/month (owner_id aware). UI text via t().
-->
<template>
  <Teleport to="body">
    <transition name="msh">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.36);" @click.self="close">
        <div class="mt-auto flex flex-col"
          style="background: var(--color-bg, #F7F5F2); border-radius: 24px 24px 0 0;
                 box-shadow: 0 -10px 40px rgba(0,0,0,0.18); max-height: 82vh;">
          <div class="flex justify-center" style="padding-top: 8px;">
            <div style="width: 36px; height: 4px; background: #D8D2C6; border-radius: 2px;" />
          </div>

          <!-- month nav -->
          <div style="display: flex; justify-content: space-between; align-items: center;
            padding: 12px 20px 12px;">
            <span @click="shift(-1)" class="active:opacity-50"
              style="color: #7A7570; font-size: 18px; padding: 4px 6px;">‹</span>
            <span style="font-family: var(--font-serif); font-size: 19px; font-weight: 600;
              color: #1A1A1A;">{{ monthLabel }}</span>
            <span @click="shift(1)" class="active:opacity-50"
              style="color: #7A7570; font-size: 18px; padding: 4px 6px;">›</span>
          </div>

          <!-- weekday header (Mon-first, locale-driven) -->
          <div style="display: grid; grid-template-columns: repeat(7, 1fr); padding: 0 12px;
            font-size: 10px; color: #7A7570; font-weight: 600; margin-bottom: 6px;">
            <div v-for="(w, i) in weekHeader" :key="i"
              :style="{ textAlign: 'center', color: i > 4 ? '#B5AEA3' : '#7A7570' }">{{ w }}</div>
          </div>

          <!-- grid -->
          <div class="overflow-y-auto" style="padding: 0 12px 12px;">
            <div v-if="loading" style="padding: 36px 0; text-align: center;
              color: #B5AEA3; font-size: 13px;">···</div>
            <div v-else style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px;">
              <div v-for="(c, i) in cells" :key="i"
                @click="c.iso && pick(c.iso)"
                :class="c.iso ? 'active:opacity-60' : ''"
                :style="cellStyle(c, i)">
                <span v-if="c.day" :style="{ fontSize: '13px',
                  fontWeight: c.iso === selected ? 700 : 500,
                  fontFamily: 'var(--font-serif)', fontVariantNumeric: 'tabular-nums' }">
                  {{ c.day }}</span>
                <span v-if="c.dot" :style="{ marginTop: '3px', width: '5px', height: '5px',
                  borderRadius: '2.5px',
                  background: c.iso === selected ? '#FFF' : c.dot }" />
                <span v-else style="margin-top: 3px; width: 5px; height: 5px;" />
              </div>
            </div>
          </div>

          <!-- legend (backend localized labels) -->
          <div v-if="legend.length" style="padding: 10px 16px calc(14px + env(safe-area-inset-bottom));
            border-top: 1px solid #F2EEE6; font-size: 11px; color: #7A7570;
            display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <span v-for="lg in legend" :key="lg.type"
              style="display: inline-flex; align-items: center; gap: 4px;">
              <span :style="{ width: '6px', height: '6px', borderRadius: '3px',
                background: lg.color }" />
              <span>{{ lg.label }}</span>
            </span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getWorklogMonth } from '@/api/worklog'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  ym: { type: String, default: '' },                 // 'YYYY-MM' parent anchor
  selected: { type: String, default: '' },           // selected iso 'YYYY-MM-DD'
  ownerId: { type: Number, default: null },
})
const emit = defineEmits(['update:modelValue', 'pick'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const loading = ref(false)
const days = ref({})                                 // { iso: { count, types:[{color,count}] } }
const legend = ref([])
const viewYM = ref('')                               // in-sheet month being viewed

function pad2(n) { return String(n).padStart(2, '0') }
function isoOf(y, m, d) { return `${y}-${pad2(m)}-${pad2(d)}` }
const locale = () => (localStorage.getItem('lang') === 'en' ? 'en-US' : 'zh-CN')

const ymParts = computed(() => {
  const [y, m] = (viewYM.value || props.ym || '').split('-').map(Number)
  return { y: y || new Date().getFullYear(), m: m || (new Date().getMonth() + 1) }
})
const monthLabel = computed(() => {
  const { y, m } = ymParts.value
  return new Date(y, m - 1, 1).toLocaleDateString(locale(), { year: 'numeric', month: 'long' })
})
const weekHeader = computed(() => {
  // Mon..Sun localized narrow names (2024-01-01 is a Monday)
  const out = []
  for (let i = 0; i < 7; i++) {
    out.push(new Date(2024, 0, 1 + i).toLocaleDateString(locale(), { weekday: 'narrow' }))
  }
  return out
})

const cells = computed(() => {
  const { y, m } = ymParts.value
  const first = new Date(y, m - 1, 1)
  const lead = (first.getDay() + 6) % 7              // Mon-first leading blanks
  const dim = new Date(y, m, 0).getDate()            // days in month
  const out = []
  for (let i = 0; i < lead; i++) out.push({})
  for (let d = 1; d <= dim; d++) {
    const iso = isoOf(y, m, d)
    const info = days.value[iso]
    let dot = null
    if (info && info.types && info.types.length) {
      dot = info.types.slice().sort((a, b) => (b.count || 0) - (a.count || 0))[0].color
    }
    out.push({ day: d, iso, dot })
  }
  while (out.length % 7 !== 0) out.push({})
  return out
})

const todayIso = (() => { const n = new Date(); return isoOf(n.getFullYear(), n.getMonth() + 1, n.getDate()) })()
function cellStyle(c, i) {
  const isToday = c.iso && c.iso === todayIso
  const isSel = c.iso && c.iso === props.selected
  const weekend = i % 7 >= 5
  return {
    aspectRatio: '1 / 1.05', display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', padding: '4px',
    background: isSel ? '#1A1A1A' : (isToday ? '#EFEAE2' : 'transparent'),
    borderRadius: (isSel || isToday) ? '10px' : '0',
    color: isSel ? '#FFF' : (!c.day ? '#B5AEA3' : (weekend ? '#B5AEA3' : '#1A1A1A')),
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params = { ym: viewYM.value }
    if (props.ownerId != null) params.owner_id = props.ownerId
    const r = await getWorklogMonth(params)
    const d = r.data?.data || {}
    days.value = d.days || {}
    legend.value = d.legend || []
  } catch (e) {
    days.value = {}; legend.value = []
  } finally {
    loading.value = false
  }
}
function shift(delta) {
  const { y, m } = ymParts.value
  const a = new Date(y, m - 1 + delta, 1)
  viewYM.value = `${a.getFullYear()}-${pad2(a.getMonth() + 1)}`
  fetchData()
}
function pick(iso) {
  emit('pick', { date: iso, ym: viewYM.value })
  close()
}
function close() { open.value = false }

watch(() => props.modelValue, v => {
  if (v) {
    viewYM.value = props.ym || props.selected.slice(0, 7)
    fetchData()
  }
})
</script>

<style scoped>
.msh-enter-active, .msh-leave-active { transition: opacity .2s; }
.msh-enter-from, .msh-leave-to { opacity: 0; }
</style>
