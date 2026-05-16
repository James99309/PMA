<!--
  TaskFormFields - shared task form body (create + edit, P2)
  Operates on a reactive `form` object passed by parent. All UI text via t().
  Reuses PersonPickerSheet (assignee), PickerSheet (priority),
  ExSearchPickerSheet (project/customer), MultiPersonPickerSheet (reviewers/shared).
-->
<template>
  <div>
    <!-- title -->
    <div :style="{ padding: '20px 20px 4px' }">
      <div :style="lab">{{ t('task.fTitle') }} <span :style="{ color: TK.red }">*</span></div>
      <input v-model="form.title" :placeholder="t('task.fTitlePh')"
        :style="{ width: '100%', border: 'none', outline: 'none', background: 'transparent',
          fontSize: '22px', fontWeight: 600, fontFamily: 'var(--font-serif)',
          color: TK.ink, lineHeight: 1.3 }" />
      <div :style="{ height: '1px', background: TK.divider, marginTop: '10px' }" />
    </div>

    <!-- assignee + priority -->
    <div :style="{ padding: '14px 20px', display: 'flex', gap: '14px' }">
      <div :style="{ flex: 1 }">
        <div :style="lab">{{ t('task.fAssignee') }} <span :style="{ color: TK.red }">*</span></div>
        <div @click="assigneeSheet = true" :style="fieldBox">
          <span v-if="assigneeName" :style="{ fontSize: '13px', fontWeight: 500 }">{{ assigneeName }}</span>
          <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fAssigneePh') }}</span>
          <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
      <div :style="{ width: '130px' }">
        <div :style="lab">{{ t('task.fPriority') }}</div>
        <div @click="prioritySheet = true" :style="{ ...fieldBox,
          background: form.priority === 'urgent' || form.priority === 'high' ? TK.warnSoft : TK.card,
          border: `1px solid ${form.priority === 'urgent' || form.priority === 'high' ? TK.warn : TK.divider}` }">
          <span :style="{ width: '6px', height: '6px', borderRadius: '3px', background: priColor }" />
          <span :style="{ fontSize: '13px', fontWeight: 500, color: priColor }">{{ priLabel }}</span>
          <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
    </div>

    <!-- dates -->
    <div :style="{ padding: '0 20px 14px', display: 'flex', gap: '12px' }">
      <div :style="{ flex: 1 }">
        <div :style="lab">{{ t('task.fStart') }}</div>
        <input type="date" v-model="form.start_date" :style="dateBox" />
      </div>
      <div :style="{ flex: 1 }">
        <div :style="lab">{{ t('task.fDue') }}</div>
        <input type="date" v-model="form.due_date" :style="dateBox" />
      </div>
    </div>

    <!-- links: project / customer -->
    <div :style="{ padding: '0 20px 14px', display: 'flex', flexDirection: 'column', gap: '14px' }">
      <div>
        <div :style="lab">{{ t('task.fProject') }}</div>
        <div @click="projectSheet = true" :style="fieldBox">
          <span v-if="form.project_name" :style="{ fontSize: '13px', fontWeight: 500 }">{{ form.project_name }}</span>
          <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fProjectPh') }}</span>
          <span v-if="form.project_id" @click.stop="clearProject"
            :style="{ marginLeft: 'auto', color: TK.ink4, fontSize: '14px' }">✕</span>
          <span v-else :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
      <div>
        <div :style="lab">{{ t('task.fCustomer') }}</div>
        <div @click="customerSheet = true" :style="fieldBox">
          <span v-if="form.customer_name" :style="{ fontSize: '13px', fontWeight: 500 }">{{ form.customer_name }}</span>
          <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fCustomerPh') }}</span>
          <span v-if="form.customer_id" @click.stop="clearCustomer"
            :style="{ marginLeft: 'auto', color: TK.ink4, fontSize: '14px' }">✕</span>
          <span v-else :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
    </div>

    <!-- reviewers / collaborators -->
    <div :style="{ padding: '0 20px 14px', display: 'flex', flexDirection: 'column', gap: '14px' }">
      <div>
        <div :style="lab">{{ t('task.fReviewers') }}</div>
        <div @click="reviewerSheet = true" :style="fieldBox">
          <span v-if="reviewerNames" :style="{ fontSize: '13px', fontWeight: 500 }">{{ reviewerNames }}</span>
          <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fReviewersPh') }}</span>
          <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
      <div>
        <div :style="lab">{{ t('task.fShared') }}</div>
        <div @click="sharedSheet = true" :style="fieldBox">
          <span v-if="sharedNames" :style="{ fontSize: '13px', fontWeight: 500 }">{{ sharedNames }}</span>
          <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fSharedPh') }}</span>
          <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
        </div>
      </div>
    </div>

    <!-- description -->
    <div :style="{ ...lab, padding: '6px 20px 8px' }">{{ t('task.secDescription') }}</div>
    <div :style="{ margin: '0 16px 14px' }">
      <textarea v-model="form.description" rows="4" :placeholder="t('task.fDescPh')"
        :style="{ width: '100%', padding: '14px', background: TK.card, borderRadius: '12px',
          border: `1px solid ${TK.divider}`, fontSize: '13px', color: TK.ink, lineHeight: 1.6,
          outline: 'none', resize: 'none', fontFamily: TK.sans, boxSizing: 'border-box' }" />
    </div>

    <PersonPickerSheet v-model="assigneeSheet" :title="t('task.fAssignee')" :options="people"
      :selected="form.assignee_id" @update:selected="v => { form.assignee_id = v }" />
    <PickerSheet v-model="prioritySheet" :title="t('task.fPriority')"
      :options="priorityOptions" :selected="form.priority"
      @update:selected="v => { form.priority = v || 'normal' }" />
    <MultiPersonPickerSheet v-model="reviewerSheet" :title="t('task.fReviewers')" :options="people"
      :selected="form.reviewer_ids" @update:selected="v => { form.reviewer_ids = v }" />
    <MultiPersonPickerSheet v-model="sharedSheet" :title="t('task.fShared')" :options="people"
      :selected="form.shared_with_users" @update:selected="v => { form.shared_with_users = v }" />
    <ExSearchPickerSheet v-model="projectSheet" :title="t('task.fProject')"
      :placeholder="t('task.fProjectPh')" :search-fn="searchProjects" @pick="onPickProject" />
    <ExSearchPickerSheet v-model="customerSheet" :title="t('task.fCustomer')"
      :placeholder="t('task.fCustomerPh')" :search-fn="searchCustomers" @pick="onPickCustomer" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import client from '@/api/client'
import PersonPickerSheet from '@/components/common/PersonPickerSheet.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'
import MultiPersonPickerSheet from '@/components/common/MultiPersonPickerSheet.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'

const props = defineProps({
  form:   { type: Object, required: true },
  people: { type: Array,  default: () => [] },
})
const { t } = useI18n()
const form = props.form

const TK = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink3: '#7A7570', ink4: '#B5AEA3',
  divider: '#EBE6DD', accent: '#D97757', warn: '#C77B22', warnSoft: '#F9F1E6', red: '#B5453A',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}
const lab = { fontSize: '11px', color: TK.ink3, fontWeight: 600, marginBottom: '6px',
  textTransform: 'uppercase', letterSpacing: '0.4px' }
const fieldBox = { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 10px',
  background: TK.card, borderRadius: '8px', border: `1px solid ${TK.divider}` }
const dateBox = { width: '100%', boxSizing: 'border-box', padding: '8px 10px', background: TK.card,
  borderRadius: '8px', border: `1px solid ${TK.divider}`, fontSize: '13px', color: TK.ink,
  outline: 'none', fontFamily: TK.sans }

const assigneeSheet = ref(false)
const prioritySheet = ref(false)
const reviewerSheet = ref(false)
const sharedSheet = ref(false)
const projectSheet = ref(false)
const customerSheet = ref(false)

const priorityOptions = computed(() => [
  { value: 'urgent', label: t('task.priUrgent') },
  { value: 'high', label: t('task.priHigh') },
  { value: 'normal', label: t('task.priNormal') },
  { value: 'low', label: t('task.priLow') },
])
const priLabel = computed(() =>
  priorityOptions.value.find(o => o.value === form.priority)?.label || t('task.priNormal'))
const priColor = computed(() =>
  form.priority === 'urgent' ? TK.red : form.priority === 'high' ? TK.warn : TK.ink3)
const assigneeName = computed(() =>
  props.people.find(p => p.id === form.assignee_id)?.name || '')

function namesOf(ids) {
  if (!ids || !ids.length) return ''
  const m = new Map(props.people.map(p => [p.id, p.name]))
  return ids.map(i => m.get(i)).filter(Boolean).join('、')
}
const reviewerNames = computed(() => namesOf(form.reviewer_ids))
const sharedNames = computed(() => namesOf(form.shared_with_users))

async function searchProjects(q) {
  const r = await client.get('/mobile/projects', { params: { search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(p => ({
    id: p.id,
    label: p.name,
    sub: [p.stage_label, p.owner_name, p.city].filter(Boolean).join(' · '),
  }))
}
async function searchCustomers(q) {
  const r = await client.get('/mobile/customers', { params: { q: q || '', search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(c => ({
    id: c.id,
    label: c.name || c.company_name,
    sub: c.primary_contact_name || c.industry || '',
  }))
}
function onPickProject(it) { form.project_id = it.id; form.project_name = it.label }
function onPickCustomer(it) { form.customer_id = it.id; form.customer_name = it.label }
function clearProject() { form.project_id = null; form.project_name = '' }
function clearCustomer() { form.customer_id = null; form.customer_name = '' }
</script>
