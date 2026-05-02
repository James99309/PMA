<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()
// 进入聊天详情、设置、广播等沉浸页时隐藏 tab bar（避免和聊天 composer 冲突）
const hideTabBar = computed(() => route.meta?.hideTabBar === true)

const tabs = [
  {
    path: '/projects',
    label: '项目',
    iconD: 'M4 6h16M4 10h16M4 14h10',
    iconDActive: 'M3 5.5h18M3 5.5a.5.5 0 010-1h18a.5.5 0 010 1M3 10.5h18M3 14.5h12',
  },
  {
    path: '/customers',
    label: '客户',
    iconD: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0',
    iconDActive: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0',
  },
  {
    path: '/messages',
    label: '聊天',
    iconD: 'M21 12c0 4.418-4.03 8-9 8a9.86 9.86 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    iconDActive: 'M21 12c0 4.418-4.03 8-9 8a9.86 9.86 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  },
  {
    path: '/profile',
    label: '我的',
    iconD: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    iconDActive: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
  },
]
</script>

<template>
  <div class="flex flex-col h-full bg-[#F7F5F2]">
    <!-- 顶部安全区域（刘海/灵动岛）-->
    <div style="height: env(safe-area-inset-top); background:#F7F5F2;" />

    <!-- 主内容区 -->
    <div class="flex-1 overflow-hidden">
      <RouterView />
    </div>

    <!-- 底部导航（聊天详情等沉浸页隐藏） -->
    <nav
      v-if="!hideTabBar"
      class="border-t border-[#E8E4E0]"
      style="background: rgba(247,245,242,0.92); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding-bottom: env(safe-area-inset-bottom);"
    >
      <div class="flex">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="flex-1 flex flex-col items-center py-2 gap-0.5 text-[11px] font-medium transition-colors"
          :class="$route.path.startsWith(tab.path) ? 'text-[var(--color-accent)]' : 'text-[var(--color-ink-3)]'"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            :stroke-width="$route.path.startsWith(tab.path) ? '2.2' : '1.7'"
          >
            <path stroke-linecap="round" stroke-linejoin="round" :d="tab.iconD" />
          </svg>
          {{ tab.label }}
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
