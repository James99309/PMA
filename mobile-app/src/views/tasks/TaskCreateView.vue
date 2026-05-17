<!--
  TaskCreateView - New task (P1 step 4 + P2 links/reviewers)
  Uses shared TaskFormFields. All UI text via t() (i18n rule).
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
      <span @click="!submitting && canCreate && submit()"
        :style="{ fontSize: '14px', fontWeight: 600,
          color: (canCreate && !submitting) ? TK.accent : TK.ink4 }">
        {{ submitting ? t('task.saving') : t('task.create') }}</span>
    </div>

    <div :style="{ flex: 1, overflowY: 'auto', paddingBottom: '30px' }">
      <TaskFormFields :form="form" :people="people" />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createTask, uploadTaskAttachment } from '@/api/tasks'
import { getAttributedCandidates } from '@/api/expense'
import TaskFormFields from '@/components/tasks/TaskFormFields.vue'

const router = useRouter()
const { t } = useI18n()

const TK = {
  bg: '#F7F5F2', ink: '#1A1A1A', ink3: '#7A7570', ink4: '#B5AEA3',
  divider: '#EBE6DD', accent: '#D97757',
  sans: '-apple-system, "SF Pro Text", "PingFang SC", system-ui, sans-serif',
}

const form = reactive({
  title: '', assignee_id: null, priority: 'normal', start_date: '', due_date: '',
  description: '', project_id: null, project_name: '', customer_id: null,
  customer_name: '', quotation_id: null, quotation_name: '',
  reviewer_ids: [], shared_with_users: [], pending_files: [], attachments: [],
})
const people = ref([])
const submitting = ref(false)
const canCreate = computed(() => !!form.title.trim() && !!form.assignee_id)

async function submit() {
  if (submitting.value) return          // guard: block double-tap duplicate create
  submitting.value = true
  try {
    const r = await createTask({
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
    const id = r.data?.data?.id
    if (id) {
      // upload attachments in background (no await); enter detail right away
      const files = [...form.pending_files]
      router.replace(`/tasks/${id}`)
      files.forEach(f => {
        const fd = new FormData()
        fd.append('file', f)
        uploadTaskAttachment(id, fd).catch(() => { /* ignore single-file failure */ })
      })
    } else {
      submitting.value = false
      router.back()
    }
  } catch (e) {
    submitting.value = false          // reset on failure so user can retry
  }
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
