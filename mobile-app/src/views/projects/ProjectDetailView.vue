<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, addProjectNote } from '@/api/projects'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const loading = ref(true)
const noteText = ref('')
const addingNote = ref(false)
const showNoteBox = ref(false)

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
  } finally {
    addingNote.value = false
  }
}

onMounted(load)

const stageLabel = {
  lead: '线索', opportunity: '商机', proposal: '投标/方案',
  negotiation: '谈判', won: '赢单', lost: '丢单', suspended: '暂停',
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 顶部栏 -->
    <div class="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3">
      <button @click="router.back()" class="text-blue-500 p-1 -ml-1">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-gray-900 flex-1 truncate">项目详情</h1>
      <button @click="showNoteBox = !showNoteBox" class="text-blue-500 text-sm">+ 跟进</button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="project" class="flex-1 overflow-y-auto">
      <!-- 项目基本信息 -->
      <div class="bg-white px-4 py-5 space-y-3">
        <h2 class="text-lg font-bold text-gray-900">{{ project.name }}</h2>
        <div class="flex gap-2 flex-wrap">
          <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
            {{ stageLabel[project.current_stage] || project.current_stage }}
          </span>
          <span class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
            {{ project.status }}
          </span>
        </div>
        <p class="text-2xl font-bold text-gray-900">
          {{ project.amount ? project.amount.toFixed(2) + ' 万' : '-' }}
        </p>
      </div>

      <div class="h-2 bg-gray-50" />

      <!-- 详情字段 -->
      <div class="bg-white px-4 divide-y divide-gray-50">
        <div class="py-3 flex justify-between text-sm">
          <span class="text-gray-500">负责人</span>
          <span class="text-gray-900">{{ project.owner_name || '-' }}</span>
        </div>
        <div class="py-3 flex justify-between text-sm">
          <span class="text-gray-500">活跃度</span>
          <span class="text-gray-900">{{ project.activity_status || '-' }}</span>
        </div>
        <div v-if="project.stage_description" class="py-3 text-sm">
          <p class="text-gray-500 mb-1">阶段描述</p>
          <p class="text-gray-800 break-words leading-relaxed line-clamp-6">{{ project.stage_description }}</p>
        </div>
      </div>

      <!-- 关联客户 -->
      <div v-if="project.customers?.length" class="mt-2">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-3">
          <p class="text-xs text-gray-400 uppercase mb-2">关联客户</p>
          <div class="space-y-1">
            <div v-for="c in project.customers" :key="c.id" class="text-sm text-gray-800">{{ c.name }}</div>
          </div>
        </div>
      </div>

      <!-- 跟进输入框 -->
      <div v-if="showNoteBox" class="mt-2">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-4">
          <p class="text-xs text-gray-400 mb-2">添加跟进记录</p>
          <textarea
            v-model="noteText"
            rows="3"
            placeholder="输入跟进内容..."
            class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none"
          />
          <div class="flex gap-2 mt-2">
            <button @click="showNoteBox = false" class="flex-1 border border-gray-200 text-gray-600 rounded-xl py-2 text-sm">取消</button>
            <button @click="submitNote" :disabled="addingNote" class="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm disabled:opacity-60">
              {{ addingNote ? '提交中...' : '提交' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
