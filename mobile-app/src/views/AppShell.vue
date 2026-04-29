<script setup>
import { RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const tabs = [
  { path: '/projects',  label: '项目', icon: 'M3 7h18M3 12h18M3 17h18' },
  { path: '/approval',  label: '审批', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
  { path: '/customers', label: '客户', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0' },
]

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- 顶部安全区域占位（刘海/灵动岛）-->
    <div class="bg-white" style="height: env(safe-area-inset-top)" />

    <!-- 主内容区 -->
    <div class="flex-1 overflow-hidden">
      <RouterView />
    </div>

    <!-- 底部导航 -->
    <nav class="bg-white border-t border-gray-100" style="padding-bottom: env(safe-area-inset-bottom)">
      <div class="flex">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="flex-1 flex flex-col items-center py-2 gap-0.5 text-xs transition"
          :class="$route.path.startsWith(tab.path) ? 'text-blue-600' : 'text-gray-400'"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" :d="tab.icon" />
          </svg>
          {{ tab.label }}
        </RouterLink>

        <!-- 退出按钮 -->
        <button
          @click="handleLogout"
          class="flex-1 flex flex-col items-center py-2 gap-0.5 text-xs text-gray-400 active:text-red-500 transition"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          退出
        </button>
      </div>
    </nav>
  </div>
</template>
