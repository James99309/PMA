<!--
  CalendarView - Work Calendar agenda (C1)
  Pixel port of Claude Design "PMA Calendar" calendar-screens.jsx CalendarAgenda:
  hero + month nav + week strip + day hero + work-item rows + daily-log card.
  Data from /mobile/worklog/{month,day}; work_type_label / quality label /
  improvement text come from backend (i18n rule), other UI via t().
  Local CAL palette = design calendar-base tokens (presentational, not global).
  Deferred to later phases (inert here): scope ▾ + month grid + view toggle (C2),
  add "+" (C3), write & submit daily log (C4).
-->
<template>
  <div :style="{ background: CAL.bg, height: '100%', fontFamily: CAL.sans, color: CAL.ink,
    display: 'flex', flexDirection: 'column' }">
    <div class="status-pad" />
    <!-- Back row -->
    <div :style="{ height: '44px', display: 'flex', alignItems: 'center', padding: '0 12px',
      flexShrink: 0 }">
      <button @click="router.back()" class="active:opacity-60"
        :style="{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'none',
          border: 'none', color: CAL.ink2, fontSize: '15px', padding: 0 }">
        <span :style="{ fontSize: '22px', lineHeight: 1, fontWeight: 300 }">‹</span>
        <span>{{ t('calendar.navBack') }}</span>
      </button>
    </div>

    <!-- viewing-other amber banner -->
    <div v-if="viewingOwner" :style="{ display: 'flex', alignItems: 'center', gap: '8px',
      padding: '10px 20px', background: CAL.warnSoft,
      borderBottom: `1px solid ${CAL.warn}33`, flexShrink: 0 }">
      <span :style="ownerAva(viewingOwner.name, 18)">{{ viewingOwner.short }}</span>
      <span :style="{ flex: 1, fontSize: '12.5px', color: CAL.warn, fontWeight: 600,
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">
        {{ t('calendar.viewingBanner', { name: viewingOwner.name }) }}</span>
      <span @click="backToMine" class="active:opacity-60"
        :style="{ fontSize: '12.5px', color: CAL.ink2, fontWeight: 600, flexShrink: 0 }">
        {{ t('calendar.backToMine') }} ›</span>
    </div>

    <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '40px' }">
      <!-- hero -->
      <div :style="{ padding: '14px 20px 14px', display: 'flex', alignItems: 'flex-start',
        justifyContent: 'space-between', gap: '14px' }">
        <div :style="{ flex: 1, minWidth: 0 }">
          <div @click="scopeSheet = true" class="active:opacity-70"
            :style="{ display: 'inline-flex', alignItems: 'center', gap: '7px' }">
            <span v-if="viewingOwner" :style="ownerAva(viewingOwner.name)">
              {{ viewingOwner.short }}</span>
            <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '26px', fontWeight: 600,
              color: CAL.ink, letterSpacing: '-0.3px' }">{{ heroTitle }}</span>
            <span :style="{ fontSize: '13px', color: CAL.ink3 }">▾</span>
          </div>
          <div :style="{ fontSize: '13px', color: CAL.ink3, marginTop: '4px' }">
            {{ heroSub }}
          </div>
        </div>
        <div :style="{ width: '36px', height: '36px', borderRadius: '18px', background: CAL.ink,
          color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '22px', fontWeight: 300, lineHeight: 1, flexShrink: 0, opacity: 0.4 }">+</div>
      </div>
      <div :style="{ height: '1px', background: CAL.divider }" />

      <!-- month nav + view toggle -->
      <div :style="{ padding: '12px 20px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between' }">
        <div :style="{ display: 'inline-flex', alignItems: 'center', gap: '16px' }">
          <span @click="shiftMonth(-1)" class="active:opacity-50"
            :style="{ color: CAL.ink3, fontSize: '18px' }">‹</span>
          <span :style="{ fontSize: '16px', fontWeight: 600, fontFamily: 'var(--font-serif)' }">
            {{ monthLabel }}</span>
          <span @click="shiftMonth(1)" class="active:opacity-50"
            :style="{ color: CAL.ink3, fontSize: '18px' }">›</span>
        </div>
        <div :style="{ display: 'flex', background: CAL.dividerSoft, padding: '2px',
          borderRadius: '7px', fontSize: '11.5px', fontWeight: 600 }">
          <span v-for="(v, i) in [t('calendar.vMonth'), t('calendar.vWeek')]"
            :key="v" @click="i === 0 && (monthSheet = true)"
            :class="i === 0 ? 'active:opacity-60' : ''"
            :style="{ padding: '5px 11px', borderRadius: '5px',
              background: i === 1 ? CAL.card : 'transparent',
              color: i === 1 ? CAL.ink : CAL.ink3,
              boxShadow: i === 1 ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' }">{{ v }}</span>
        </div>
      </div>

      <!-- week strip -->
      <div :style="{ display: 'flex', padding: '0 12px 14px', gap: '4px' }">
        <div v-for="d in weekStrip" :key="d.iso" @click="selectDay(d.iso)"
          class="active:opacity-70"
          :style="{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
            padding: '8px 0', borderRadius: '10px',
            background: d.iso === selectedDate ? CAL.ink : 'transparent',
            color: d.iso === selectedDate ? '#FFF' : (d.weekend ? CAL.ink4 : CAL.ink2) }">
          <span :style="{ fontSize: '10px', fontWeight: 500, letterSpacing: '0.3px',
            color: d.iso === selectedDate ? 'rgba(255,255,255,0.7)'
              : (d.weekend ? CAL.ink4 : CAL.ink3) }">{{ d.wd }}</span>
          <span :style="{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-serif)',
            marginTop: '3px' }">{{ d.day }}</span>
          <span v-if="d.count > 0" :style="{ marginTop: '4px', width: '4px', height: '4px',
            borderRadius: '2px',
            background: d.iso === selectedDate ? '#FFF' : CAL.accent }" />
          <span v-else :style="{ marginTop: '4px', width: '4px', height: '4px' }" />
        </div>
      </div>

      <!-- day hero -->
      <div :style="{ padding: '4px 20px 6px', display: 'flex', alignItems: 'baseline',
        justifyContent: 'space-between' }">
        <div>
          <div :style="{ fontSize: '11px', color: CAL.ink3, letterSpacing: '0.6px',
            fontWeight: 600, textTransform: 'uppercase' }">{{ dayKicker }}</div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 600,
            marginTop: '2px' }">{{ dayHeroLine }}</div>
        </div>
        <div :style="{ textAlign: 'right' }">
          <div :style="{ fontSize: '10px', color: CAL.ink3 }">{{ t('calendar.totalHours') }}</div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontWeight: 600,
            color: CAL.blue, fontVariantNumeric: 'tabular-nums' }">{{ cfmt(totalHours) }}h</div>
        </div>
      </div>

      <!-- work items -->
      <div v-if="loadingDay" :style="{ padding: '40px 0', textAlign: 'center', color: CAL.ink4,
        fontSize: '13px' }">···</div>
      <div v-else-if="!dayItems.length" :style="{ padding: '48px 20px', textAlign: 'center',
        color: CAL.ink3, fontSize: '13px' }">{{ t('calendar.emptyDay') }}</div>
      <div v-else :style="{ background: CAL.card, marginTop: '6px',
        borderTop: `1px solid ${CAL.dividerSoft}`, borderBottom: `1px solid ${CAL.dividerSoft}`,
        opacity: refreshing ? 0.45 : 1, transition: 'opacity .15s' }">
        <div v-for="(it, i) in dayItems" :key="it.id"
          :style="{ padding: '14px 20px', display: 'flex', alignItems: 'flex-start', gap: '12px',
            borderBottom: i === dayItems.length - 1 ? 'none' : `1px solid ${CAL.dividerSoft}`,
            opacity: (it.status === 'completed' || it.status === 'cancelled' || it.is_invalidated) ? 0.55 : 1 }">
          <!-- time col -->
          <div :style="{ width: '46px', flexShrink: 0, textAlign: 'right', paddingTop: '1px' }">
            <div :style="{ fontSize: '12px', fontWeight: 600, color: CAL.ink,
              fontVariantNumeric: 'tabular-nums', fontFamily: 'var(--font-serif)' }">
              {{ hm(it.start_time) || (it.is_all_day ? t('calendar.allDay') : '–') }}</div>
            <div v-if="hm(it.end_time)" :style="{ fontSize: '10px', color: CAL.ink4,
              fontVariantNumeric: 'tabular-nums', marginTop: '1px' }">{{ hm(it.end_time) }}</div>
          </div>
          <!-- color bar -->
          <div :style="{ width: '3px', alignSelf: 'stretch', background: it.color || CAL.ink3,
            borderRadius: '2px', flexShrink: 0 }" />
          <!-- content -->
          <div :style="{ flex: 1, minWidth: 0 }">
            <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }">
              <span :style="{ fontSize: '10px', color: it.color || CAL.ink3,
                background: softBg(it.color), padding: '1px 6px', borderRadius: '3px',
                fontWeight: 700, letterSpacing: '0.3px' }">{{ it.work_type_label }}</span>
              <span v-if="it.is_business_trip" :style="{ fontSize: '9px', color: CAL.ink3,
                background: CAL.dividerSoft, padding: '1px 5px', borderRadius: '3px',
                fontWeight: 600, letterSpacing: '0.3px' }">{{ t('calendar.bizTrip') }}</span>
              <span v-if="it.status === 'completed'" :style="{ fontSize: '9.5px', color: CAL.green,
                background: CAL.greenSoft, padding: '1px 5px', borderRadius: '3px',
                fontWeight: 700, letterSpacing: '0.3px' }">✓ {{ t('calendar.done') }}</span>
              <span v-else-if="it.status === 'cancelled'" :style="{ fontSize: '9.5px',
                color: CAL.ink4, background: CAL.dividerSoft, padding: '1px 5px',
                borderRadius: '3px', fontWeight: 700 }">{{ t('calendar.cancelled') }}</span>
            </div>
            <div :style="{ fontSize: '14px', fontWeight: 600, marginTop: '4px', lineHeight: 1.35,
              textDecoration: (it.status === 'cancelled' || it.is_invalidated) ? 'line-through' : 'none' }">
              {{ it.title }}</div>
            <div v-if="it.description" :style="{ fontSize: '11.5px', color: CAL.ink3,
              marginTop: '3px', lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box',
              '-webkit-line-clamp': 2, '-webkit-box-orient': 'vertical' }">{{ it.description }}</div>
            <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px',
              fontSize: '10.5px', color: CAL.ink3, flexWrap: 'wrap' }">
              <span v-if="itemHours(it) != null"
                :style="{ display: 'inline-flex', alignItems: 'center', gap: '3px' }">
                <span>⏱</span>{{ cfmt(itemHours(it)) }}h</span>
              <span v-if="it.project_name" :style="{ fontSize: '10px', padding: '1px 6px',
                borderRadius: '3px', background: CAL.accentSoft, color: CAL.accent,
                fontWeight: 600, maxWidth: '140px', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">#{{ it.project_name }}</span>
              <span v-if="it.customer_name" :style="{ fontSize: '10px', padding: '1px 6px',
                borderRadius: '3px', background: CAL.tealSoft, color: CAL.teal,
                fontWeight: 600, maxWidth: '140px', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">{{ it.customer_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- daily log card -->
      <div v-if="!loadingDay && day" :style="{ padding: '18px 16px 0',
        opacity: refreshing ? 0.45 : 1, transition: 'opacity .15s' }">
        <div :style="{ background: CAL.card, borderRadius: '14px',
          border: `1px solid ${CAL.divider}`, padding: '16px' }">
          <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }">
            <span :style="{ fontSize: '11px', color: CAL.ink3, letterSpacing: '0.6px',
              fontWeight: 600, textTransform: 'uppercase' }">
              {{ t('calendar.logTitle', { d: dayHeroDateShort }) }}</span>
            <span v-if="isSubmitted" :style="{ fontSize: '10px', color: CAL.green,
              background: CAL.greenSoft, padding: '2px 7px', borderRadius: '3px',
              fontWeight: 700 }">{{ t('calendar.submitted') }}</span>
            <span v-else :style="{ fontSize: '10px', color: CAL.warn, background: CAL.warnSoft,
              padding: '2px 7px', borderRadius: '3px', fontWeight: 700 }">
              {{ t('calendar.draft') }}</span>
          </div>

          <!-- draft -->
          <template v-if="!isSubmitted">
            <div :style="{ display: 'flex', gap: '14px', marginBottom: '12px' }">
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stHours') }}</div>
                <div :style="statValStyle(CAL.blue)">{{ cfmt(totalHours) }} h</div>
              </div>
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stItems') }}</div>
                <div :style="statValStyle(CAL.ink)">{{ stats.total_items || 0 }}</div>
              </div>
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stQuality') }}</div>
                <div :style="statValStyle(CAL.ink4)">—</div>
              </div>
            </div>
            <div v-if="logSummary">
              <div :style="sectionLabelStyle">{{ t('calendar.autoSummary') }}</div>
              <div :style="{ fontSize: '13px', color: CAL.ink2, lineHeight: 1.55,
                paddingBottom: '14px', borderBottom: `1px solid ${CAL.dividerSoft}`,
                marginBottom: '12px' }">{{ logSummary }}</div>
            </div>
            <button :style="{ width: '100%', padding: '11px 0', borderRadius: '12px',
              background: CAL.accent, border: 'none', color: '#FFF', fontSize: '14px',
              fontWeight: 600, opacity: 0.45 }">{{ t('calendar.writeSubmit') }} →</button>
          </template>

          <!-- submitted -->
          <template v-else>
            <div :style="{ display: 'flex', gap: '14px', marginBottom: '14px',
              alignItems: 'flex-start' }">
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stQuality') }}</div>
                <div :style="{ display: 'inline-flex', alignItems: 'baseline', gap: '4px',
                  marginTop: '4px' }">
                  <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '38px',
                    fontWeight: 600, color: CAL.green, letterSpacing: '-1px', lineHeight: 1 }">
                    {{ quality.total }}</span>
                  <span :style="{ fontSize: '12px', color: CAL.ink3 }">/ 100</span>
                </div>
                <div :style="{ fontSize: '11px', color: CAL.green, marginTop: '4px',
                  fontWeight: 600 }">{{ quality.label }}</div>
              </div>
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stHours') }}</div>
                <div :style="statValStyle(CAL.blue)">{{ cfmt(totalHours) }}h</div>
              </div>
              <div :style="{ flex: 1 }">
                <div :style="statLabelStyle">{{ t('calendar.stItems') }}</div>
                <div :style="statValStyle(CAL.ink)">{{ stats.total_items || 0 }}</div>
              </div>
            </div>
            <template v-if="logNotes">
              <div :style="sectionLabelStyle">{{ t('calendar.supplementary') }}</div>
              <div :style="{ fontSize: '12.5px', color: CAL.ink2, lineHeight: 1.55,
                paddingBottom: '12px', borderBottom: `1px solid ${CAL.dividerSoft}`,
                marginBottom: '10px' }">{{ logNotes }}</div>
            </template>
            <template v-if="quality.issues_detail && quality.issues_detail.length">
              <div :style="sectionLabelStyle">{{ t('calendar.improvements') }}</div>
              <div v-for="(iss, i) in quality.issues_detail" :key="i"
                :style="{ padding: '8px 10px', background: CAL.blueSoft, borderRadius: '8px',
                  marginBottom: '6px' }">
                <div :style="{ fontSize: '12px', fontWeight: 600, color: CAL.blueDeep }">
                  · {{ iss.issue }}</div>
                <div :style="{ fontSize: '11px', color: CAL.ink2, marginTop: '2px' }">
                  {{ iss.suggestion }}</div>
              </div>
            </template>
          </template>
        </div>
      </div>
    </div>

    <CalendarScopeSheet v-model="scopeSheet" :current-owner-id="ownerId"
      @pick="onPickAccount" />
    <CalendarMonthSheet v-model="monthSheet" :ym="anchorYM" :selected="selectedDate"
      :owner-id="ownerId" @pick="onPickMonthDay" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getWorklogMonth, getWorklogDay } from '@/api/worklog'
import CalendarScopeSheet from '@/components/calendar/CalendarScopeSheet.vue'
import CalendarMonthSheet from '@/components/calendar/CalendarMonthSheet.vue'

const router = useRouter()
const { t } = useI18n()

// Design calendar-base palette (presentational, not global tokens)
const CAL = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', accentSoft: '#FAEEE5', blue: '#3A6FB7', blueSoft: '#E5EBF4',
  blueDeep: '#1A4A8C', green: '#2F7A4F', greenSoft: '#E9F1EB', warn: '#C77B22',
  warnSoft: '#F9F1E6', teal: '#1F8478', tealSoft: '#DEEFEB',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}

function pad2(n) { return String(n).padStart(2, '0') }
function isoOf(d) { return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}` }
function cfmt(n) {
  const v = Number(n)
  if (!isFinite(v)) return '0'
  return v.toFixed(1).replace(/\.0$/, '')
}
function hm(t8) { return t8 ? String(t8).slice(0, 5) : '' }
function softBg(hex) {
  return (hex && /^#[0-9a-fA-F]{6}$/.test(hex)) ? hex + '22' : CAL.dividerSoft
}
const locale = () => (localStorage.getItem('lang') === 'en' ? 'en-US' : 'zh-CN')

const today = new Date()
const todayIso = isoOf(today)
const selectedDate = ref(todayIso)
const monthAnchor = ref(new Date(today.getFullYear(), today.getMonth(), 1))

const loadingDay = ref(false)        // first-ever load → skeleton
const refreshing = ref(false)        // switching with prior content → dim, no blank
const monthDays = ref({})            // { 'YYYY-MM-DD': { count, types } }
const day = ref(null)                // /mobile/worklog/day data

const scopeSheet = ref(false)
const monthSheet = ref(false)
const viewingOwner = ref(null)       // {id,name,short,department,week_count} or null = self
const ownerId = computed(() => viewingOwner.value ? viewingOwner.value.id : null)
const anchorYM = computed(() =>
  `${monthAnchor.value.getFullYear()}-${pad2(monthAnchor.value.getMonth() + 1)}`)

const _AVA = ['#3A6FB7', '#7B5BAC', '#C77B22', '#2F7A4F', '#B5453A', '#D97757']
function ownerAva(name, size = 22) {
  let h = 0
  for (const c of (name || '?')) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return { width: size + 'px', height: size + 'px', borderRadius: (size / 2) + 'px',
    background: _AVA[h % _AVA.length], color: '#FFF', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: (size * 0.42) + 'px',
    fontWeight: 700, flexShrink: 0 }
}
const heroTitle = computed(() =>
  viewingOwner.value ? viewingOwner.value.name : t('calendar.title'))

const stats = computed(() => day.value?.statistics || {})
const totalHours = computed(() => stats.value.total_hours || 0)
const dayItems = computed(() => {
  const d = day.value
  if (!d) return []
  const all = [...(d.completed_items || []), ...(d.pending_items || []),
    ...(d.cancelled_items || [])]
  return all.sort((a, b) => (a.start_time || '99').localeCompare(b.start_time || '99'))
})
const logObj = computed(() => day.value?.log || null)
const isSubmitted = computed(() => logObj.value?.status === 'submitted')
const logSummary = computed(() => logObj.value?.summary || '')
const logNotes = computed(() => logObj.value?.additional_notes || '')
const quality = computed(() => day.value?.quality_score || {})

function itemHours(it) {
  const h = it.actual_hours != null ? it.actual_hours : it.estimated_hours
  return h != null ? h : null
}

const monthLabel = computed(() =>
  monthAnchor.value.toLocaleDateString(locale(), { year: 'numeric', month: 'long' }))

const heroSub = computed(() => {
  const n = Object.values(monthDays.value).reduce((s, v) => s + (v.count || 0), 0)
  return t('calendar.heroSub', { month: monthLabel.value, n })
})

const weekStrip = computed(() => {
  // week (Mon..Sun) containing selectedDate
  const sel = new Date(selectedDate.value + 'T00:00:00')
  const dow = (sel.getDay() + 6) % 7   // Mon=0
  const mon = new Date(sel); mon.setDate(sel.getDate() - dow)
  const out = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(mon); d.setDate(mon.getDate() + i)
    const iso = isoOf(d)
    out.push({
      iso, day: d.getDate(),
      wd: d.toLocaleDateString(locale(), { weekday: 'short' }),
      weekend: i >= 5,
      count: monthDays.value[iso]?.count || 0,
    })
  }
  return out
})

const selDateObj = computed(() => new Date(selectedDate.value + 'T00:00:00'))
const dayKicker = computed(() => {
  const wd = selDateObj.value.toLocaleDateString(locale(), { weekday: 'long' })
  return selectedDate.value === todayIso ? `${wd} · ${t('calendar.today')}` : wd
})
const dayHeroDateShort = computed(() =>
  selDateObj.value.toLocaleDateString(locale(), { month: 'long', day: 'numeric' }))
const dayHeroLine = computed(() =>
  t('calendar.dayHero', { d: dayHeroDateShort.value, n: dayItems.value.length }))

const statLabelStyle = { fontSize: '10px', color: CAL.ink3, fontWeight: 600,
  letterSpacing: '0.4px' }
function statValStyle(color) {
  return { fontFamily: 'var(--font-serif)', fontSize: '20px', fontWeight: 600, color,
    marginTop: '4px', fontVariantNumeric: 'tabular-nums' }
}
const sectionLabelStyle = { fontSize: '11px', color: CAL.ink3, marginBottom: '5px',
  letterSpacing: '0.4px', textTransform: 'uppercase', fontWeight: 600 }

// perf: dedupe (skip refetch when key unchanged) + seq guard (drop stale
// responses when user navigates faster than the network)
let _monthSeq = 0
let _monthKey = ''
let _daySeq = 0
let _dayKey = ''

async function loadMonth() {
  const key = `${anchorYM.value}|${ownerId.value}`
  if (key === _monthKey) return
  const seq = ++_monthSeq
  const params = { ym: anchorYM.value }
  if (ownerId.value != null) params.owner_id = ownerId.value
  try {
    const r = await getWorklogMonth(params)
    if (seq !== _monthSeq) return            // superseded by a newer nav
    monthDays.value = r.data?.data?.days || {}
    _monthKey = key
  } catch (e) {
    // keep prior month dots on error (no blank flash); only blank if never loaded
    if (seq === _monthSeq && !Object.keys(monthDays.value).length) monthDays.value = {}
  }
}
async function loadDay() {
  const key = `${selectedDate.value}|${ownerId.value}`
  if (key === _dayKey && day.value) return    // already showing this day
  const seq = ++_daySeq
  // stale-while-revalidate: skeleton only on first ever load; on subsequent
  // switches keep old content visible (dimmed) until new arrives — no empty flash
  if (!day.value) loadingDay.value = true
  else refreshing.value = true
  try {
    const params = { date: selectedDate.value }
    if (ownerId.value != null) params.owner_id = ownerId.value
    const r = await getWorklogDay(params)
    if (seq !== _daySeq) return               // superseded by a newer nav
    day.value = r.data?.data || null
    _dayKey = key
  } catch (e) {
    if (seq === _daySeq && !day.value) day.value = null  // keep prior on error
  } finally {
    if (seq === _daySeq) { loadingDay.value = false; refreshing.value = false }
  }
}
// No artificial debounce: fetch immediately so a single tap fills at once
// (no empty→full double frame). Rapid taps are made safe by the _monthSeq/
// _daySeq guards (stale responses dropped) + key dedupe (no redundant fetch).
function selectDay(iso) {
  if (iso === selectedDate.value) return
  selectedDate.value = iso
  loadDay()
}
function shiftMonth(delta) {
  const a = new Date(monthAnchor.value)
  a.setMonth(a.getMonth() + delta)
  monthAnchor.value = a
  // keep selection sensible: today if same month, else 1st of month
  const sameAsToday = a.getFullYear() === today.getFullYear()
    && a.getMonth() === today.getMonth()
  selectedDate.value = sameAsToday ? todayIso : isoOf(a)
  loadMonth()
  loadDay()
}

function onPickAccount(e) {
  if (!e || e.is_self || e.id == null) { backToMine(); return }
  if (viewingOwner.value && viewingOwner.value.id === e.id) return
  viewingOwner.value = { id: e.id, name: e.name, short: e.short,
    department: e.department, week_count: e.week_count }
  loadMonth()
  loadDay()
}
function backToMine() {
  if (!viewingOwner.value) return
  viewingOwner.value = null
  loadMonth()
  loadDay()
}
function onPickMonthDay({ date, ym }) {
  if (!date) return
  const [y, m] = ym.split('-').map(Number)
  monthAnchor.value = new Date(y, m - 1, 1)
  selectedDate.value = date
  loadMonth()
  loadDay()
}

onMounted(() => { loadMonth(); loadDay() })
</script>
