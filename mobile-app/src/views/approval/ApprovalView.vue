<script setup>
import { ref, onMounted } from 'vue'
import { getPendingApprovals, doApprovalAction } from '@/api/approval'

const items = ref([])
const loading = ref(true)
const acting = ref(null)
const commentMap = ref({})

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
  <div class="flex flex-col h-full bg-[#F7F5F2]">
    <!-- 大标题头部 -->
    <div class="bg-[#F7F5F2] px-5 pt-5 pb-4">
      <p class="text-[14px] text-[#9CA3AF] mb-1">审批中心</p>
      <h1 class="font-serif text-[60px] font-bold leading-none text-[#1A1A1A]">审批</h1>
      <p class="text-[14px] text-[#9CA3AF] mt-1.5">待处理 {{ items.length }} 项</p>
    </div>
    <div class="h-px bg-[#E8E4E0]" />

    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 border-[#D97757] border-t-transparent rounded-full animate-spin" />
      </div>

      <div v-else-if="items.length === 0"
        class="flex flex-col items-center justify-center h-40 text-[#9CA3AF] text-sm gap-2">
        <svg class="w-10 h-10 text-[#D0CBC4]" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        暂无待审批
      </div>

      <ul v-else class="px-4 py-3 space-y-3">
        <li v-for="item in items" :key="item.id"
          class="bg-white rounded-2xl p-4 border border-[#F0EDE9]">
          <div class="flex items-start justify-between gap-2 mb-3">
            <div class="flex-1 min-w-0">
              <span class="inline-block text-xs bg-[#F4E4D8] text-[#D97757] px-2 py-0.5 rounded-full font-medium mb-1">
                {{ item.object_type_label }}
              </span>
              <p class="font-serif text-[16px] font-medium text-[#1A1A1A] leading-snug">{{ item.object_name }}</p>
              <p class="text-xs text-[#7A7570] mt-0.5">提交人：{{ item.submitted_by_name }}</p>
            </div>
          </div>

          <input
            v-model="commentMap[item.id]"
            type="text"
            placeholder="审批备注（选填）"
            class="w-full bg-[#F7F5F2] border border-[#E8E4E0] rounded-xl px-3 py-2.5 text-sm outline-none focus:border-[#D97757] mb-3 text-[#1A1A1A] placeholder-[#9CA3AF]"
          />

          <div class="flex gap-2">
            <button
              @click="action(item.id, 'reject')"
              :disabled="acting === item.id"
              class="flex-1 border border-[#FCA5A5] text-[#EF4444] rounded-xl py-2.5 text-sm font-medium active:bg-red-50 disabled:opacity-40">
              驳回
            </button>
            <button
              @click="action(item.id, 'approve')"
              :disabled="acting === item.id"
              class="flex-1 bg-[#1A1A1A] text-white rounded-xl py-2.5 text-sm font-semibold active:bg-[#333] disabled:opacity-40">
              {{ acting === item.id ? '处理中…' : '同意' }}
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
