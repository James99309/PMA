<!--
  WorkItemDetailSheet - tap a work item → detail + actions (C3, solves UAT #2).
  Actions call backend worklog_service via /mobile/worklog (single source).
  readonly (viewing a colleague / not owner) → no actions. UI text via t();
  type label/color from backend.
-->
<template>
  <Teleport to="body">
    <transition name="wds">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(20,20,20,0.42);" @click.self="close">
        <div class="mt-auto flex flex-col"
          :style="{ background: CAL.bg, borderRadius: '20px 20px 0 0',
            padding: '14px 0 22px', maxHeight: '85vh' }">
          <div class="flex justify-center" style="padding-bottom: 12px;">
            <div style="width: 36px; height: 4px; background: #D8D2C6; border-radius: 2px;" />
          </div>

          <div v-if="it" :style="{ padding: '0 20px 12px' }">
            <div :style="{ display: 'flex', alignItems: 'center', gap: '8px',
              marginBottom: '8px' }">
              <span :style="{ fontFamily: 'var(--font-serif)', fontSize: '20px',
                fontWeight: 600, color: CAL.ink }">{{ t('calendar.itemDetail') }}</span>
              <span :style="{ fontSize: '10px', padding: '2px 7px', borderRadius: '4px',
                fontWeight: 700, ...statusBadge }">{{ statusText }}</span>
            </div>
            <span :style="{ display: 'inline-block', fontSize: '11px', color: it.color || CAL.ink3,
              background: (it.color || CAL.ink3) + '22', padding: '2px 7px',
              borderRadius: '3px', fontWeight: 700, marginBottom: '6px' }">
              {{ it.work_type_label }}</span>
            <div :style="{ fontFamily: 'var(--font-serif)', fontSize: '21px', fontWeight: 600,
              lineHeight: 1.3, color: CAL.ink }">{{ it.title }}</div>
          </div>

          <div v-if="it" class="overflow-y-auto" style="padding: 0 16px;">
            <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px',
              marginBottom: '12px' }">
              <div :style="meta"><div :style="metaLab">{{ t('calendar.mDate') }}</div>
                <div :style="metaVal(CAL.ink)">{{ it.planned_date }}{{ it.end_date && it.end_date !== it.planned_date ? ' → ' + it.end_date : '' }}</div></div>
              <div :style="meta"><div :style="metaLab">{{ t('calendar.mTime') }}</div>
                <div :style="metaVal(CAL.ink)">{{ timeText }}</div></div>
              <div :style="meta"><div :style="metaLab">{{ t('calendar.mHours') }}</div>
                <div :style="metaVal(CAL.blue)">{{ hoursText }}</div></div>
              <div :style="meta"><div :style="metaLab">{{ t('calendar.mStatus') }}</div>
                <div :style="metaVal(statusBadge.color)">{{ statusText }}</div></div>
            </div>

            <template v-if="it.project_name || it.customer_name">
              <div :style="secLab">{{ t('calendar.secLinks') }}</div>
              <div :style="{ background: CAL.card, borderRadius: '10px',
                border: `1px solid ${CAL.divider}`, padding: '10px 14px',
                marginBottom: '12px' }">
                <div v-if="it.project_name" :style="{ display: 'flex',
                  justifyContent: 'space-between', fontSize: '13px',
                  paddingBottom: it.customer_name ? '6px' : '0',
                  borderBottom: it.customer_name ? `1px solid ${CAL.dividerSoft}` : 'none',
                  marginBottom: it.customer_name ? '6px' : '0' }">
                  <span :style="{ color: CAL.ink3 }">{{ t('calendar.lProject') }}</span>
                  <span :style="{ color: CAL.accent, fontWeight: 500 }">#{{ it.project_name }}</span>
                </div>
                <div v-if="it.customer_name" :style="{ display: 'flex',
                  justifyContent: 'space-between', fontSize: '13px' }">
                  <span :style="{ color: CAL.ink3 }">{{ t('calendar.lCustomer') }}</span>
                  <span :style="{ color: CAL.accent, fontWeight: 500 }">{{ it.customer_name }}</span>
                </div>
              </div>
            </template>

            <template v-if="it.description || it.execution_notes">
              <div :style="secLab">{{ t('calendar.secNotes') }}</div>
              <div :style="{ background: CAL.card, borderRadius: '10px',
                border: `1px solid ${CAL.divider}`, padding: '12px 14px',
                fontSize: '13px', color: CAL.ink2, lineHeight: 1.65,
                whiteSpace: 'pre-wrap' }">{{ it.description || '' }}<template
                v-if="it.execution_notes">{{ it.description ? '\n\n' : '' }}{{ it.execution_notes }}</template></div>
            </template>
            <div style="height: 14px;" />
          </div>

          <div v-if="it && !readonly" :style="{ padding: '14px 16px 0',
            borderTop: `1px solid ${CAL.divider}`, display: 'flex', gap: '10px',
            flexShrink: 0, flexWrap: 'wrap' }">
            <button @click="onEdit" :disabled="busy" class="active:opacity-70"
              :style="btn(false)">{{ t('common.edit') }}</button>
            <button v-if="it.status === 'planned'" @click="onComplete" :disabled="busy"
              class="active:opacity-70" :style="btnPrimary">{{ t('calendar.aComplete') }}</button>
            <button v-if="it.status === 'planned'" @click="onCancel" :disabled="busy"
              class="active:opacity-70" :style="btn(false)">{{ t('calendar.aCancel') }}</button>
            <button @click="onDelete" :disabled="busy" class="active:opacity-70"
              :style="btn(true)">{{ t('common.delete') }}</button>
          </div>
          <div v-if="it && readonly" :style="{ padding: '12px 20px 0', textAlign: 'center',
            fontSize: '12px', color: CAL.ink4 }">{{ t('calendar.readonlyHint') }}</div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { completeWorklogItem, cancelWorklogItem, deleteWorklogItem } from '@/api/worklog'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, default: null },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'edit', 'changed'])

const CAL = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', blue: '#3A6FB7', green: '#2F7A4F', greenSoft: '#E9F1EB',
  blueSoft: '#E5EBF4', red: '#B5453A', ink4Soft: '#EFEAE2',
}
const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const it = computed(() => props.item)
const busy = ref(false)

const meta = { padding: '10px 12px', background: CAL.card, borderRadius: '10px',
  border: `1px solid ${CAL.divider}` }
const metaLab = { fontSize: '10px', color: CAL.ink3, fontWeight: 600, letterSpacing: '0.4px' }
function metaVal(c) {
  return { fontFamily: 'var(--font-serif)', fontSize: '15px', fontWeight: 600,
    color: c, marginTop: '3px', fontVariantNumeric: 'tabular-nums' }
}
const secLab = { fontSize: '11px', color: CAL.ink3, letterSpacing: '0.6px',
  fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px' }

const statusBadge = computed(() => {
  const s = it.value?.status
  if (s === 'completed') return { color: CAL.green, background: CAL.greenSoft }
  if (s === 'cancelled') return { color: CAL.ink4, background: CAL.ink4Soft }
  return { color: CAL.blue, background: CAL.blueSoft }
})
const statusText = computed(() => {
  const s = it.value?.status
  if (s === 'completed') return t('calendar.stCompleted')
  if (s === 'cancelled') return t('calendar.stCancelled')
  return t('calendar.stPlanned')
})
function _hm(x) { return x ? String(x).slice(0, 5) : '' }
const timeText = computed(() => {
  const i = it.value
  if (!i) return '—'
  if (i.is_all_day) return t('calendar.allDay')
  const s = _hm(i.start_time), e = _hm(i.end_time)
  return s ? (e ? `${s} – ${e}` : s) : '—'
})
const hoursText = computed(() => {
  const i = it.value
  if (!i) return '—'
  const h = i.actual_hours != null ? i.actual_hours : i.estimated_hours
  return h != null ? `${Number(h)}h` : '—'
})

function btn(danger) {
  return { flex: 1, minWidth: '78px', height: '44px', borderRadius: '22px',
    background: CAL.card, border: `1.5px solid ${danger ? CAL.red : CAL.divider}`,
    color: danger ? CAL.red : CAL.ink2, fontSize: '13.5px', fontWeight: 600 }
}
const btnPrimary = { flex: 1.4, minWidth: '90px', height: '44px', borderRadius: '22px',
  background: CAL.green, border: 'none', color: '#FFF', fontSize: '13.5px', fontWeight: 600 }

function close() { open.value = false }
function onEdit() {
  emit('edit', it.value)
  close()
}
async function _act(fn, confirmMsg) {
  if (busy.value || !it.value) return
  if (confirmMsg && !window.confirm(confirmMsg)) return
  busy.value = true
  try {
    await fn(it.value.id)
    emit('changed')
    close()
  } catch (e) {
    window.alert(e.response?.data?.message || e.message)
  } finally {
    busy.value = false
  }
}
function onComplete() { _act(id => completeWorklogItem(id, {})) }
function onCancel() {
  _act(id => cancelWorklogItem(id, {}), t('calendar.confirmCancel'))
}
function onDelete() {
  _act(deleteWorklogItem, t('calendar.confirmDelete', { title: it.value?.title || '' }))
}
</script>

<style scoped>
.wds-enter-active, .wds-leave-active { transition: opacity .2s; }
.wds-enter-from, .wds-leave-to { opacity: 0; }
</style>
