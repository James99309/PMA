<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer } from '@/api/customers'

const route = useRoute()
const router = useRouter()
const customer = ref(null)
const loading = ref(true)

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    customer.value = res.data.data
  } finally {
    loading.value = false
  }
}

function callPhone(phone) {
  if (phone) window.open(`tel:${phone}`)
}
function sendEmail(email) {
  if (email) window.open(`mailto:${email}`)
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3">
      <button @click="router.back()" class="text-blue-500 p-1 -ml-1">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-gray-900 flex-1 truncate">客户详情</h1>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="customer" class="flex-1 overflow-y-auto">
      <!-- 基本信息 -->
      <div class="bg-white px-4 py-5">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-lg font-bold">
            {{ customer.name?.[0] }}
          </div>
          <div>
            <h2 class="text-lg font-bold text-gray-900">{{ customer.name }}</h2>
            <p class="text-sm text-gray-400">{{ [customer.industry, customer.region].filter(Boolean).join(' · ') }}</p>
          </div>
        </div>
        <div v-if="customer.address" class="text-sm text-gray-500 flex gap-1">
          <svg class="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          </svg>
          {{ customer.address }}
        </div>
      </div>

      <!-- 联系人 -->
      <div v-if="customer.contacts?.length" class="mt-2">
        <div class="h-2 bg-gray-50" />
        <div class="bg-white px-4 py-3">
          <p class="text-xs text-gray-400 uppercase mb-3">联系人 ({{ customer.contacts.length }})</p>
          <ul class="space-y-4">
            <li v-for="ct in customer.contacts" :key="ct.id">
              <div class="flex items-start justify-between">
                <div>
                  <p class="font-medium text-gray-900">{{ ct.name }}</p>
                  <p class="text-xs text-gray-400">{{ [ct.title, ct.department].filter(Boolean).join(' · ') }}</p>
                </div>
                <div class="flex gap-2">
                  <button v-if="ct.phone" @click="callPhone(ct.phone)"
                    class="w-9 h-9 bg-green-100 rounded-full flex items-center justify-center text-green-600 active:bg-green-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                  </button>
                  <button v-if="ct.email" @click="sendEmail(ct.email)"
                    class="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 active:bg-blue-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
              <p v-if="ct.phone" class="text-sm text-gray-500 mt-1">{{ ct.phone }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
