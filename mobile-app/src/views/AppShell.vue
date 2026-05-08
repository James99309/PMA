<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { getUnreadCount } from '@/api/chat'
import { useAuthStore } from '@/stores/auth'
import { REGIONS } from '@/api/client'
import CrossRegionBar from '@/components/common/CrossRegionBar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
// 进入聊天详情、设置、广播等沉浸页时隐藏 tab bar（避免和聊天 composer 冲突）
const hideTabBar = computed(() => route.meta?.hideTabBar === true)

// away 时全局顶部琥珀条; 登录页等不显示
const showCrossBar = computed(() => auth.isAway && route.path !== '/login')
const currentRegion = computed(() => REGIONS[auth.regionId] || REGIONS.cn)

function backToHome() {
  if (auth.switchRegion(auth.homeRegionId)) {
    // Capacitor WebView 下 router.go(0) 是 no-op, 必须 location.reload 真刷新
    window.location.reload()
  }
}

// 未读消息数 —— 30s 轮询, 只数本区 (peer 走琥珀卡, 不再 sum)
const unreadTotal = ref(0)
let unreadTimer = null
async function refreshUnread() {
  try {
    const r = await getUnreadCount()
    unreadTotal.value = r.data?.data?.total_unread || 0
  } catch {
    // 静默失败
  }
}
onMounted(() => {
  refreshUnread()
  unreadTimer = setInterval(refreshUnread, 30000)
})
onUnmounted(() => { if (unreadTimer) clearInterval(unreadTimer) })

// 路由切换时立即刷新未读 (用户从聊天详情返回 tab badge 立刻更新, 不用等 30s)
watch(() => route.path, () => { refreshUnread() })

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

    <!-- 全局跨区域提示条: 用户切到非本位区时常驻 -->
    <CrossRegionBar v-if="showCrossBar"
      :region-flag="currentRegion.flag"
      :region-label="currentRegion.label"
      @back="backToHome" />

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
          class="flex-1 flex flex-col items-center py-2 gap-0.5 text-[11px] font-medium transition-colors relative"
          :class="$route.path.startsWith(tab.path) ? 'text-[var(--color-accent)]' : 'text-[var(--color-ink-3)]'"
        >
          <div class="relative">
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              :stroke-width="$route.path.startsWith(tab.path) ? '2.2' : '1.7'"
            >
              <path stroke-linecap="round" stroke-linejoin="round" :d="tab.iconD" />
            </svg>
            <!-- 聊天 tab 角标 -->
            <span v-if="tab.path === '/messages' && unreadTotal > 0"
              class="absolute -top-1 -right-2 min-w-[18px] h-[18px] px-1 rounded-full inline-flex items-center justify-center text-[10px] font-bold text-white"
              style="background: #FF3B30;">
              {{ unreadTotal > 99 ? '99+' : unreadTotal }}
            </span>
          </div>
          {{ tab.label }}
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
