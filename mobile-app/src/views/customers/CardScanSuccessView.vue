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

// 副标文字: 跟客户的关系 (公司名加粗)
const subtitleVerb = computed(() => {
  const x = r.value
  if (!x) return ''
  if (x.mergeMode === 'merge')  return '已合并到'
  if (x.mergeMode === 'attach') return '已加到'
  return '已加入新客户'
})

// 低置信度字段数 (置信度 <0.9, 由 ConfirmView countLowConfidence 计算后传入)
const lowConfidenceCount = computed(() => r.value?.lowConfidenceCount || 0)

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
  // 设计稿: 右 CTA 文案 "去客户详情 ›", 跳客户详情而非联系人详情
  const x = r.value
  if (!x) { router.replace('/customers'); return }
  scanStore.clear()
  router.replace(`/customers/${x.companyId}`)
}
function close() {
  scanStore.clear()
  router.replace('/customers')
}
</script>

<template>
  <div v-if="r" class="flex flex-col h-full" style="background: var(--color-bg); position: relative; overflow: hidden;">
    <!-- 顶部 NavBar (左空 / 中空 / 右 X) -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <span class="w-6"></span>
      <span class="font-serif text-[16px] font-medium"></span>
      <button @click="close" class="active:opacity-60 px-2"
        style="font-size: 22px; color: var(--color-ink); font-weight: 200;">×</button>
    </div>

    <div class="flex-1 overflow-y-auto pb-32">
      <!-- 大对勾 + 标题 + 副标 (设计稿: 76px + box-shadow) -->
      <div class="flex flex-col items-center px-6"
        style="padding-top: 20px; padding-bottom: 16px;">
        <div class="inline-flex items-center justify-center"
          style="width: 76px; height: 76px; border-radius: 38px; background: var(--color-accent);
                 box-shadow: 0 14px 32px rgba(217,119,87,0.20);">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
            <path d="M9 18l6 6 12-14" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <div class="font-serif" style="font-size: 24px; margin-top: 18px; color: var(--color-ink); letter-spacing: -0.3px;">
          已添加联系人
        </div>
        <div class="text-center" style="font-size: 13px; color: var(--color-ink-3); margin-top: 4px; line-height: 1.6;">
          {{ r.contactName }} {{ subtitleVerb }} <b style="color: var(--color-ink);">{{ r.companyName }}</b><br>
          <span style="color: var(--color-ink-4, #A8A29B);">
            {{ r.fieldCount || 0 }} 个字段已保存<template v-if="lowConfidenceCount > 0"> · {{ lowConfidenceCount }} 个待你后续核对</template>
          </span>
        </div>
      </div>

      <!-- 联系人卡 (含名片图 chip + 3 快捷动作, 全在一张卡里) -->
      <div class="bg-white overflow-hidden"
        style="margin: 24px 16px 16px; border-radius: 14px; border: 1px solid var(--color-divider);">
        <!-- 联系人 row -->
        <div class="flex items-center gap-3"
          style="padding: 16px 18px; border-bottom: 1px solid var(--color-divider);">
          <div class="rounded-full inline-flex items-center justify-center font-serif shrink-0"
            style="width: 44px; height: 44px; background: var(--color-accent); color: #fff; font-size: 18px;">
            {{ r.contactName?.[0] || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <div style="font-size: 15.5px; font-weight: 600; color: var(--color-ink);">{{ r.contactName }}</div>
            <div style="font-size: 12px; color: var(--color-ink-3); margin-top: 2px;">
              {{ r.position ? r.position + ' · ' : '' }}{{ r.companyName }}
            </div>
          </div>
          <span style="font-size: 11px; padding: 3px 7px; border-radius: 4px; background: #E9F1EB; color: #2F7A4F; font-weight: 600;">新</span>
        </div>

        <!-- 名片原图 chip row -->
        <div v-if="r.fileUrl" @click="showCard = true"
          class="flex items-center gap-3 active:opacity-80 cursor-pointer"
          style="padding: 12px 18px; border-bottom: 1px solid var(--color-divider);">
          <img :src="cardImageFullUrl" class="object-cover shrink-0"
            style="width: 56px; height: 36px; border-radius: 5px; border: 1px solid var(--color-divider); background: #fff;" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5" style="font-size: 12.5px; color: var(--color-ink-2);">
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                <rect x="1" y="3" width="10" height="7" rx="1" stroke="currentColor" stroke-width="1.1" />
                <path d="M4 3l1-1h2l1 1" stroke="currentColor" stroke-width="1.1" fill="none" />
                <circle cx="6" cy="6.5" r="1.6" stroke="currentColor" stroke-width="1.1" />
              </svg>
              名片原图
            </div>
            <div style="font-size: 11px; color: var(--color-ink-3); margin-top: 2px; font-variant-numeric: tabular-nums;">
              {{ dateStr }} · 1 张
            </div>
          </div>
          <span style="font-size: 12px; color: var(--color-accent); font-weight: 500;">查看 ›</span>
        </div>

        <!-- 3 快捷动作 row (设计稿: 12px 0 padding, right border 分隔, icon 16px) -->
        <div class="flex">
          <button @click="sendEmail" :disabled="!r.email"
            class="flex-1 flex flex-col items-center gap-1 active:bg-gray-50 disabled:opacity-40"
            style="padding: 12px 0; border-right: 1px solid var(--color-divider);">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="1.5" y="3.5" width="13" height="9" rx="1" stroke="var(--color-ink-2)" stroke-width="1.3" />
              <path d="M2 4l6 4 6-4" stroke="var(--color-ink-2)" stroke-width="1.3" stroke-linejoin="round" fill="none" />
            </svg>
            <span style="font-size: 12px; color: var(--color-ink-2);">发邮件</span>
          </button>
          <button @click="callPhone" :disabled="!r.phone"
            class="flex-1 flex flex-col items-center gap-1 active:bg-gray-50 disabled:opacity-40"
            style="padding: 12px 0; border-right: 1px solid var(--color-divider);">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 4a1 1 0 011-1h2l1 3-1.5 1a8 8 0 004 4l1-1.5 3 1v2a1 1 0 01-1 1A10 10 0 013 4z"
                stroke="var(--color-ink-2)" stroke-width="1.3" stroke-linejoin="round" fill="none" />
            </svg>
            <span style="font-size: 12px; color: var(--color-ink-2);">拨电话</span>
          </button>
          <button @click="gotoProjects"
            class="flex-1 flex flex-col items-center gap-1 active:bg-gray-50"
            style="padding: 12px 0;">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h12v8H2zM2 4l6 4 6-4" stroke="var(--color-ink-2)" stroke-width="1.3" stroke-linejoin="round" fill="none" />
            </svg>
            <span style="font-size: 12px; color: var(--color-ink-2);">加入项目</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 底部双 CTA (设计稿: 50px 高, 14px 圆角) -->
    <div class="absolute left-0 right-0 bottom-0 flex"
      style="padding: 16px 16px 28px; background: var(--color-bg); border-top: 1px solid var(--color-divider); gap: 10px;
             padding-bottom: calc(env(safe-area-inset-bottom) + 16px);">
      <button @click="continueScan"
        class="flex-1 inline-flex items-center justify-center gap-1.5 active:opacity-70"
        style="height: 50px; border-radius: 14px; background: #fff; border: 1px solid var(--color-divider-strong);
               color: var(--color-ink); font-size: 15px; font-weight: 600;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
          <rect x="3" y="6" width="18" height="13" rx="2" stroke-linejoin="round" />
          <circle cx="12" cy="12.5" r="3.5" />
          <path d="M9 6V5a1 1 0 011-1h4a1 1 0 011 1v1" stroke-linecap="round" />
        </svg>
        继续拍下一张
      </button>
      <button @click="gotoDetail"
        class="flex-1 active:opacity-70"
        style="height: 50px; border-radius: 14px; background: var(--color-ink); color: #fff; font-size: 15px; font-weight: 600;">
        去客户详情 ›
      </button>
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
