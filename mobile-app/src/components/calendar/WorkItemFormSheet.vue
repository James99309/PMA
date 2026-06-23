<!--
  WorkItemFormSheet - create / edit a work item (C3).
  Single source = backend worklog_service via /mobile/worklog/items.
  Type picker uses backend meta.type_groups; project/customer reuse the shared
  ExSearchPickerSheet. All UI text via t(); type label/color from backend.
  Scope per plan: type/title/dates/times/hours/project/customer/biz-trip/
  all-day/notes. (attachments + share not in C3 scope.)
-->
<template>
  <Teleport to="body">
    <transition name="wfs">
      <div v-if="open" class="fixed inset-0 z-50"
        :style="{ background: CAL.bg, display: 'flex', flexDirection: 'column' }">
        <!-- header -->
        <div class="status-pad" />
        <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 16px',
          borderBottom: `1px solid ${CAL.divider}`, flexShrink: 0 }">
          <span @click="close" class="active:opacity-60"
            :style="{ fontSize: '14px', color: CAL.ink3 }">{{ t('common.cancel') }}</span>
          <span :style="{ fontSize: '15px', fontWeight: 600, color: CAL.ink }">
            {{ isEdit ? t('calendar.editItem') : t('calendar.newItem') }}</span>
          <span @click="submit" class="active:opacity-60"
            :style="{ fontSize: '14px', fontWeight: 600,
              color: canSave && !saving ? CAL.accent : CAL.ink4 }">
            {{ saving ? t('calendar.saving') : (isEdit ? t('common.save') : t('calendar.create')) }}</span>
        </div>

        <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '30px' }">
          <!-- type + title -->
          <div :style="{ padding: '18px 20px 4px' }">
            <div :style="secLabel">{{ t('calendar.fTypeTitle') }} <span :style="{ color: CAL.red }">*</span></div>
            <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px',
              background: CAL.card, borderRadius: '10px', border: `1px solid ${CAL.divider}` }">
              <span @click="typeSheet = true" class="active:opacity-70"
                :style="{ fontSize: '11px', color: typeMeta.color, background: typeMeta.color + '22',
                  padding: '3px 8px', borderRadius: '4px', fontWeight: 700, flexShrink: 0,
                  whiteSpace: 'nowrap' }">{{ typeMeta.label }} ▾</span>
              <input v-model="form.title" :placeholder="t('calendar.titlePh')"
                :style="{ flex: 1, minWidth: 0, border: 'none', outline: 'none',
                  background: 'transparent', fontSize: '14px', color: CAL.ink }" />
            </div>
          </div>

          <!-- dates -->
          <div :style="secWrap">{{ t('calendar.secDateTime') }}</div>
          <div :style="{ padding: '0 16px', display: 'grid',
            gridTemplateColumns: '1fr 1fr', gap: '12px' }">
            <div>
              <div :style="fieldLabel">{{ t('calendar.fStartDate') }} <span :style="{ color: CAL.red }">*</span></div>
              <input type="date" v-model="form.planned_date" :style="inp" />
            </div>
            <div>
              <div :style="fieldLabel">{{ t('calendar.fEndDate') }}
                <span :style="{ fontSize: '10px', color: CAL.ink4, fontWeight: 400 }">
                  {{ t('calendar.fEndDateHint') }}</span></div>
              <input type="date" v-model="form.end_date" :style="inp" />
            </div>
          </div>
          <div :style="{ padding: '12px 20px 0', display: 'flex', gap: '20px' }">
            <label :style="chk">
              <input type="checkbox" v-model="form.is_all_day" style="accent-color:#1A1A1A;" />
              {{ t('calendar.fAllDay') }}</label>
            <label :style="chk">
              <input type="checkbox" v-model="form.is_business_trip" style="accent-color:#1A1A1A;" />
              {{ t('calendar.fBizTrip') }}</label>
          </div>
          <div v-if="!form.is_all_day" :style="{ padding: '10px 16px 0', display: 'grid',
            gridTemplateColumns: '1fr 1fr', gap: '12px' }">
            <div>
              <div :style="fieldLabel">{{ t('calendar.fStartTime') }}</div>
              <input type="time" v-model="form.start_time" :style="inp" />
            </div>
            <div>
              <div :style="fieldLabel">{{ t('calendar.fEndTime') }}</div>
              <input type="time" v-model="form.end_time" :style="inp" />
            </div>
          </div>
          <div :style="{ padding: '14px 16px 0' }">
            <div :style="fieldLabel">{{ t('calendar.fHours') }}</div>
            <input type="number" step="0.5" min="0" inputmode="decimal"
              v-model="form.estimated_hours" :placeholder="t('calendar.fHoursPh')"
              :style="inp" />
          </div>

          <!-- links -->
          <div :style="secWrap">{{ t('calendar.secLinks') }}</div>
          <div :style="{ background: CAL.card, borderTop: `1px solid ${CAL.dividerSoft}`,
            borderBottom: `1px solid ${CAL.dividerSoft}` }">
            <div @click="projectSheet = true" class="active:opacity-60" :style="rowLink">
              <span :style="rowLab">{{ t('calendar.fProject') }}</span>
              <span :style="{ flex: 1, fontSize: '13.5px',
                color: form.project_name ? CAL.accent : CAL.ink4 }">
                {{ form.project_name || t('calendar.tapSelect') }}</span>
              <span v-if="form.project_id" @click.stop="clearProject"
                :style="{ color: CAL.ink4, fontSize: '12px', padding: '0 6px' }">✕</span>
              <span :style="{ color: CAL.ink4 }">›</span>
            </div>
            <div @click="customerSheet = true" class="active:opacity-60"
              :style="{ ...rowLink, borderBottom: 'none' }">
              <span :style="rowLab">{{ t('calendar.fCustomer') }}</span>
              <span :style="{ flex: 1, fontSize: '13.5px',
                color: form.customer_name ? CAL.accent : CAL.ink4 }">
                {{ form.customer_name || t('calendar.tapSelect') }}</span>
              <span v-if="form.customer_id" @click.stop="clearCustomer"
                :style="{ color: CAL.ink4, fontSize: '12px', padding: '0 6px' }">✕</span>
              <span :style="{ color: CAL.ink4 }">›</span>
            </div>
          </div>

          <!-- notes -->
          <div :style="secWrap">{{ t('calendar.secNotes') }}</div>
          <div :style="{ margin: '0 16px' }" @click="notesEditorOpen = true">
            <div v-if="form.description" class="rich-preview" v-html="rich(form.description)"
              :style="{ width: '100%', boxSizing: 'border-box', minHeight: '90px',
              maxHeight: '14em', padding: '14px', background: CAL.card, borderRadius: '12px',
              border: `1px solid ${CAL.divider}`, fontSize: '13px', lineHeight: 1.6,
              wordBreak: 'break-word', overflow: 'hidden', color: CAL.ink }"></div>
            <div v-else :style="{ width: '100%', boxSizing: 'border-box', minHeight: '90px',
              padding: '14px', background: CAL.card, borderRadius: '12px',
              border: `1px solid ${CAL.divider}`, fontSize: '13px', lineHeight: 1.6,
              color: CAL.ink4 }">{{ t('calendar.notesPh') }}</div>
          </div>
          <FullscreenTextEditor v-model="notesEditorOpen" :value="form.description || ''"
            :title="t('calendar.secNotes')" :placeholder="t('calendar.notesPh')"
            @save="v => { form.description = v }" />
        </div>

        <WorkItemTypePickerSheet v-model="typeSheet" :groups="groups"
          :selected="form.work_type" @pick="onPickType" />
        <ExSearchPickerSheet v-model="projectSheet" :title="t('calendar.fProject')"
          :placeholder="t('calendar.fProjectPh')" :search-fn="searchProjects"
          @pick="onPickProject" />
        <ExSearchPickerSheet v-model="customerSheet" :title="t('calendar.fCustomer')"
          :placeholder="t('calendar.fCustomerPh')" :search-fn="searchCustomers"
          @pick="onPickCustomer" />
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import client from '@/api/client'
import { createWorklogItem, updateWorklogItem } from '@/api/worklog'
import WorkItemTypePickerSheet from './WorkItemTypePickerSheet.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'
import FullscreenTextEditor from '@/components/common/FullscreenTextEditor.vue'
import { renderRich } from '@/utils/richNote'

const { t } = useI18n()
const rich = renderRich
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, default: null },        // edit target (null = create)
  defaultDate: { type: String, default: '' },   // create: prefilled planned_date
  groups: { type: Array, default: () => [] },   // backend meta.type_groups
})
const emit = defineEmits(['update:modelValue', 'saved'])

const CAL = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A',
  ink3: '#7A7570', ink4: '#B5AEA3', divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', red: '#B5453A',
}
const secLabel = { fontSize: '11px', color: CAL.ink3, fontWeight: 600,
  letterSpacing: '0.4px', textTransform: 'uppercase', marginBottom: '8px' }
const secWrap = { padding: '18px 20px 8px', fontSize: '11px', color: CAL.ink3,
  letterSpacing: '0.6px', fontWeight: 600, textTransform: 'uppercase' }
const fieldLabel = { fontSize: '11px', color: CAL.ink3, fontWeight: 600,
  marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.4px' }
const inp = { width: '100%', boxSizing: 'border-box', padding: '9px 12px',
  background: CAL.card, borderRadius: '8px', border: `1px solid ${CAL.divider}`,
  fontSize: '14px', color: CAL.ink, outline: 'none' }
const chk = { display: 'inline-flex', alignItems: 'center', gap: '7px',
  fontSize: '13px', color: CAL.ink2 }
const rowLink = { padding: '13px 20px', display: 'flex', alignItems: 'center',
  gap: '12px', borderBottom: `1px solid ${CAL.dividerSoft}` }
const rowLab = { width: '76px', fontSize: '12px', color: CAL.ink3, flexShrink: 0 }

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const isEdit = computed(() => !!(props.item && props.item.id))
const saving = ref(false)
const notesEditorOpen = ref(false)
const typeSheet = ref(false)
const projectSheet = ref(false)
const customerSheet = ref(false)

const form = reactive({
  work_type: 'other', title: '', planned_date: '', end_date: '',
  is_all_day: true, is_business_trip: false, start_time: '', end_time: '',
  estimated_hours: '', project_id: null, project_name: '',
  customer_id: null, customer_name: '', description: '',
})

const _flatTypes = computed(() => {
  const m = {}
  for (const g of props.groups) for (const o of (g.options || [])) m[o.value] = o
  return m
})
const typeMeta = computed(() => {
  const o = _flatTypes.value[form.work_type]
  if (o) return { label: o.label, color: o.color }
  // fallback: backend item label/color if editing an unlisted/legacy type
  return { label: props.item?.work_type_label || form.work_type || t('calendar.pickType'),
    color: props.item?.color || CAL.ink3 }
})
const canSave = computed(() => !!form.title.trim() && !!form.planned_date)

function _hm(t8) { return t8 ? String(t8).slice(0, 5) : '' }
function seed() {
  const it = props.item
  if (it && it.id) {
    form.work_type = it.work_type || 'other'
    form.title = it.title || ''
    form.planned_date = it.planned_date || ''
    form.end_date = it.end_date || ''
    form.is_all_day = it.is_all_day !== false
    form.is_business_trip = !!it.is_business_trip
    form.start_time = _hm(it.start_time)
    form.end_time = _hm(it.end_time)
    form.estimated_hours = it.estimated_hours != null ? it.estimated_hours : ''
    form.project_id = it.project_id || null
    form.project_name = it.project_name || ''
    form.customer_id = it.customer_id || null
    form.customer_name = it.customer_name || ''
    form.description = it.description || ''
  } else {
    form.work_type = 'other'
    form.title = ''
    form.planned_date = props.defaultDate || ''
    form.end_date = ''
    form.is_all_day = true
    form.is_business_trip = false
    form.start_time = ''
    form.end_time = ''
    form.estimated_hours = ''
    form.project_id = null
    form.project_name = ''
    form.customer_id = null
    form.customer_name = ''
    form.description = ''
  }
}
watch(() => props.modelValue, v => { if (v) { saving.value = false; seed() } })

function onPickType(v) { form.work_type = v }
async function searchProjects(q) {
  const r = await client.get('/mobile/projects', { params: { search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(p => ({
    id: p.id, label: p.name,
    sub: [p.stage_label, p.owner_name, p.city].filter(Boolean).join(' · '),
  }))
}
async function searchCustomers(q) {
  const r = await client.get('/mobile/customers', { params: { q: q || '', search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(c => ({
    id: c.id, label: c.name || c.company_name,
    sub: c.primary_contact_name || c.industry || '',
  }))
}
function onPickProject(it) { form.project_id = it.id; form.project_name = it.label }
function onPickCustomer(it) { form.customer_id = it.id; form.customer_name = it.label }
function clearProject() { form.project_id = null; form.project_name = '' }
function clearCustomer() { form.customer_id = null; form.customer_name = '' }

function _payload() {
  return {
    work_type: form.work_type,
    title: form.title.trim(),
    description: form.description.trim(),
    planned_date: form.planned_date,
    end_date: form.end_date || '',
    is_all_day: form.is_all_day,
    is_business_trip: form.is_business_trip,
    start_time: form.is_all_day ? '' : (form.start_time || ''),
    end_time: form.is_all_day ? '' : (form.end_time || ''),
    estimated_hours: form.estimated_hours === '' ? '' : form.estimated_hours,
    project_id: form.project_id || '',
    customer_id: form.customer_id || '',
  }
}
async function submit() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateWorklogItem(props.item.id, _payload())
    } else {
      await createWorklogItem(_payload())
    }
    emit('saved')
    open.value = false
  } catch (e) {
    window.alert(e.response?.data?.message || e.message)
  } finally {
    saving.value = false
  }
}
function close() { open.value = false }
</script>

<style scoped>
.wfs-enter-active, .wfs-leave-active { transition: opacity .2s; }
.wfs-enter-from, .wfs-leave-to { opacity: 0; }
.rich-preview { white-space: pre-wrap; }
.rich-preview :deep(img) { max-width: 100%; height: auto; display: block; border-radius: 8px; margin: 4px 0; }
.rich-preview :deep(.arn-img) { display: inline-block; max-width: 100%; }
</style>
