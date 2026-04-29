<script setup>
import { ref, onMounted } from 'vue'
import { getPendingApprovals, doApprovalAction } from '@/api/approval'

const items = ref([])
const loading = ref(true)
const acting = ref(null)
const commentMap = ref({})
const tab = ref('pending')

async function load() {
  loading.value = true
  try {
    const res = await getPendingApprovals()
    items.value = res.data.data.items
  } finally {
    loading.value = false
  }
}

async function action(instanceId, act) {
  acting.value = instanceId
  try {
    await doApprovalAction(instanceId, act, commentMap.value[instanceId] || '')
    items.value = items.value.filter(i => i.id !== instanceId)
  } finally {
    acting.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="bg-white border-b border-gray-100 px-4 py-3">
      <h1 class="font-semibold text-gray-900">审批中心</h1>
      <p class="text-xs text-gray-400 mt-0.5">待审批 {{ items.length }} 项</p>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <div v-else-if="items.length === 0" class="flex flex-col items-center justify-center h-40 text-gray-400 text-sm gap-2">
        <svg class="w-10 h-10 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        暂无待审批
      </div>

      <ul v-else class="divide-y divide-gray-100 space-y-2 p-3">
        <li v-for="item in items" :key="item.id" class="bg-white rounded-2xl p-4 shadow-sm">
          <div class="flex items-start justify-between gap-2 mb-3">
            <div>
              <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{{ item.object_type_label }}</span>
              <p class="font-medium text-gray-900 mt-1">{{ item.object_name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">提交人：{{ item.submitted_by_name }}</p>
            </div>
          </div>

          <input
            v-model="commentMap[item.id]"
            type="text"
            placeholder="审批备注（选填）"
            class="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-300 mb-3"
          />

          <div class="flex gap-2">
            <button
              @click="action(item.id, 'reject')"
              :disabled="acting === item.id"
              class="flex-1 border border-red-200 text-red-500 rounded-xl py-2.5 text-sm font-medium active:bg-red-50 disabled:opacity-50"
            >
              驳回
            </button>
            <button
              @click="action(item.id, 'approve')"
              :disabled="acting === item.id"
              class="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium active:bg-blue-700 disabled:opacity-50"
            >
              {{ acting === item.id ? '处理中...' : '同意' }}
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
