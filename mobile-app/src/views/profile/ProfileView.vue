<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CapacitorUpdater } from '@capgo/capacitor-updater'
import { REGIONS } from '@/api/client'

const router = useRouter()
const auth = useAuthStore()

// Bundle 版本（Capgo 当前激活的）
const bundleId = ref('builtin')
const bundleVer = ref('-')
const bundleStatus = ref('')

// 区域切换 (Federation Lite) — 双 token 已在登录时自动并行获取, 切换零密码
const otherRegion = computed(() => {
  const otherId = auth.regionId === 'cn' ? 'sg' : 'cn'
  return REGIONS[otherId]
})
const showSwitchConfirm = ref(false)
const switchError = ref('')

function openSwitchConfirm() {
  switchError.value = ''
  showSwitchConfirm.value = true
}

function confirmSwitch() {
  if (auth.switchRegion(otherRegion.value.id)) {
    showSwitchConfirm.value = false
    router.go(0)   // reload to apply new token everywhere
  } else {
    switchError.value = `${otherRegion.value.label}系统未授权该账号，请联系 admin 设为「海外支持」`
  }
}

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
      bundleStatus.value = `下载完成，重启 App 生效`
      await CapacitorUpdater.set({ id: dl.id })
    } else {
      bundleStatus.value = '已是最新版本'
    }
  } catch (e) {
    // Capgo 在"无新版本"时也会抛 no_new_version_available 等错误码
    // 这些都视为"已是最新"，只对真实错误（网络/签名等）保留报错
    const msg = e?.message || String(e || '')
    const benign = ['no_new_version_available', 'no_channel', 'already_set']
    if (benign.some(k => msg.includes(k))) {
      bundleStatus.value = '已是最新版本'
    } else {
      bundleStatus.value = `检查失败: ${msg}`
    }
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

      <!-- 区域切换 (Federation Lite) — 左右分段控件, 当前橙色, 点对方切换 -->
      <div v-if="auth.hasOtherRegionToken"
        class="bg-white rounded-2xl overflow-hidden">
        <div class="px-4 pt-3 pb-2">
          <div class="text-[11px] font-semibold uppercase mb-2"
            style="color: var(--color-ink-3); letter-spacing: 1px;">区域</div>
          <div class="flex gap-2">
            <button v-for="r in [auth.region, otherRegion]" :key="r.id"
              @click="r.id === auth.regionId ? null : openSwitchConfirm()"
              :disabled="r.id === auth.regionId"
              class="flex-1 py-3 rounded-xl flex flex-col items-center gap-0.5 transition-all"
              :style="{
                background: r.id === auth.regionId ? 'var(--color-accent)' : 'var(--color-bg)',
                color: r.id === auth.regionId ? '#fff' : 'var(--color-ink-2)',
                border: r.id === auth.regionId ? 'none' : '1px solid var(--color-divider-strong)',
                cursor: r.id === auth.regionId ? 'default' : 'pointer',
              }">
              <span class="text-[22px] leading-none">{{ r.flag }}</span>
              <span class="text-[13px] font-semibold mt-0.5">{{ r.label }}</span>
              <span class="text-[10px] mt-0.5"
                :style="{ opacity: r.id === auth.regionId ? 0.85 : 0.6 }">
                {{ r.id === auth.regionId ? '当前' : '点击切换' }}
              </span>
            </button>
          </div>
        </div>
      </div>
      <!-- 单边账号 fallback -->
      <div v-else class="bg-white rounded-2xl overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between">
          <span class="text-[13px]" style="color: var(--color-ink-2);">当前区域</span>
          <span class="text-[13px] font-medium" style="color: var(--color-ink);">
            {{ auth.region.flag }} {{ auth.region.label }}
          </span>
        </div>
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

    <!-- 切换区域: 确认对话框 (无密码) -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showSwitchConfirm" class="fixed inset-0 z-50 flex items-center justify-center px-6">
          <div class="absolute inset-0 bg-black/40" @click="showSwitchConfirm = false" />
          <div class="relative bg-white rounded-2xl px-6 py-6 w-full"
            style="max-width: 340px;">
            <div class="text-center">
              <div class="text-[40px] mb-2">{{ otherRegion.flag }}</div>
              <p class="font-serif text-[18px] font-semibold mb-1" style="color: var(--color-ink);">
                切换到 {{ otherRegion.label }} 区域
              </p>
              <p class="text-[13px] leading-relaxed" style="color: var(--color-ink-3);">
                之后看到的客户、项目、报价等数据都来自<br>
                <b style="color: var(--color-ink);">{{ otherRegion.label }} 系统</b>
              </p>
            </div>
            <p v-if="switchError" class="text-[12px] mt-3 text-center" style="color: #C44;">
              {{ switchError }}
            </p>
            <div class="flex gap-2 mt-5">
              <button @click="showSwitchConfirm = false"
                class="flex-1 py-3 rounded-xl text-[14px]"
                style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">
                取消
              </button>
              <button @click="confirmSwitch"
                class="flex-1 py-3 rounded-xl text-[14px] font-semibold text-white"
                style="background: var(--color-accent);">
                确定切换
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
.sheet-enter-from, .sheet-leave-to       { opacity: 0; }
</style>
