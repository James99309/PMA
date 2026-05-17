<!--
  DailyLogSubmitSheet - write & submit the daily log (C4).
  Single source = backend worklog_service via /mobile/worklog/day{,/submit}.
  Stats + auto summary come from the already-loaded day payload; user adds
  supplementary notes then submits. After submit the parent re-fetches the
  day → DailyLogCard flips to the submitted state (quality score / level /
  improvements, localized by the backend). All UI text via t().
  Scope per plan: stats + auto summary + notes + submit.
  (@mention / #project chips not in C4 scope — backend supports, FE later.)
-->
<template>
  <Teleport to="body">
    <transition name="dls">
      <div v-if="open" class="fixed inset-0 z-50"
        :style="{ background: CAL.bg, display: 'flex', flexDirection: 'column' }">
        <div class="status-pad" />
        <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 16px',
          borderBottom: `1px solid ${CAL.divider}`, flexShrink: 0 }">
          <span @click="close" class="active:opacity-60"
            :style="{ fontSize: '14px', color: CAL.ink3 }">{{ t('common.cancel') }}</span>
          <span :style="{ fontSize: '15px', fontWeight: 600, color: CAL.ink }">
            {{ t('calendar.writeLogTitle') }}</span>
          <span @click="submit" class="active:opacity-60"
            :style="{ fontSize: '14px', fontWeight: 600,
              color: saving ? CAL.ink4 : CAL.accent }">
            {{ saving ? t('calendar.submitting') : t('calendar.submit') }}</span>
        </div>

        <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '30px' }">
          <div :style="{ padding: '20px 20px 4px' }">
            <div :style="{ fontSize: '11px', color: CAL.ink3, letterSpacing: '0.6px',
              fontWeight: 600, textTransform: 'uppercase' }">{{ dateKicker }}</div>
            <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '23px',
              fontWeight: 600, marginTop: '4px', color: CAL.ink }">
              {{ t('calendar.logTitle', { d: dateShort }) }}</div>
          </div>

          <div :style="{ padding: '14px 16px', display: 'flex', gap: '10px' }">
            <div v-for="s in stats" :key="s.l" :style="{ flex: 1, padding: '10px 12px',
              background: CAL.card, borderRadius: '10px', border: `1px solid ${CAL.divider}` }">
              <div :style="{ fontSize: '10px', color: CAL.ink3, fontWeight: 600,
                letterSpacing: '0.4px' }">{{ s.l }}</div>
              <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '19px',
                fontWeight: 600, color: s.c, marginTop: '3px',
                fontVariantNumeric: 'tabular-nums' }">{{ s.v }}</div>
            </div>
          </div>

          <div :style="secWrap">{{ t('calendar.autoSummary') }}</div>
          <div :style="{ margin: '0 16px', padding: '12px 14px', background: CAL.blueSoft,
            borderRadius: '10px', border: '1px solid #DCE6F2', fontSize: '13px',
            color: CAL.ink, lineHeight: 1.65, whiteSpace: 'pre-wrap' }">
            {{ summary || t('calendar.summaryEmpty') }}</div>

          <div :style="secWrap">{{ t('calendar.supplementary') }}</div>
          <div :style="{ margin: '0 16px' }">
            <textarea v-model="notes" :placeholder="t('calendar.notesLogPh')"
              :style="{ width: '100%', boxSizing: 'border-box', minHeight: '100px',
                padding: '14px', background: CAL.card, borderRadius: '12px',
                border: `1.5px solid ${CAL.accent}`, fontSize: '13px', color: CAL.ink,
                lineHeight: 1.65, outline: 'none', resize: 'none' }" />
          </div>

          <div :style="{ margin: '20px 16px 0', padding: '11px 12px',
            background: CAL.warnSoft, borderRadius: '8px', fontSize: '12px',
            color: CAL.warn, lineHeight: 1.55 }">ⓘ {{ t('calendar.submitTip') }}</div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { updateWorklogDayDraft, submitWorklogDay } from '@/api/worklog'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  date: { type: String, default: '' },     // iso 'YYYY-MM-DD'
  day: { type: Object, default: null },    // already-loaded /mobile/worklog/day data
})
const emit = defineEmits(['update:modelValue', 'submitted'])

const CAL = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink3: '#7A7570',
  ink4: '#B5AEA3', divider: '#EBE6DD', accent: '#D97757', blue: '#3A6FB7',
  blueSoft: '#E5EBF4', purple: '#7B5BAC', warn: '#C77B22', warnSoft: '#F9F1E6',
}
const secWrap = { padding: '18px 20px 8px', fontSize: '11px', color: CAL.ink3,
  letterSpacing: '0.6px', fontWeight: 600, textTransform: 'uppercase' }
const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const saving = ref(false)
const notes = ref('')
let _seeded = ''

const locale = () => (localStorage.getItem('lang') === 'en' ? 'en-US' : 'zh-CN')
const _d = computed(() => props.date ? new Date(props.date + 'T00:00:00') : new Date())
const dateKicker = computed(() =>
  _d.value.toLocaleDateString(locale(), { weekday: 'long' }) + ' · ' + props.date)
const dateShort = computed(() =>
  _d.value.toLocaleDateString(locale(), { month: 'long', day: 'numeric' }))

const _st = computed(() => props.day?.statistics || {})
const _log = computed(() => props.day?.log || null)
const summary = computed(() => _log.value?.summary || '')
function _fmt(n) {
  const v = Number(n)
  return isFinite(v) ? v.toFixed(1).replace(/\.0$/, '') : '0'
}
const stats = computed(() => [
  { l: t('calendar.stItems'), v: _st.value.total_items || 0, c: CAL.ink },
  { l: t('calendar.stHours'), v: `${_fmt(_st.value.total_hours)} h`, c: CAL.blue },
  { l: t('calendar.lProject'), v: _st.value.project_count || 0, c: CAL.purple },
])

watch(() => props.modelValue, v => {
  if (v) {
    saving.value = false
    notes.value = _log.value?.additional_notes || ''
    _seeded = notes.value
  }
})

async function submit() {
  if (saving.value) return
  saving.value = true
  try {
    await submitWorklogDay(props.date, { additional_notes: notes.value.trim() })
    emit('submitted')
    open.value = false
  } catch (e) {
    window.alert(e.response?.data?.message || e.message)
  } finally {
    saving.value = false
  }
}
async function close() {
  // best-effort: persist edited notes as draft so they aren't lost
  if (!saving.value && notes.value.trim() !== _seeded.trim()) {
    try { await updateWorklogDayDraft(props.date, { additional_notes: notes.value.trim() }) }
    catch (e) { /* noop */ }
  }
  open.value = false
}
</script>

<style scoped>
.dls-enter-active, .dls-leave-active { transition: opacity .2s; }
.dls-enter-from, .dls-leave-to { opacity: 0; }
</style>
