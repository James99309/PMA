<script setup>
// 名片扫描保存成功页 (设计稿 ScanSuccess)
// 显示: ✓ + 联系人卡 + 名片图 + 3 快捷动作 + 双 CTA (继续拍 / 去详情)
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { useCardScanStore } from '@/stores/cardScan'

const router = useRouter()
const scanStore = useCardScanStore()
const r = computed(() => scanStore.saveResult)

const showCard = ref(false)

onMounted(() => {
  // 没有 saveResult 直接到这页 (刷新/直访) → 跳客户列表
  if (!scanStore.saveResult) {
    router.replace('/customers')
  }
})

// 名片原图带 token 的全 URL
const cardImageFullUrl = computed(() => {
  const u = r.value?.fileUrl
  if (!u) return ''
  if (/^https?:\/\//.test(u)) return u
  const baseHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
  const token = localStorage.getItem('access_token') || ''
  const sep = u.includes('?') ? '&' : '?'
  return `${baseHost}${u}${sep}token=${encodeURIComponent(token)}`
})

// 副标文字: 跟客户的关系
const subtitle = computed(() => {
  const x = r.value
  if (!x) return ''
  if (x.mergeMode === 'merge')  return `${x.contactName} 已合并到 ${x.companyName}`
  if (x.mergeMode === 'attach') return `${x.contactName} 已加到 ${x.companyName}`
  return `${x.contactName} 已加入新客户 ${x.companyName}`
})

const dateStr = computed(() => {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
})

// 3 快捷动作
function callPhone() {
  if (r.value?.phone) window.open(`tel:${r.value.phone}`)
}
function sendEmail() {
  if (r.value?.email) window.open(`mailto:${r.value.email}`)
}
function gotoProjects() {
  // "加入项目" — 当前 PMA 没有 contact 直接关联到 project 的接口,
  // 暂时跳到项目列表让用户人工挑 (后续如果加 API 再接)
  router.push('/projects')
}

// 双 CTA
function continueScan() {
  // 保留 attachTo 状态, 重新进取景
  const attachTo = scanStore.attachToCompanyId
  scanStore.resetForNextScan()
  if (attachTo) {
    router.replace({ path: '/customers/scan',
      query: { attachTo, attachToName: scanStore.attachToCompanyName || '' } })
  } else {
    router.replace('/customers/scan')
  }
}
function gotoDetail() {
  const x = r.value
  if (!x) { router.replace('/customers'); return }
  scanStore.clear()
  router.replace(`/customers/${x.companyId}/contacts/${x.contactId}`)
}
function close() {
  scanStore.clear()
  router.replace('/customers')
}
</script>

<template>
  <div v-if="r" class="flex flex-col h-full" style="background: var(--color-bg);">
    <!-- 顶部 X 关闭 -->
    <div class="flex items-center justify-end px-4 py-3 shrink-0">
      <button @click="close" class="w-9 h-9 rounded-full inline-flex items-center justify-center active:opacity-70"
        style="font-size: 20px; color: var(--color-ink-3); background: var(--color-card); border: 1px solid var(--color-divider);">
        ×
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-4 pb-32">
      <!-- 大对勾 + 标题 -->
      <div class="flex flex-col items-center mt-4 mb-6">
        <div class="w-20 h-20 rounded-full inline-flex items-center justify-center"
          style="background: var(--color-accent);">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
            <path d="M9 18l6 6 12-14" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h2 class="font-serif mt-4" style="font-size: 22px; color: var(--color-ink); letter-spacing: -0.3px;">已添加联系人</h2>
        <p class="text-[13px] mt-1.5 text-center px-4" style="color: var(--color-ink-2); line-height: 1.5;">
          {{ subtitle }}
        </p>
        <p class="text-[12px] mt-1" style="color: var(--color-ink-3);">
          {{ r.fieldCount || 0 }} 个字段已保存
        </p>
      </div>

      <!-- 联系人卡 -->
      <div class="bg-white rounded-2xl px-4 py-4 mb-3"
        style="border: 1px solid var(--color-divider);">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full inline-flex items-center justify-center font-serif font-semibold text-[20px] shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            {{ r.contactName?.[0] || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="font-serif text-[16px] font-medium" style="color: var(--color-ink);">{{ r.contactName }}</span>
              <span class="text-[10px] font-bold px-1.5 py-px rounded"
                style="color: #2F7A4F; background: #E9F1EB;">新</span>
            </div>
            <p class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
              {{ r.position ? r.position + ' · ' : '' }}{{ r.companyName }}
            </p>
          </div>
        </div>

        <!-- 名片原图 chip -->
        <div v-if="r.fileUrl"
          @click="showCard = true"
          class="mt-3 flex items-center gap-3 px-3 py-2.5 rounded-xl active:opacity-80 cursor-pointer"
          style="background: var(--color-bg); border: 1px solid var(--color-divider);">
          <img :src="cardImageFullUrl" class="w-12 h-9 object-cover rounded shrink-0"
            style="background: #fff;" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
                style="color: var(--color-ink-2);">
                <rect x="3" y="6" width="18" height="13" rx="2" stroke-linejoin="round" />
                <circle cx="12" cy="12.5" r="3.5" />
              </svg>
              <span class="text-[13px] font-medium" style="color: var(--color-ink);">名片原图</span>
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
              {{ dateStr }} · 1 张
            </div>
          </div>
          <span style="font-size: 12px; color: var(--color-accent); font-weight: 500;">查看 ›</span>
        </div>
      </div>

      <!-- 3 快捷动作 -->
      <div class="bg-white rounded-2xl overflow-hidden mb-3"
        style="border: 1px solid var(--color-divider);">
        <div class="flex">
          <button @click="sendEmail" :disabled="!r.email"
            class="flex-1 py-4 flex flex-col items-center gap-1.5 active:bg-gray-50 disabled:opacity-40">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
              style="color: var(--color-accent);">
              <rect x="2" y="5" width="20" height="14" rx="2" stroke-linejoin="round" />
              <path d="M2 7l10 7 10-7" stroke-linejoin="round" />
            </svg>
            <span class="text-[12px]" style="color: var(--color-ink-2);">发邮件</span>
          </button>
          <div style="width: 1px; background: var(--color-divider);"></div>
          <button @click="callPhone" :disabled="!r.phone"
            class="flex-1 py-4 flex flex-col items-center gap-1.5 active:bg-gray-50 disabled:opacity-40">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
              style="color: var(--color-accent);">
              <path d="M5 4l3 4-2 2a8 8 0 005 5l2-2 4 3-2 2c-1 1-2.5 1-4 0-3.5-2-6.5-5-8.5-8.5-1-1.5-1-3 0-4l3-1.5z"
                stroke-linejoin="round" />
            </svg>
            <span class="text-[12px]" style="color: var(--color-ink-2);">拨电话</span>
          </button>
          <div style="width: 1px; background: var(--color-divider);"></div>
          <button @click="gotoProjects"
            class="flex-1 py-4 flex flex-col items-center gap-1.5 active:bg-gray-50">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
              style="color: var(--color-accent);">
              <path d="M3 5a2 2 0 012-2h4l2 2h6a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V5z" stroke-linejoin="round" />
            </svg>
            <span class="text-[12px]" style="color: var(--color-ink-2);">加入项目</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 底部双 CTA -->
    <div class="px-4 pt-3 shrink-0"
      style="background: var(--color-card); border-top: 1px solid var(--color-divider); padding-bottom: calc(env(safe-area-inset-bottom) + 14px);">
      <div class="flex gap-2.5">
        <button @click="continueScan"
          class="flex-1 py-3.5 rounded-xl active:opacity-70"
          style="background: var(--color-bg); border: 1px solid var(--color-divider-strong); font-size: 14.5px; color: var(--color-ink-2); font-weight: 500;">
          📷 继续拍下一张
        </button>
        <button @click="gotoDetail"
          class="rounded-xl text-white font-semibold active:opacity-70"
          style="flex: 1.2; padding: 14px 0; background: var(--color-ink); font-size: 14.5px;">
          去详情页 ›
        </button>
      </div>
    </div>

    <!-- 名片全屏 lightbox -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCard && cardImageFullUrl" class="fixed inset-0 z-50 flex items-center justify-center"
          style="background: rgba(0,0,0,0.92);" @click="showCard = false">
          <button class="absolute top-3 right-3 w-10 h-10 rounded-full inline-flex items-center justify-center"
            style="background: rgba(255,255,255,0.15); color: #fff; font-size: 22px; font-weight: 200;"
            @click.stop="showCard = false">×</button>
          <img :src="cardImageFullUrl" class="block"
            style="max-width: 95vw; max-height: 80vh; object-fit: contain;" />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
