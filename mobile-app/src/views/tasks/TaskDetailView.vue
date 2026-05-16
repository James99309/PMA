<!--
  TaskDetailView - Task detail (P1 step 4)
  Pixel port of Claude Design "PMA Task EN" task-detail-en.jsx + quick-status
  / review sheets from task-forms-en.jsx. status/priority text from backend
  *_label; other UI text via t() (i18n rule). Local TK = design task-base.
-->
<template>
  <div :style="{ background: TK.bg, height: '100%', fontFamily: TK.sans, color: TK.ink,
    display: 'flex', flexDirection: 'column' }">
    <div class="status-pad" />
    <!-- nav -->
    <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 12px', flexShrink: 0,
      borderBottom: `1px solid ${TK.divider}` }">
      <button @click="router.back()" class="active:opacity-60"
        :style="{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'none',
          border: 'none', color: TK.ink2, fontSize: '14px', padding: 0 }">
        <span :style="{ fontSize: '22px', lineHeight: 1, fontWeight: 300 }">‹</span>
        <span>{{ t('task.navTasks') }}</span>
      </button>
      <span :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('task.detailTitle') }}</span>
      <span :style="{ minWidth: '40px', textAlign: 'right', fontSize: '13px',
        color: TK.accent, fontWeight: 600 }">{{ d?.can_edit ? t('common.edit') : '' }}</span>
    </div>

    <div v-if="loading" :style="{ flex: 1, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: TK.ink4 }">···</div>

    <div v-else-if="d" :style="{ flex: 1, overflowY: 'auto', paddingBottom: '92px' }">
      <div :style="{ padding: '14px 20px 18px' }">
        <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }">
          <span :style="chip(pri(d.priority), 'md')">{{ d.priority_label }}</span>
          <span :style="chip(stat(d.status), 'md')">{{ d.status_label }}</span>
          <span v-if="d.overdue" :style="{ fontSize: '10px', color: TK.red, fontWeight: 700,
            background: TK.redSoft, padding: '3px 7px', borderRadius: '4px' }">{{ t('task.overdue') }}</span>
        </div>
        <h1 :style="{ margin: 0, fontFamily: 'var(--font-serif)', fontSize: '24px',
          fontWeight: 600, color: TK.ink, lineHeight: 1.25 }">{{ d.title }}</h1>
        <div :style="{ fontSize: '12px', color: TK.ink3, marginTop: '6px' }">
          {{ taskCode }} · {{ t('task.metaCreated') }} {{ fmt(d.created_at) }} · {{ t('task.metaUpdated') }} {{ fmt(d.updated_at) }}
        </div>
      </div>

      <!-- 2x2 meta -->
      <div :style="{ margin: '0 16px 12px', background: TK.card, borderRadius: '12px',
        border: `1px solid ${TK.divider}`, padding: '12px 0', display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)' }">
        <div v-for="(m, i) in metaCells" :key="i" :style="{ padding: '6px 16px',
          borderRight: i % 2 === 0 ? `1px solid ${TK.dividerSoft}` : 'none',
          borderTop: i > 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <div :style="{ fontSize: '10.5px', color: TK.ink3, letterSpacing: '0.4px',
            textTransform: 'uppercase' }">{{ m.l }}</div>
          <div :style="{ fontSize: '14px', fontWeight: 600, marginTop: '3px',
            color: m.accent ? TK.red : TK.ink }">{{ m.v || '—' }}</div>
        </div>
      </div>

      <!-- description -->
      <div :style="secTitle">{{ t('task.secDescription') }}</div>
      <div :style="{ background: TK.card, padding: '14px 20px', fontSize: '13.5px',
        color: TK.ink2, lineHeight: 1.65, borderTop: `1px solid ${TK.dividerSoft}`,
        borderBottom: `1px solid ${TK.dividerSoft}` }">
        {{ d.description || t('task.noDescription') }}
      </div>

      <!-- links -->
      <div :style="secTitle">{{ t('task.secLinks') }}</div>
      <div :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}`,
        borderBottom: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(lk, i) in linkRows" :key="lk.l" :style="{ padding: '12px 20px',
          display: 'flex', gap: '14px', borderBottom: i < linkRows.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <div :style="{ width: '86px', fontSize: '12px', color: TK.ink3, flexShrink: 0 }">{{ lk.l }}</div>
          <div :style="{ flex: 1, fontSize: '13.5px' }">
            <span v-if="lk.v" :style="{ color: TK.accent, fontWeight: 500 }">{{ lk.v }}</span>
            <span v-else :style="{ color: TK.ink4 }">{{ t('task.notLinked') }}</span>
          </div>
        </div>
      </div>

      <!-- reviewers -->
      <template v-if="d.reviewers && d.reviewers.length">
        <div :style="secTitle">{{ t('task.secReviewers') }}</div>
        <div :style="{ background: TK.card, borderTop: `1px solid ${TK.dividerSoft}`,
          borderBottom: `1px solid ${TK.dividerSoft}` }">
          <div v-for="(rv, i) in d.reviewers" :key="i" :style="{ padding: '12px 20px',
            display: 'flex', alignItems: 'center', gap: '12px',
            borderBottom: i < d.reviewers.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
            <span :style="ava(rv.reviewer_name || rv.name, 32)">{{ shortOf(rv.reviewer_name || rv.name) }}</span>
            <div :style="{ flex: 1, fontSize: '13.5px', fontWeight: 600 }">{{ rv.reviewer_name || rv.name }}</div>
            <span :style="{ fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px',
              color: rvTone(rv.status).color, background: rvTone(rv.status).bg }">{{ rvLabel(rv.status) }}</span>
          </div>
        </div>
      </template>

      <!-- subtasks -->
      <div :style="secTitle">{{ t('task.secSubtasks', { done: subDone, total: (d.subtasks || []).length }) }}</div>
      <div v-if="(d.subtasks || []).length" :style="{ background: TK.card,
        borderTop: `1px solid ${TK.dividerSoft}`, borderBottom: `1px solid ${TK.dividerSoft}` }">
        <div v-for="(s, i) in d.subtasks" :key="s.id" :style="{ padding: '12px 20px',
          display: 'flex', alignItems: 'flex-start', gap: '12px',
          borderBottom: i < d.subtasks.length - 1 ? `1px solid ${TK.dividerSoft}` : 'none' }">
          <span :style="{ width: '20px', height: '20px', flexShrink: 0, marginTop: '1px',
            borderRadius: s.is_milestone ? '4px' : '10px', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            border: `1.5px solid ${s.status === 'completed' ? TK.green : (s.is_milestone ? TK.purple : TK.divider)}`,
            background: s.status === 'completed' ? TK.green : 'transparent', color: '#fff', fontSize: '11px' }">
            <span v-if="s.status === 'completed'">✓</span>
          </span>
          <div :style="{ flex: 1, minWidth: 0 }">
            <div :style="{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }">
              <span :style="{ fontSize: '13.5px', fontWeight: 600,
                textDecoration: s.status === 'completed' ? 'line-through' : 'none',
                opacity: s.status === 'completed' ? 0.55 : 1 }">{{ s.title }}</span>
              <span v-if="s.is_milestone" :style="{ fontSize: '9.5px', color: TK.purple,
                background: TK.purpleSoft, padding: '1px 5px', borderRadius: '3px',
                fontWeight: 700, letterSpacing: '0.4px', textTransform: 'uppercase' }">{{ t('task.milestone') }}</span>
            </div>
            <div :style="{ fontSize: '11px', color: TK.ink3, marginTop: '4px' }">
              {{ s.owner_name }} · {{ s.start }} – {{ s.due }}
              <template v-if="s.progress_notes > 0"> · <span :style="{ color: TK.blue, fontWeight: 600 }">{{ t('task.subUpdates', { n: s.progress_notes }) }}</span></template>
            </div>
          </div>
        </div>
      </div>

      <!-- activity timeline -->
      <div :style="secTitle">{{ t('task.secActivity', { n: commentCount }) }}</div>
      <div :style="{ padding: '0 20px 12px' }">
        <template v-for="(r, i) in (d.timeline || [])" :key="i">
          <div v-if="r.kind === 'system'" :style="{ padding: '8px 0 8px 30px', position: 'relative',
            fontSize: '11px', color: TK.ink3, fontStyle: 'italic', fontFamily: 'var(--font-serif)' }">
            <span :style="{ position: 'absolute', left: '11px', top: '12px', width: '7px',
              height: '7px', borderRadius: '3.5px', background: TK.divider }" />
            {{ r.text }} <span :style="{ color: TK.ink4, fontStyle: 'normal', marginLeft: '6px' }">{{ r.at }}</span>
          </div>
          <div v-else-if="r.kind === 'progress'" :style="{ margin: '4px 0 10px', paddingLeft: '30px' }">
            <div :style="{ background: TK.blueSoft, borderRadius: '8px', padding: '8px 12px',
              border: '1px solid #DCE6F2' }">
              <div :style="{ fontSize: '10px', color: '#1A4A8C', fontWeight: 600,
                letterSpacing: '0.4px', marginBottom: '3px', textTransform: 'uppercase' }">
                {{ t('task.tlUpdate') }}<template v-if="r.sub"> · {{ r.sub }}</template></div>
              <div :style="{ fontSize: '12.5px', color: TK.ink, lineHeight: 1.5 }">{{ r.text }}</div>
              <div :style="{ fontSize: '10px', color: TK.ink3, marginTop: '4px' }">{{ r.author }} · {{ r.at }}</div>
            </div>
          </div>
          <div v-else :style="{ display: 'flex', gap: '10px', padding: '10px 0' }">
            <span :style="ava(r.author, 24)">{{ r.author_short }}</span>
            <div :style="{ flex: 1, minWidth: 0 }">
              <div :style="{ fontSize: '12px', color: TK.ink2, marginBottom: '3px' }">
                <strong :style="{ fontWeight: 600 }">{{ r.author }}</strong>
                <span :style="{ color: TK.ink4, marginLeft: '6px' }">{{ r.at }}</span>
              </div>
              <div :style="{ fontSize: '13.5px', color: TK.ink, lineHeight: 1.55 }">{{ r.text }}</div>
            </div>
          </div>
        </template>
        <div v-if="!(d.timeline || []).length" :style="{ padding: '20px 0', textAlign: 'center',
          fontSize: '12px', color: TK.ink4 }">{{ t('task.noActivity') }}</div>
      </div>
    </div>

    <!-- bottom bar -->
    <div v-if="d" :style="{ position: 'absolute', bottom: 0, left: 0, right: 0,
      padding: '10px 12px calc(22px + env(safe-area-inset-bottom))', background: TK.card,
      borderTop: `1px solid ${TK.divider}`, display: 'flex', gap: '8px', alignItems: 'center' }">
      <template v-if="d.can_review">
        <button @click="openReview('reject')" :style="{ flex: 1, height: '44px', borderRadius: '22px',
          background: TK.card, color: TK.red, border: `1.5px solid ${TK.red}`, fontSize: '14px',
          fontWeight: 600 }">{{ t('task.reject') }}</button>
        <button @click="openReview('approve')" :style="{ flex: 2, height: '44px', borderRadius: '22px',
          background: TK.green, color: '#fff', border: 'none', fontSize: '14px', fontWeight: 600 }">{{ t('task.approve') }}</button>
      </template>
      <template v-else>
        <input v-model="commentText" :placeholder="t('task.addComment')"
          @keyup.enter="sendComment"
          :style="{ flex: 1, height: '40px', borderRadius: '20px', background: TK.bg,
            padding: '0 14px', fontSize: '13px', color: TK.ink, outline: 'none',
            border: `1px solid ${TK.dividerSoft}` }" />
        <button @click="commentText.trim() ? sendComment() : (statusSheet = true)"
          :style="{ height: '40px', padding: '0 14px', borderRadius: '20px', background: TK.ink,
            color: '#fff', border: 'none', display: 'flex', alignItems: 'center', gap: '6px',
            fontSize: '13px', fontWeight: 600 }">
          <span v-if="commentText.trim()">{{ t('task.send') }}</span>
          <template v-else>
            <span :style="{ width: '6px', height: '6px', borderRadius: '3px',
              background: stat(d.status).color }" />
            {{ d.status_label }} <span :style="{ fontSize: '10px', opacity: 0.7 }">›</span>
          </template>
        </button>
      </template>
    </div>

    <!-- Quick status sheet -->
    <Teleport to="body">
      <div v-if="statusSheet" :style="ovl" @click.self="statusSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ padding: '0 4px 4px' }">
            <div :style="{ fontSize: '11px', color: TK.ink3, letterSpacing: '0.6px',
              fontWeight: 600, textTransform: 'uppercase' }">{{ t('task.changeStatus') }}</div>
            <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontWeight: 600, marginTop: '4px' }">
              {{ t('task.currently') }} · <span :style="{ color: stat(d.status).color }">{{ d.status_label }}</span>
            </div>
          </div>
          <div :style="{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }">
            <div v-for="op in statusOptions" :key="op.to" @click="doStatus(op)"
              :style="{ padding: '14px', background: TK.card, borderRadius: '12px',
                border: op.primary ? `1.5px solid ${TK.green}` : `1px solid ${TK.divider}`,
                display: 'flex', alignItems: 'center', gap: '14px',
                boxShadow: op.primary ? `0 0 0 3px ${TK.greenSoft}` : 'none' }">
              <div :style="{ width: '32px', height: '32px', borderRadius: '10px',
                background: op.primary ? op.tone : TK.bg, color: op.primary ? '#fff' : op.tone,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }">{{ op.icon }}</div>
              <div :style="{ flex: 1 }">
                <div :style="{ fontSize: '14px', fontWeight: 600, color: op.tone }">{{ op.l }}</div>
                <div v-if="op.sub" :style="{ fontSize: '11px', color: TK.ink3, marginTop: '2px' }">{{ op.sub }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Review approve/reject sheet -->
    <Teleport to="body">
      <div v-if="reviewSheet" :style="ovl" @click.self="reviewSheet = false">
        <div :style="sheet">
          <div :style="grab" />
          <div :style="{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.6px',
            textTransform: 'uppercase', color: reviewAction === 'approve' ? TK.green : TK.red }">
            {{ reviewAction === 'approve' ? t('task.approve') : t('task.reject') }}
          </div>
          <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 600, marginTop: '4px' }">
            {{ reviewAction === 'approve' ? t('task.approveTitle') : t('task.rejectTitle') }}
          </div>
          <div :style="{ marginTop: '14px', padding: '12px 14px', background: TK.card,
            borderRadius: '10px', border: `1px solid ${TK.divider}` }">
            <div :style="{ fontSize: '11px', color: TK.ink3, marginBottom: '6px',
              textTransform: 'uppercase', letterSpacing: '0.4px' }">
              {{ t('task.note') }}<span v-if="reviewAction === 'reject'" :style="{ color: TK.red }"> *</span>
            </div>
            <textarea v-model="reviewComment" rows="3"
              :placeholder="reviewAction === 'reject' ? t('task.notePhReject') : t('task.notePhApprove')"
              :style="{ width: '100%', border: 'none', outline: 'none', resize: 'none',
                fontSize: '13px', color: TK.ink, background: 'transparent', fontFamily: TK.sans }" />
          </div>
          <div :style="{ display: 'flex', gap: '10px', marginTop: '18px' }">
            <button @click="reviewSheet = false" :style="{ flex: 1, height: '46px',
              borderRadius: '23px', background: TK.card, border: `1.5px solid ${TK.divider}`,
              color: TK.ink2, fontSize: '14px', fontWeight: 600 }">{{ t('common.cancel') }}</button>
            <button @click="doReview" :style="{ flex: 2, height: '46px', borderRadius: '23px',
              background: reviewAction === 'approve' ? TK.green : TK.red, color: '#fff',
              border: 'none', fontSize: '14px', fontWeight: 600 }">
              {{ reviewAction === 'approve' ? t('task.confirmApprove') : t('task.confirmReject') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getTask, changeTaskStatus, addTaskReply, reviewTask } from '@/api/tasks'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const TK = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', accentSoft: '#FAEEE5', blue: '#3A6FB7', blueSoft: '#E5EBF4',
  green: '#2F7A4F', greenSoft: '#E9F1EB', warn: '#C77B22', warnSoft: '#F9F1E6',
  red: '#B5453A', redSoft: '#F4E4E1', purple: '#7B5BAC', purpleSoft: '#EEE6F5',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}
const STATUS_TK = {
  pending: { color: TK.ink3, bg: '#EFEAE2' }, in_progress: { color: TK.blue, bg: TK.blueSoft },
  paused: { color: TK.warn, bg: TK.warnSoft }, pending_review: { color: TK.purple, bg: TK.purpleSoft },
  completed: { color: TK.green, bg: TK.greenSoft }, cancelled: { color: TK.ink4, bg: '#EFEAE2' },
}
const PRIORITY_TK = {
  urgent: { color: TK.red, bg: TK.redSoft }, high: { color: TK.warn, bg: TK.warnSoft },
  normal: { color: TK.ink3, bg: '#EFEAE2' }, low: { color: TK.ink4, bg: '#F2EEE6' },
}
const _AVA = [TK.blue, TK.purple, TK.warn, TK.green, TK.red, TK.accent]
function stat(k) { return STATUS_TK[k] || STATUS_TK.pending }
function pri(k) { return PRIORITY_TK[k] || PRIORITY_TK.normal }
function chip(p, sz) {
  return { fontSize: sz === 'md' ? '11px' : '10px', color: p.color, background: p.bg,
    padding: sz === 'md' ? '3px 9px' : '2px 7px', borderRadius: '4px', fontWeight: 600,
    letterSpacing: '0.3px', whiteSpace: 'nowrap' }
}
function shortOf(name) {
  if (!name) return '?'
  const n = name.trim()
  if (/^[\x00-\x7F]/.test(n)) return n.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase()
  return n.slice(-1)
}
function ava(name, size) {
  let h = 0; for (const c of (name || '?')) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return { width: size + 'px', height: size + 'px', borderRadius: (size / 2) + 'px',
    background: _AVA[h % _AVA.length], color: '#fff', display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center', fontSize: (size * 0.4) + 'px',
    fontWeight: 700, flexShrink: 0 }
}
const secTitle = { padding: '20px 20px 10px', fontSize: '11px', color: TK.ink3,
  letterSpacing: '0.6px', fontWeight: 600, textTransform: 'uppercase' }
const ovl = { position: 'fixed', inset: 0, background: 'rgba(26,26,26,.42)', zIndex: 60 }
const sheet = { position: 'absolute', left: 0, right: 0, bottom: 0, background: TK.bg,
  borderRadius: '20px 20px 0 0', padding: '14px 16px calc(26px + env(safe-area-inset-bottom))',
  boxShadow: '0 -10px 30px rgba(0,0,0,.18)', maxHeight: '86%', overflowY: 'auto' }
const grab = { width: '36px', height: '4px', background: TK.divider, borderRadius: '2px', margin: '0 auto 14px' }

const id = computed(() => route.params.id)
const d = ref(null)
const loading = ref(true)
const commentText = ref('')
const statusSheet = ref(false)
const reviewSheet = ref(false)
const reviewAction = ref('approve')
const reviewComment = ref('')

const taskCode = computed(() => 'T-' + String(d.value?.id || '').padStart(4, '0'))
function fmt(iso) {
  if (!iso) return '—'
  const dt = new Date(iso)
  return `${dt.getMonth() + 1}/${dt.getDate()} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}
function fmtDate(iso) {
  if (!iso) return null
  const dt = new Date(iso)
  return `${dt.getMonth() + 1}/${dt.getDate()}`
}
const metaCells = computed(() => d.value ? [
  { l: t('task.mAssignee'), v: d.value.assignee_name },
  { l: t('task.mCreator'), v: d.value.creator_name },
  { l: t('task.mStart'), v: fmtDate(d.value.start_date) },
  { l: t('task.mDue'), v: fmtDate(d.value.due_date), accent: d.value.overdue },
] : [])
const linkRows = computed(() => d.value ? [
  { l: t('task.lProject'), v: d.value.project_name },
  { l: t('task.lCustomer'), v: d.value.customer_name },
  { l: t('task.lQuotation'), v: d.value.quotation_number },
] : [])
const subDone = computed(() => (d.value?.subtasks || []).filter(s => s.status === 'completed').length)
const commentCount = computed(() => (d.value?.timeline || []).filter(r => r.kind !== 'system').length)

function rvTone(s) {
  if (s === 'approved') return { color: TK.green, bg: TK.greenSoft }
  if (s === 'rejected') return { color: TK.red, bg: TK.redSoft }
  return { color: TK.warn, bg: TK.warnSoft }
}
function rvLabel(s) {
  return s === 'approved' ? t('task.rvApproved') : s === 'rejected' ? t('task.rvRejected') : t('task.rvPending')
}

const statusOptions = computed(() => [
  { to: 'pending', icon: '◯', tone: TK.ink3, l: t('task.stBackTodo') },
  { to: 'paused', icon: '⏸', tone: TK.warn, l: t('task.stPause'), sub: t('task.stPauseSub'), needReason: true },
  { to: 'pending_review', icon: '↗', tone: TK.purple, l: t('task.stSubmitReview'), sub: t('task.stSubmitReviewSub') },
  { to: 'completed', icon: '✓', tone: TK.green, l: t('task.stComplete'), primary: true },
  { to: 'cancelled', icon: '✕', tone: TK.red, l: t('task.stCancel'), sub: t('task.stCancelSub') },
])

async function load() {
  loading.value = true
  try {
    const r = await getTask(id.value)
    d.value = r.data?.data || null
  } finally {
    loading.value = false
  }
}
async function sendComment() {
  const c = commentText.value.trim()
  if (!c) return
  try {
    const r = await addTaskReply(id.value, c)
    if (r.data?.data?.timeline) d.value.timeline = r.data.data.timeline
    commentText.value = ''
  } catch (e) { /* keep text on failure */ }
}
async function doStatus(op) {
  let reason = ''
  if (op.needReason) {
    reason = (window.prompt(t('task.pausePrompt')) || '').trim()
    if (!reason) return
  }
  try {
    await changeTaskStatus(id.value, { to: op.to, reason })
    statusSheet.value = false
    await load()
  } catch (e) { /* noop */ }
}
function openReview(a) { reviewAction.value = a; reviewComment.value = ''; reviewSheet.value = true }
async function doReview() {
  if (reviewAction.value === 'reject' && !reviewComment.value.trim()) return
  try {
    await reviewTask(id.value, { action: reviewAction.value, comment: reviewComment.value.trim() })
    reviewSheet.value = false
    await load()
  } catch (e) { /* noop */ }
}

onMounted(load)
</script>
