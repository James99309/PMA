<!--
  TaskCreateView - New task (P1 step 4)
  Pixel port of Claude Design "PMA Task EN" task-create-en.jsx (core fields).
  All UI text via t() (i18n rule). Local TK = design task-base palette.
-->
<template>
  <div :style="{ background: TK.bg, height: '100%', fontFamily: TK.sans, color: TK.ink,
    display: 'flex', flexDirection: 'column' }">
    <div class="status-pad" />
    <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 16px', flexShrink: 0,
      borderBottom: `1px solid ${TK.divider}` }">
      <span @click="router.back()" class="active:opacity-60"
        :style="{ fontSize: '14px', color: TK.ink3 }">{{ t('common.cancel') }}</span>
      <span :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('task.newTask') }}</span>
      <span @click="canCreate && submit()"
        :style="{ fontSize: '14px', fontWeight: 600,
          color: canCreate ? TK.accent : TK.ink4 }">{{ t('task.create') }}</span>
    </div>

    <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '30px' }">
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
            <template v-if="assigneeName">
              <span :style="{ fontSize: '13px', fontWeight: 500 }">{{ assigneeName }}</span>
            </template>
            <span v-else :style="{ fontSize: '13px', color: TK.ink4 }">{{ t('task.fAssigneePh') }}</span>
            <span :style="{ marginLeft: 'auto', color: TK.ink4 }">›</span>
          </div>
        </div>
        <div :style="{ width: '130px' }">
          <div :style="lab">{{ t('task.fPriority') }}</div>
          <div @click="prioritySheet = true" :style="{ ...fieldBox,
            background: form.priority === 'urgent' || form.priority === 'high' ? TK.warnSoft : TK.card,
            border: `1px solid ${form.priority === 'urgent' || form.priority === 'high' ? TK.warn : TK.divider}` }">
            <span :style="{ width: '6px', height: '6px', borderRadius: '3px',
              background: priColor }" />
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

      <!-- description -->
      <div :style="{ ...lab, padding: '6px 20px 8px' }">{{ t('task.secDescription') }}</div>
      <div :style="{ margin: '0 16px 14px' }">
        <textarea v-model="form.description" rows="4" :placeholder="t('task.fDescPh')"
          :style="{ width: '100%', padding: '14px', background: TK.card, borderRadius: '12px',
            border: `1px solid ${TK.divider}`, fontSize: '13px', color: TK.ink, lineHeight: 1.6,
            outline: 'none', resize: 'none', fontFamily: TK.sans, boxSizing: 'border-box' }" />
      </div>
    </div>

    <PersonPickerSheet v-model="assigneeSheet" :options="people"
      :selected="form.assignee_id"
      @update:selected="v => { form.assignee_id = v }" />
    <PickerSheet v-model="prioritySheet" :title="t('task.fPriority')"
      :options="priorityOptions" :selected="form.priority"
      @update:selected="v => { form.priority = v || 'normal' }" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createTask } from '@/api/tasks'
import { getAttributedCandidates } from '@/api/expense'
import PersonPickerSheet from '@/components/common/PersonPickerSheet.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'

const router = useRouter()
const { t } = useI18n()

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

const form = reactive({ title: '', assignee_id: null, priority: 'normal',
  start_date: '', due_date: '', description: '' })
const assigneeSheet = ref(false)
const prioritySheet = ref(false)
const people = ref([])

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
  people.value.find(p => p.id === form.assignee_id)?.name || '')
const canCreate = computed(() => !!form.title.trim() && !!form.assignee_id)

async function submit() {
  try {
    const r = await createTask({
      title: form.title.trim(),
      assignee_id: form.assignee_id,
      priority: form.priority,
      start_date: form.start_date || null,
      due_date: form.due_date || null,
      description: form.description.trim() || null,
    })
    const id = r.data?.data?.id
    if (id) router.replace(`/tasks/${id}`)
    else router.back()
  } catch (e) { /* keep form on failure */ }
}

onMounted(async () => {
  try {
    const r = await getAttributedCandidates()
    people.value = (r.data?.data || []).map(u => ({
      id: u.id,
      name: u.name || u.real_name || u.username,
      department: u.department || u.dept || '',
    }))
  } catch (e) { /* noop */ }
})
</script>
