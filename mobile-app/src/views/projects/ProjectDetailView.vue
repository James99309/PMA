<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, addProjectNote } from '@/api/projects'
import client from '@/api/client'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const loading = ref(true)

const noteText = ref('')
const addingNote = ref(false)
const showNoteBox = ref(false)

const showStagePicker = ref(false)
const updatingStage = ref(false)

const showAuthModal = ref(false)
const authNote = ref('')
const submittingAuth = ref(false)

const STAGES = [
  { key: 'discover',   label: '发现' },
  { key: 'embed',      label: '植入' },
  { key: 'pre_tender', label: '标前' },
  { key: 'tendering',  label: '标中' },
  { key: 'awarded',    label: '中标' },
  { key: 'quoted',     label: '批价' },
  { key: 'signed',     label: '签约' },
  { key: 'lost',       label: '失败' },
  { key: 'paused',     label: '搁置' },
]

const STAGE_STYLE = {
  discover:   'background:linear-gradient(135deg,#d3e3fc,#b8d4f8,#9dc5f4);color:#0d47a1',
  embed:      'background:linear-gradient(135deg,#b7ddc8,#9fd3b3,#87c99e);color:#1b5e20',
  pre_tender: 'background:linear-gradient(135deg,#91c79f,#7bb88a,#65a975);color:#1b5e20',
  tendering:  'background:linear-gradient(135deg,#6daf6c,#5a9259,#4d7c4c);color:#fff',
  awarded:    'background:linear-gradient(135deg,#559c4c,#477f3f,#3a6832);color:#fff',
  quoted:     'background:linear-gradient(135deg,#3c8c2c,#327326,#285e20);color:#fff',
  signed:     'background:linear-gradient(135deg,#216822,#1b541d,#154518);color:#fff',
  lost:       'background:linear-gradient(135deg,#6e2b23,#5a241e,#4a1f1a);color:#fff',
  paused:     'background:linear-gradient(135deg,#9e9e9e,#858585,#6c6c6c);color:#fff',
}

const canAdvanceStage = computed(() => {
  if (!project.value) return false
  return project.value.current_stage !== 'signed' && !project.value.is_locked
})

// 只在未授权且未申请中时显示申请按钮
const showAuthButton = computed(() => {
  if (!project.value) return false
  return !project.value.authorization_code && project.value.authorization_status !== 'pending'
})

async function load() {
  try {
    const res = await getProject(route.params.id)
    project.value = res.data.data
  } finally {
    loading.value = false
  }
}

async function submitNote() {
  if (!noteText.value.trim()) return
  addingNote.value = true
  try {
    await addProjectNote(route.params.id, noteText.value.trim())
    noteText.value = ''
    showNoteBox.value = false
    await load()
  } finally {
    addingNote.value = false
  }
}

async function updateStage(stageKey) {
  updatingStage.value = true
  try {
    await client.post(`/mobile/projects/${route.params.id}/stage`, { stage: stageKey })
    showStagePicker.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.message || '更新失败')
  } finally {
    updatingStage.value = false
  }
}

async function submitAuthRequest() {
  submittingAuth.value = true
  try {
    const res = await client.post(`/mobile/projects/${route.params.id}/auth-request`, { note: authNote.value })
    alert(res.data.message)
    showAuthModal.value = false
    authNote.value = ''
    await load()
  } catch (e) {
    alert(e.response?.data?.message || '提交失败')
  } finally {
    submittingAuth.value = false
  }
}

function callPhone(phone) { if (phone) window.open(`tel:${phone}`) }
function sendEmail(email) { if (email) window.open(`mailto:${email}`) }

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-2">
      <button @click="router.back()" class="text-blue-500 p-1 -ml-1 shrink-0">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-gray-900 flex-1 truncate text-sm">项目详情</h1>
      <button @click="showNoteBox = !showNoteBox" class="text-blue-500 text-xs px-2 py-1 border border-blue-200 rounded-lg shrink-0">
        + 跟进
      </button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="project" class="flex-1 overflow-y-auto">

      <!-- 基本信息 -->
      <div class="bg-white px-4 py-4">
        <h2 class="text-base font-bold text-gray-900 mb-2">{{ project.name }}</h2>
        <div class="flex flex-wrap gap-1.5 mb-3">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
            :style="STAGE_STYLE[project.current_stage] || 'background:#e5e7eb;color:#4b5563'">
            {{ project.stage_label || project.current_stage }}
          </span>
          <!-- 已授权：只在徽章显示，不显示按钮 -->
          <span v-if="project.authorization_code"
            class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-mono">
            {{ project.authorization_code }}
          </span>
          <span v-else-if="project.authorization_status === 'pending'"
            class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
            授权申请中
          </span>
          <span v-else-if="project.authorization_status === 'rejected'"
            class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-600">
            授权已拒绝
          </span>
        </div>
        <p class="text-2xl font-bold text-gray-900">
          {{ project.amount ? project.amount.toFixed(2) + ' 万' : '-' }}
          <span class="text-sm font-normal text-gray-400 ml-1">{{ project.currency }}</span>
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="bg-white border-t border-gray-50 px-4 py-3 flex gap-2">
        <button v-if="canAdvanceStage" @click="showStagePicker = true"
          class="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm font-medium active:bg-blue-700">
          推进阶段
        </button>
        <div v-else class="flex-1 bg-gray-100 text-gray-400 rounded-xl py-2 text-sm text-center">
          {{ project.current_stage === 'signed' ? '已签约锁定' : '项目已锁定' }}
        </div>
        <button v-if="showAuthButton" @click="showAuthModal = true"
          class="flex-1 border border-blue-200 text-blue-600 rounded-xl py-2 text-sm font-medium active:bg-blue-50">
          申请授权
        </button>
      </div>

      <div class="h-2 bg-gray-50" />

      <!-- 详情字段 -->
      <div class="bg-white px-4 divide-y divide-gray-50">
        <div class="py-2.5 flex justify-between text-sm">
          <span class="text-gray-400 shrink-0 mr-4">负责人</span>
          <span class="text-gray-900">{{ project.owner_name || '-' }}</span>
        </div>
        <div class="py-2.5 flex justify-between text-sm">
          <span class="text-gray-400 shrink-0 mr-4">活跃度</span>
          <span class="text-gray-900">{{ project.activity_label || '-' }}</span>
        </div>
        <div v-if="project.project_type" class="py-2.5 flex justify-between text-sm">
          <span class="text-gray-400 shrink-0 mr-4">项目类型</span>
          <span class="text-gray-900">{{ project.project_type_label || project.project_type }}</span>
        </div>
        <div v-if="project.end_user" class="py-2.5 flex justify-between text-sm">
          <span class="text-gray-400 shrink-0 mr-4">最终用户</span>
          <span class="text-gray-900 truncate max-w-52 text-right">{{ project.end_user }}</span>
        </div>
        <div v-if="project.delivery_forecast" class="py-2.5 flex justify-between text-sm">
          <span class="text-gray-400 shrink-0 mr-4">预计交货</span>
          <span class="text-gray-900">{{ project.delivery_forecast }}</span>
        </div>
      </div>

      <!-- 关联客户（可点击） -->
      <div v-if="project.customers?.length">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white">
          <p class="text-xs text-gray-400 px-4 pt-3 pb-1">关联客户</p>
          <div class="divide-y divide-gray-50">
            <button v-for="c in project.customers" :key="c.id"
              @click="router.push(`/customers/${c.id}`)"
              class="w-full px-4 py-3 flex items-center justify-between active:bg-gray-50">
              <span class="text-sm text-gray-900">{{ c.name }}</span>
              <svg class="w-4 h-4 text-gray-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 联系人 -->
      <div v-if="project.contacts?.length">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-3">
          <p class="text-xs text-gray-400 mb-3">联系人 ({{ project.contacts.length }})</p>
          <ul class="space-y-3">
            <li v-for="ct in project.contacts" :key="ct.id" class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">{{ ct.name }}</p>
                <p class="text-xs text-gray-400">{{ [ct.title, ct.company_name].filter(Boolean).join(' · ') }}</p>
              </div>
              <div class="flex gap-2 shrink-0">
                <button v-if="ct.phone" @click="callPhone(ct.phone)"
                  class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600 active:bg-green-200">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </button>
                <button v-if="ct.email" @click="sendEmail(ct.email)"
                  class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 active:bg-blue-200">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- 报价单入口 -->
      <div>
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-3">
          <p class="text-xs text-gray-400 mb-2">报价单 ({{ project.quotation_count || 0 }})</p>
          <div v-if="project.quotations?.length" class="space-y-2">
            <div v-for="q in project.quotations" :key="q.id"
              class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <div>
                <p class="text-sm font-medium text-gray-900">{{ q.number }}</p>
                <p class="text-xs text-gray-400">{{ q.created_at }}</p>
              </div>
              <div class="text-right">
                <p class="text-sm font-semibold text-gray-800">{{ q.total }}万</p>
                <span class="text-xs px-1.5 py-0.5 rounded"
                  :class="q.status === 'approved' ? 'bg-green-100 text-green-700' : q.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500'">
                  {{ q.status === 'approved' ? '已批准' : q.status === 'pending' ? '审批中' : q.status || '草稿' }}
                </span>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400 text-center py-2">暂无报价单</p>
        </div>
      </div>

      <!-- 跟进记录 -->
      <div>
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-3">
          <p class="text-xs text-gray-400 mb-3">跟进记录 ({{ project.actions?.length || 0 }})</p>
          <ul v-if="project.actions?.length" class="space-y-3">
            <li v-for="a in project.actions" :key="a.id" class="flex gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-400 mb-0.5">{{ a.date }} · {{ a.owner_name }}</p>
                <p class="text-sm text-gray-800 break-words leading-relaxed">{{ a.communication }}</p>
              </div>
            </li>
          </ul>
          <p v-else class="text-sm text-gray-400 text-center py-2">暂无跟进记录</p>
        </div>
      </div>

      <!-- 跟进输入框 -->
      <div v-if="showNoteBox">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-4">
          <p class="text-xs text-gray-400 mb-2">添加跟进记录</p>
          <textarea v-model="noteText" rows="3" placeholder="输入跟进内容..."
            class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none" />
          <div class="flex gap-2 mt-2">
            <button @click="showNoteBox = false" class="flex-1 border border-gray-200 text-gray-600 rounded-xl py-2 text-sm">取消</button>
            <button @click="submitNote" :disabled="addingNote" class="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm disabled:opacity-60">
              {{ addingNote ? '提交中...' : '提交' }}
            </button>
          </div>
        </div>
      </div>

      <div class="h-8" />
    </div>

    <!-- 阶段选择器 -->
    <Teleport to="body">
      <div v-if="showStagePicker" class="fixed inset-0 z-50 flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/40" @click="showStagePicker = false" />
        <div class="relative bg-white rounded-t-2xl pt-4 pb-8">
          <div class="flex items-center justify-between px-4 mb-3">
            <h3 class="font-semibold text-gray-900">选择新阶段</h3>
            <button @click="showStagePicker = false" class="text-gray-400 text-sm">取消</button>
          </div>
          <div class="divide-y divide-gray-50">
            <button v-for="s in STAGES" :key="s.key"
              @click="updateStage(s.key)"
              :disabled="s.key === project.current_stage || updatingStage"
              class="w-full px-4 py-3 flex items-center justify-between disabled:opacity-40 active:bg-gray-50">
              <span class="text-xs px-2.5 py-1 rounded-full font-medium"
                :style="STAGE_STYLE[s.key] || 'background:#e5e7eb;color:#4b5563'">{{ s.label }}</span>
              <svg v-if="s.key === project.current_stage" class="w-4 h-4 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 授权申请弹窗 -->
    <Teleport to="body">
      <div v-if="showAuthModal" class="fixed inset-0 z-50 flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/40" @click="showAuthModal = false" />
        <div class="relative bg-white rounded-t-2xl pt-4 pb-8 px-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-900">提交授权申请</h3>
            <button @click="showAuthModal = false" class="text-gray-400 text-sm">取消</button>
          </div>
          <textarea v-model="authNote" rows="3" placeholder="申请备注（选填）..."
            class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none mb-3" />
          <button @click="submitAuthRequest" :disabled="submittingAuth"
            class="w-full bg-blue-600 text-white rounded-xl py-3 text-sm font-medium disabled:opacity-60">
            {{ submittingAuth ? '提交中...' : '确认提交授权申请' }}
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>
