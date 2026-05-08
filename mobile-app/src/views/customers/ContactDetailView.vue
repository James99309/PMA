<script setup>
// 联系人详情页 — /customers/:cid/contacts/:contactId
// 基础信息 + 名片图 (带 ?token= 鉴权) + 拨打/邮件快捷键
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/api/client'
import NavBar from '@/components/common/NavBar.vue'

const route = useRoute()
const router = useRouter()

const contact = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  try {
    const id = route.params.contactId
    const res = await client.get(`/mobile/contacts/${id}`)
    if (res.data?.success) {
      contact.value = res.data.data
    } else {
      error.value = res.data?.message || '加载失败'
    }
  } catch (e) {
    error.value = e?.message || '网络错误'
  } finally {
    loading.value = false
  }
}

onMounted(load)

// 名片图 URL 注入 ?token= (跟客户详情同款)
const cardImageFullUrl = computed(() => {
  const u = contact.value?.business_card_image_url
  if (!u) return ''
  if (/^https?:\/\//.test(u)) return u
  const baseHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
  const token = localStorage.getItem('access_token') || ''
  const sep = u.includes('?') ? '&' : '?'
  return `${baseHost}${u}${sep}token=${encodeURIComponent(token)}`
})

const showCard = ref(false)
function callPhone() { if (contact.value?.phone) window.open(`tel:${contact.value.phone}`) }
function sendEmail() { if (contact.value?.email) window.open(`mailto:${contact.value.email}`) }
function backToCustomer() {
  const cid = route.params.cid
  if (cid) router.replace(`/customers/${cid}`)
  else router.back()
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">
    <NavBar :title="contact?.name || '联系人'" :show-back="true" />

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>
    <div v-else-if="error" class="flex-1 flex items-center justify-center px-6 text-center">
      <div>
        <p style="color: #C44; font-size: 13px;">{{ error }}</p>
        <button @click="router.back()"
          class="mt-4 px-5 py-2 rounded-full text-[13px]"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">返回</button>
      </div>
    </div>

    <div v-else-if="contact" class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      <!-- 头像 + 姓名卡 -->
      <div class="bg-white rounded-2xl px-4 py-4 flex items-center gap-3.5"
        style="border: 1px solid var(--color-divider);">
        <div class="w-14 h-14 rounded-full inline-flex items-center justify-center font-serif font-semibold text-[22px] shrink-0"
          style="background: var(--color-accent-soft); color: var(--color-accent);">
          {{ contact.name?.[0] || '?' }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-baseline gap-1.5">
            <p class="font-serif text-[18px]" style="color: var(--color-ink); letter-spacing: -0.2px;">{{ contact.name }}</p>
            <span v-if="contact.is_primary" class="text-[10px] font-bold px-1.5 py-px rounded"
              style="background: var(--color-accent); color: #fff;">主要</span>
            <span v-if="contact.business_card_image_url"
              @click="showCard = true"
              class="text-[10px] font-bold px-1.5 py-px rounded inline-flex items-center gap-0.5 active:opacity-70"
              style="color: var(--color-accent); background: var(--color-accent-soft);">
              📇 名片
            </span>
          </div>
          <p class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
            {{ [contact.position, contact.department].filter(Boolean).join(' · ') || '—' }}
          </p>
          <p class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
            {{ contact.company_name }}
          </p>
        </div>
      </div>

      <!-- 联系方式 -->
      <div class="bg-white rounded-2xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-2.5"
          style="border-bottom: 1px solid var(--color-divider);">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">联系方式</span>
        </div>
        <button v-if="contact.phone" @click="callPhone"
          class="w-full px-4 py-3.5 flex items-center gap-3 active:bg-gray-50 text-left"
          style="border-bottom: 1px solid var(--color-divider);">
          <div class="w-8 h-8 rounded-full inline-flex items-center justify-center shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
                fill="currentColor" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[11px]" style="color: var(--color-ink-3);">电话</div>
            <div class="tabular text-[14px] font-medium" style="color: var(--color-ink);">{{ contact.phone }}</div>
          </div>
          <span style="font-size: 11px; color: var(--color-accent);">点击拨打</span>
        </button>
        <button v-if="contact.email" @click="sendEmail"
          class="w-full px-4 py-3.5 flex items-center gap-3 active:bg-gray-50 text-left"
          :style="contact.phone ? '' : ''">
          <div class="w-8 h-8 rounded-full inline-flex items-center justify-center shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="3" width="12" height="8" rx="1" stroke="currentColor" stroke-width="1.4" />
              <path d="M1 4l6 4 6-4" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[11px]" style="color: var(--color-ink-3);">邮箱</div>
            <div class="text-[13px] font-medium truncate" style="color: var(--color-ink);">{{ contact.email }}</div>
          </div>
          <span style="font-size: 11px; color: var(--color-accent);">发邮件</span>
        </button>
        <div v-if="!contact.phone && !contact.email"
          class="px-4 py-4 text-center text-[12px]" style="color: var(--color-ink-3);">
          无电话/邮箱
        </div>
      </div>

      <!-- 备注 -->
      <div v-if="contact.notes" class="bg-white rounded-2xl px-4 py-3"
        style="border: 1px solid var(--color-divider);">
        <div class="text-[11px] font-semibold uppercase mb-2"
          style="color: var(--color-ink-3); letter-spacing: 0.6px;">备注</div>
        <p class="text-[13px]" style="color: var(--color-ink-2); line-height: 1.55; white-space: pre-wrap;">{{ contact.notes }}</p>
      </div>

      <!-- 名片缩略 (有就显示) -->
      <div v-if="contact.business_card_image_url" class="bg-white rounded-2xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-2.5"
          style="border-bottom: 1px solid var(--color-divider);">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">名片原图</span>
        </div>
        <button @click="showCard = true" class="block w-full active:opacity-80">
          <img :src="cardImageFullUrl" class="w-full block"
            style="max-height: 240px; object-fit: contain; background: var(--color-bg);" />
        </button>
      </div>

      <!-- 返回客户 -->
      <button @click="backToCustomer"
        class="w-full py-3 rounded-2xl active:opacity-70"
        style="background: white; border: 1px solid var(--color-divider-strong); font-size: 14px; color: var(--color-ink-2); font-weight: 500;">
        返回客户「{{ contact.company_name }}」
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
