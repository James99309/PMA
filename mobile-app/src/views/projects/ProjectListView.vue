<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects } from '@/api/projects'

const router = useRouter()
const projects = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const page = ref(1)

const stageColors = {
  lead: 'bg-gray-100 text-gray-600',
  opportunity: 'bg-blue-100 text-blue-700',
  proposal: 'bg-yellow-100 text-yellow-700',
  negotiation: 'bg-orange-100 text-orange-700',
  won: 'bg-green-100 text-green-700',
  lost: 'bg-red-100 text-red-600',
  suspended: 'bg-gray-100 text-gray-500',
}

async function load(reset = false) {
  if (reset) { page.value = 1; projects.value = [] }
  loading.value = true
  try {
    const res = await getProjects({ search: search.value, page: page.value, per_page: 20 })
    const data = res.data.data
    total.value = data.total
    projects.value = reset ? data.items : [...projects.value, ...data.items]
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (projects.value.length < total.value) {
    page.value++
    load()
  }
}

onMounted(() => load(true))
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 搜索栏 -->
    <div class="bg-white px-4 py-3 border-b border-gray-100">
      <div class="flex items-center bg-gray-100 rounded-xl px-3 py-2 gap-2">
        <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="search"
          type="search"
          placeholder="搜索项目..."
          @keyup.enter="load(true)"
          class="flex-1 bg-transparent text-sm outline-none placeholder-gray-400"
        />
      </div>
    </div>

    <!-- 列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading && projects.length === 0" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <div v-else-if="projects.length === 0" class="flex flex-col items-center justify-center h-40 text-gray-400 text-sm">
        暂无项目
      </div>

      <ul v-else class="divide-y divide-gray-100">
        <li
          v-for="p in projects"
          :key="p.id"
          @click="router.push(`/projects/${p.id}`)"
          class="bg-white px-4 py-4 active:bg-gray-50 transition cursor-pointer"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 truncate">{{ p.name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ p.owner_name }}</p>
            </div>
            <div class="flex flex-col items-end gap-1 shrink-0">
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', stageColors[p.current_stage] || 'bg-gray-100 text-gray-600']">
                {{ p.stage_label }}
              </span>
              <span class="text-sm font-semibold text-gray-700">
                {{ p.amount ? p.amount.toFixed(2) + '万' : '-' }}
              </span>
            </div>
          </div>
        </li>
      </ul>

      <!-- 加载更多 -->
      <div v-if="projects.length < total" class="py-4 text-center">
        <button @click="loadMore" :disabled="loading" class="text-blue-500 text-sm disabled:opacity-50">
          {{ loading ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>
  </div>
</template>
