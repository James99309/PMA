<!--
  TaskEditView - Edit task (P1b + P2 links/reviewers)
  Uses shared TaskFormFields, pre-filled from getTask, submits via PATCH
  updateTask (shared task_service.update_task). All UI text via t().
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
      <span :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('task.editTitle') }}</span>
      <span @click="canSave && submit()"
        :style="{ fontSize: '14px', fontWeight: 600,
          color: canSave ? TK.accent : TK.ink4 }">{{ t('common.save') }}</span>
    </div>

    <div v-if="loading" :style="{ flex: 1, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: TK.ink4 }">···</div>

    <div v-else :style="{ flex: 1, overflowY: 'auto', paddingBottom: '30px' }">
      <TaskFormFields :form="form" :people="people" :task-id="id" />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getTask, updateTask } from '@/api/tasks'
import { getAttributedCandidates } from '@/api/expense'
import TaskFormFields from '@/components/tasks/TaskFormFields.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const TK = {
  bg: '#F7F5F2', ink: '#1A1A1A', ink3: '#7A7570', ink4: '#B5AEA3',
  divider: '#EBE6DD', accent: '#D97757',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}

const id = computed(() => route.params.id)
const loading = ref(true)
const people = ref([])
const form = reactive({
  title: '', assignee_id: null, priority: 'normal', start_date: '', due_date: '',
  description: '', project_id: null, project_name: '', customer_id: null,
  customer_name: '', quotation_id: null, quotation_name: '',
  reviewer_ids: [], shared_with_users: [], pending_files: [], attachments: [],
})
const canSave = computed(() => !!form.title.trim() && !!form.assignee_id)

async function submit() {
  try {
    await updateTask(id.value, {
      title: form.title.trim(),
      assignee_id: form.assignee_id,
      priority: form.priority,
      start_date: form.start_date || null,
      due_date: form.due_date || null,
      description: form.description.trim() || null,
      project_id: form.project_id || null,
      customer_id: form.customer_id || null,
      quotation_id: form.quotation_id || null,
      reviewer_ids: form.reviewer_ids,
      shared_with_users: form.shared_with_users,
    })
    router.replace(`/tasks/${id.value}`)
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
  try {
    const r = await getTask(id.value)
    const d = r.data?.data || {}
    form.title = d.title || ''
    form.assignee_id = d.assignee_id || null
    form.priority = d.priority || 'normal'
    form.start_date = d.start_date ? String(d.start_date).slice(0, 10) : ''
    form.due_date = d.due_date ? String(d.due_date).slice(0, 10) : ''
    form.description = d.description || ''
    form.project_id = d.project_id || null
    form.project_name = d.project_name || ''
    form.customer_id = d.customer_id || null
    form.customer_name = d.customer_name || ''
    form.quotation_id = d.quotation_id || null
    form.quotation_name = d.quotation_number || ''
    form.reviewer_ids = (d.reviewers || []).map(rv => rv.reviewer_id).filter(Boolean)
    form.shared_with_users = Array.isArray(d.shared_with_users) ? [...d.shared_with_users] : []
    form.attachments = Array.isArray(d.attachments) ? [...d.attachments] : []
  } catch (e) { /* noop */ } finally {
    loading.value = false
  }
})
</script>
