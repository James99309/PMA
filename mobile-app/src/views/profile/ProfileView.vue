<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CapacitorUpdater } from '@capgo/capacitor-updater'

const router = useRouter()
const auth = useAuthStore()

// Bundle 版本（Capgo 当前激活的）
const bundleId = ref('builtin')
const bundleVer = ref('-')
const bundleStatus = ref('')

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

async function checkUpdate() {
  bundleStatus.value = '检查中…'
  try {
    const latest = await CapacitorUpdater.getLatest()
    if (latest?.version && latest.version !== bundleVer.value) {
      bundleStatus.value = `发现新版 ${latest.version}，下载中…`
      const dl = await CapacitorUpdater.download({
        url: latest.url,
        version: latest.version,
      })
      bundleStatus.value = `下载完成，正在切换…`
      await CapacitorUpdater.set({ id: dl.id })
    } else {
      bundleStatus.value = '已是最新'
    }
  } catch (e) {
    bundleStatus.value = `检查失败: ${e.message || e}`
  }
}

onMounted(async () => {
  try {
    const info = await CapacitorUpdater.current()
    bundleId.value = info?.bundle?.id || 'builtin'
    bundleVer.value = info?.bundle?.version || 'builtin'
  } catch {
    // Web/dev 环境调用会失败，忽略
  }
})
</script>

<template>
  <div class="flex flex-col h-full bg-[#F7F5F2]">
    <div class="bg-[#F7F5F2] px-5 pt-5 pb-4">
      <p class="text-[14px] text-[#9CA3AF] mb-1">账户设置</p>
      <h1 class="font-serif text-[60px] font-bold leading-none text-[#1A1A1A]">我的</h1>
    </div>
    <div class="h-px bg-[#E8E4E0]" />

    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      <!-- User card -->
      <div class="bg-white rounded-2xl px-4 py-4 flex items-center gap-3">
        <div class="w-12 h-12 rounded-full bg-[#F4E4D8] flex items-center justify-center text-[#D97757] font-semibold text-lg shrink-0">
          {{ auth.user?.real_name?.[0] || auth.user?.username?.[0] || '?' }}
        </div>
        <div>
          <p class="font-medium text-[#1A1A1A]">{{ auth.user?.real_name || auth.user?.username }}</p>
          <p class="text-sm text-[#7A7570] mt-0.5">{{ auth.user?.email || '' }}</p>
        </div>
      </div>

      <!-- 工作入口 (审批等高频功能从 TabBar 移到这里) -->
      <div class="bg-white rounded-2xl overflow-hidden">
        <button @click="router.push('/approval')"
          class="w-full flex items-center gap-3 px-4 py-4 active:bg-gray-50 text-left">
          <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-[#1A1A1A] font-medium flex-1">审批中心</span>
          <svg width="7" height="11" viewBox="0 0 7 11">
            <path d="M1 1l4 4.5L1 10" stroke="#7A7570" stroke-width="1.4" fill="none" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <!-- 版本 / OTA 状态 -->
      <div class="bg-white rounded-2xl overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between"
          style="border-bottom: 1px solid var(--color-divider);">
          <span class="text-[13px]" style="color: var(--color-ink-2);">App 版本</span>
          <span class="text-[12px] tabular" style="color: var(--color-ink-3);">{{ bundleVer }}</span>
        </div>
        <button @click="checkUpdate"
          class="w-full px-4 py-3 flex items-center justify-between active:bg-gray-50 text-left">
          <span class="text-[13px]" style="color: var(--color-accent); font-weight: 500;">检查更新</span>
          <span class="text-[11px]" style="color: var(--color-ink-3);">{{ bundleStatus }}</span>
        </button>
      </div>

      <!-- 退出 -->
      <div class="bg-white rounded-2xl overflow-hidden">
        <button
          @click="handleLogout"
          class="w-full flex items-center gap-3 px-4 py-4 active:bg-gray-50 text-left"
        >
          <div class="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </div>
          <span class="text-[#EF4444] font-medium">退出登录</span>
        </button>
      </div>
    </div>
  </div>
</template>
