<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCustomers } from '@/api/customers'

const router = useRouter()
const customers = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const page = ref(1)

async function load(reset = false) {
  if (reset) { page.value = 1; customers.value = [] }
  loading.value = true
  try {
    const res = await getCustomers({ search: search.value, page: page.value })
    const data = res.data.data
    total.value = data.total
    customers.value = reset ? data.items : [...customers.value, ...data.items]
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (customers.value.length < total.value) {
    page.value++
    load()
  }
}

onMounted(() => load(true))
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="bg-white px-4 py-3 border-b border-gray-100">
      <div class="flex items-center bg-gray-100 rounded-xl px-3 py-2 gap-2">
        <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="search" type="search" placeholder="搜索客户..." @keyup.enter="load(true)"
          class="flex-1 bg-transparent text-sm outline-none placeholder-gray-400" />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-if="loading && customers.length === 0" class="flex justify-center items-center h-40">
        <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <ul v-else class="divide-y divide-gray-100">
        <li v-for="c in customers" :key="c.id"
          @click="router.push(`/customers/${c.id}`)"
          class="bg-white px-4 py-4 active:bg-gray-50 cursor-pointer"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">
              {{ c.name?.[0] || '?' }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 truncate">{{ c.name }}</p>
              <p class="text-xs text-gray-400 mt-0.5 truncate">
                {{ [c.industry, c.region].filter(Boolean).join(' · ') || '暂无信息' }}
              </p>
            </div>
            <div v-if="c.primary_contact_name" class="text-right shrink-0">
              <p class="text-xs text-gray-700">{{ c.primary_contact_name }}</p>
              <p class="text-xs text-gray-400">{{ c.primary_contact_phone }}</p>
            </div>
          </div>
        </li>
      </ul>

      <div v-if="customers.length < total" class="py-4 text-center">
        <button @click="loadMore" :disabled="loading" class="text-blue-500 text-sm disabled:opacity-50">
          {{ loading ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>
  </div>
</template>
