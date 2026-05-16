<!--
  TaskListView - Task Center list (P1)
  Pixel port of Claude Design "PMA Task EN" task-list-en.jsx:
  hero + underline tabs + filter row + rows. status/priority text from
  backend *_label; other UI text via t() (i18n rule). Colors use a local
  TK map (design task-base palette, not global tokens, presentational).
-->
<template>
  <div :style="{ background: TK.bg, height: '100%', fontFamily: TK.sans, color: TK.ink,
    display: 'flex', flexDirection: 'column' }">
    <div class="status-pad" />
    <!-- Back row (needed for a real screen; design canvas omits it) -->
    <div :style="{ height: '44px', display: 'flex', alignItems: 'center', padding: '0 12px',
      flexShrink: 0 }">
      <button @click="router.back()" class="active:opacity-60"
        :style="{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'none',
          border: 'none', color: TK.ink2, fontSize: '15px', padding: 0 }">
        <span :style="{ fontSize: '22px', lineHeight: 1, fontWeight: 300 }">‹</span>
        <span>{{ t('task.navBack') }}</span>
      </button>
    </div>

    <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '40px' }">
      <!-- hero -->
      <div :style="{ padding: '14px 20px 14px', display: 'flex', alignItems: 'flex-start',
        justifyContent: 'space-between', gap: '14px' }">
        <div :style="{ flex: 1, minWidth: 0 }">
          <div :style="{ display: 'inline-flex', alignItems: 'center', gap: '8px' }">
            <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '26px', fontWeight: 600,
              color: TK.ink, letterSpacing: '-0.3px' }">{{ t('task.title') }}</span>
          </div>
          <div :style="{ fontSize: '13px', color: TK.ink3, marginTop: '4px' }">
            {{ t('task.heroSub', { ip: counts.in_progress, rv: counts.review, od: counts.overdue }) }}
          </div>
        </div>
        <div :style="{ width: '36px', height: '36px', borderRadius: '18px', background: TK.ink,
          color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '22px', fontWeight: 300, lineHeight: 1, flexShrink: 0 }"
          @click="onCreate">+</div>
      </div>
      <div :style="{ height: '1px', background: TK.divider }" />

      <!-- Underline tabs -->
      <div :style="{ display: 'flex', gap: '20px', padding: '14px 20px 0',
        borderBottom: `1px solid ${TK.divider}`, overflowX: 'auto' }" class="no-scrollbar">
        <div v-for="tb in tabs" :key="tb.k" @click="switchTab(tb.k)"
          :style="{ paddingBottom: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px',
            borderBottom: activeTab === tb.k ? `2px solid ${TK.ink}` : '2px solid transparent',
            fontSize: '13.5px', fontWeight: activeTab === tb.k ? 600 : 500,
            color: activeTab === tb.k ? TK.ink : TK.ink3, whiteSpace: 'nowrap', flexShrink: 0 }">
          {{ tb.l }}
          <span v-if="tb.n > 0" :style="{ fontSize: '11.5px', fontWeight: 600,
            color: tb.alert ? TK.warn : TK.ink3 }">{{ tb.n }}</span>
        </div>
      </div>

      <!-- Filter row + sort -->
      <div :style="{ display: 'flex', alignItems: 'center', padding: '14px 20px',
        background: TK.bg, gap: '16px', overflowX: 'auto' }" class="no-scrollbar">
        <span v-for="f in statusFilters" :key="f.k" @click="statusF = f.k"
          :style="{ fontSize: '13px', fontWeight: statusF === f.k ? 600 : 500,
            color: statusF === f.k ? TK.ink : TK.ink3, whiteSpace: 'nowrap' }">{{ f.l }}</span>
        <span @click="toggleSort"
          :style="{ marginLeft: 'auto', fontSize: '12.5px', color: TK.ink3,
            display: 'inline-flex', alignItems: 'center', gap: '3px', flexShrink: 0 }">
          {{ sort === 'due_asc' ? '↑' : '↓' }} {{ t('task.sortDue') }}
        </span>
      </div>

      <!-- List -->
      <div v-if="loading" :style="{ padding: '40px 0', textAlign: 'center', color: TK.ink4,
        fontSize: '13px' }">···</div>
      <div v-else-if="!items.length" :style="{ padding: '48px 0', textAlign: 'center',
        color: TK.ink3, fontSize: '13px' }">{{ t('task.empty') }}</div>
      <div v-else :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(it, i) in items" :key="it.id"
          :style="{ padding: '13px 20px', display: 'flex', alignItems: 'flex-start', gap: '11px',
            borderBottom: i === items.length - 1 ? 'none' : `1px solid ${TK.dividerSoft}` }">
          <!-- Status dot -->
          <span :style="{ width: '8px', height: '8px', borderRadius: '4px', flexShrink: 0,
            marginTop: '5px', background: stat(it.status).color,
            boxShadow: it.status === 'in_progress' ? `0 0 0 3px ${stat(it.status).bg}` : 'none' }" />
          <div :style="{ flex: 1, minWidth: 0 }">
            <div :style="{ display: 'flex', alignItems: 'flex-start', gap: '8px' }">
              <div :style="{ flex: 1, minWidth: 0 }">
                <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }">
                  <span :style="{ fontSize: '14.5px', fontWeight: 600, color: TK.ink, lineHeight: 1.35 }">{{ it.title }}</span>
                  <span v-if="it.priority === 'urgent' || it.priority === 'high'"
                    :style="chipStyle(pri(it.priority))">{{ it.priority_label }}</span>
                </div>
                <div v-if="it.desc" :style="{ fontSize: '11.5px', color: TK.ink3, marginTop: '4px',
                  lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box',
                  '-webkit-line-clamp': 1, '-webkit-box-orient': 'vertical' }">{{ it.desc }}</div>
              </div>
              <div :style="{ textAlign: 'right', flexShrink: 0 }">
                <div :style="{ fontSize: '13px', fontWeight: 600, fontVariantNumeric: 'tabular-nums',
                  color: it.overdue ? TK.red : TK.ink2 }">{{ it.due || '–' }}</div>
                <div v-if="it.overdue" :style="{ fontSize: '9.5px', color: TK.red, fontWeight: 700,
                  letterSpacing: '0.4px', textTransform: 'uppercase' }">{{ t('task.overdue') }}</div>
              </div>
            </div>
            <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px',
              fontSize: '11px', color: TK.ink3, flexWrap: 'wrap' }">
              <span :style="{ display: 'inline-flex', alignItems: 'center', gap: '4px' }">
                <span :style="avatarStyle(it.assignee_name, 16)">{{ it.assignee_short }}</span>
                <span :style="{ color: TK.ink2, fontWeight: 500 }">{{ it.assignee_name }}</span>
              </span>
              <span v-if="it.sub.total > 0" :style="{ display: 'inline-flex', alignItems: 'center', gap: '5px' }">
                <span :style="{ width: '36px', height: '3px', borderRadius: '1.5px',
                  background: TK.divider, overflow: 'hidden' }">
                  <span :style="{ display: 'block', height: '100%',
                    width: (it.sub.done / it.sub.total * 100) + '%',
                    background: it.status === 'pending_review' ? TK.purple : TK.blue }" />
                </span>
                <span :style="{ fontSize: '10px', color: TK.ink4 }">{{ it.sub.done }}/{{ it.sub.total }}</span>
              </span>
              <span v-if="it.project" :style="{ fontSize: '10px', padding: '1px 6px', borderRadius: '3px',
                background: TK.accentSoft, color: TK.accent, fontWeight: 600, maxWidth: '130px',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">#{{ it.project }}</span>
              <span :style="{ marginLeft: 'auto' }">
                <span :style="chipStyle(stat(it.status))">{{ it.status_label }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getTasks } from '@/api/tasks'

const router = useRouter()
const { t } = useI18n()

// Design task-base palette (purple etc. not in global tokens; presentational)
const TK = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', accentSoft: '#FAEEE5', blue: '#3A6FB7', blueSoft: '#E5EBF4',
  green: '#2F7A4F', greenSoft: '#E9F1EB', warn: '#C77B22', warnSoft: '#F9F1E6',
  red: '#B5453A', redSoft: '#F4E4E1', purple: '#7B5BAC', purpleSoft: '#EEE6F5',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}
const STATUS_TK = {
  pending:        { color: TK.ink3,   bg: '#EFEAE2' },
  in_progress:    { color: TK.blue,   bg: TK.blueSoft },
  paused:         { color: TK.warn,   bg: TK.warnSoft },
  pending_review: { color: TK.purple, bg: TK.purpleSoft },
  completed:      { color: TK.green,  bg: TK.greenSoft },
  cancelled:      { color: TK.ink4,   bg: '#EFEAE2' },
}
const PRIORITY_TK = {
  urgent: { color: TK.red,  bg: TK.redSoft },
  high:   { color: TK.warn, bg: TK.warnSoft },
  normal: { color: TK.ink3, bg: '#EFEAE2' },
  low:    { color: TK.ink4, bg: '#F2EEE6' },
}
const _AVA = [TK.blue, TK.purple, TK.warn, TK.green, TK.red, TK.accent]
function stat(k) { return STATUS_TK[k] || STATUS_TK.pending }
function pri(k) { return PRIORITY_TK[k] || PRIORITY_TK.normal }
function chipStyle(p) {
  return { fontSize: '10px', color: p.color, background: p.bg, padding: '2px 7px',
    borderRadius: '4px', fontWeight: 600, letterSpacing: '0.3px', flexShrink: 0,
    lineHeight: 1.4, whiteSpace: 'nowrap' }
}
function avatarStyle(name, size) {
  let h = 0
  for (const c of (name || '?')) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return { width: size + 'px', height: size + 'px', borderRadius: (size / 2) + 'px',
    background: _AVA[h % _AVA.length], color: '#FFF', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: (size * 0.42) + 'px',
    fontWeight: 700, flexShrink: 0 }
}

const activeTab = ref('mine')
const statusF = ref('all')
const sort = ref('due_desc')
const loading = ref(false)
const items = ref([])
const counts = ref({ mine: 0, created: 0, shared: 0, review: 0, in_progress: 0, overdue: 0 })

const tabs = computed(() => [
  { k: 'mine',    l: t('task.tabMine'),    n: counts.value.mine },
  { k: 'created', l: t('task.tabCreated'), n: counts.value.created },
  { k: 'shared',  l: t('task.tabShared'),  n: counts.value.shared },
  { k: 'review',  l: t('task.tabReview'),  n: counts.value.review, alert: true },
])
const statusFilters = computed(() => [
  { k: 'all',            l: t('task.fAll') },
  { k: 'in_progress',    l: t('task.fInProgress') },
  { k: 'pending_review', l: t('task.fInReview') },
  { k: 'completed',      l: t('task.fCompleted') },
  { k: 'overdue',        l: t('task.fOverdue') },
])

async function load() {
  loading.value = true
  try {
    const r = await getTasks({ tab: activeTab.value, status: statusF.value, sort: sort.value })
    const d = r.data?.data || {}
    items.value = d.items || []
    if (d.counts) counts.value = d.counts
  } catch (e) {
    items.value = []
  } finally {
    loading.value = false
  }
}
function switchTab(k) { if (k !== activeTab.value) { activeTab.value = k; load() } }
function toggleSort() { sort.value = sort.value === 'due_desc' ? 'due_asc' : 'due_desc'; load() }
function onCreate() { /* P1 step 4: create-task screen, wired later */ }

import { watch } from 'vue'
watch(statusF, load)
onMounted(load)
</script>
