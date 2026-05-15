<script setup>
// 联系人详情页 — /customers/:cid/contacts/:contactId
// 顶部 NavBar: 返回 + ... 菜单 (编辑 / 删除)
// 下面: 头像卡 + 联系方式 + 备注 + 名片原图
// 编辑模式: 字段变成可编辑 input + 顶部右侧"保存"
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import client from '@/api/client'
import NavBar from '@/components/common/NavBar.vue'
import { getContact, updateContact, deleteContact } from '@/api/customers'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()
const { t } = useI18n()

const route = useRoute()
const router = useRouter()

const contact = ref(null)
const loading = ref(true)
const error = ref('')

// 编辑状态
const editMode = ref(false)
const editForm = ref({})
const saving = ref(false)

// 操作菜单
const showActions = ref(false)
const showDeleteConfirm = ref(false)
const deleting = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getContact(route.params.contactId)
    if (res.data?.success) {
      contact.value = res.data.data
    } else {
      error.value = res.data?.message || t('customer.loadFail')
    }
  } catch (e) {
    error.value = e?.message || t('customer.netError')
  } finally {
    loading.value = false
  }
}

onMounted(load)

// 名片图 URL 注入 ?token= 鉴权
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

// NavBar 事件
function onBack() { router.back() }
function onMore() { showActions.value = true }

// 编辑
function startEdit() {
  showActions.value = false
  editForm.value = {
    name: contact.value.name || '',
    position: contact.value.position || '',
    department: contact.value.department || '',
    phone: contact.value.phone || '',
    email: contact.value.email || '',
    notes: contact.value.notes || '',
  }
  editMode.value = true
}

function cancelEdit() {
  editMode.value = false
  editForm.value = {}
}

async function saveEdit() {
  if (!editForm.value.name?.trim()) {
    error.value = t('customer.nameRequired')
    return
  }
  saving.value = true
  error.value = ''
  try {
    const res = await updateContact(route.params.contactId, editForm.value)
    if (res.data?.success) {
      // 更新本地视图字段, 退出编辑模式
      const d = res.data.data
      contact.value = { ...contact.value, ...d }
      editMode.value = false
    } else {
      error.value = res.data?.message || t('customer.saveFail')
    }
  } catch (e) {
    error.value = e?.message || t('customer.saveFail')
  } finally {
    saving.value = false
  }
}

// 删除
function askDelete() {
  showActions.value = false
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  if (deleting.value) return
  deleting.value = true
  try {
    const res = await deleteContact(route.params.contactId)
    if (res.data?.success) {
      const cid = res.data.data?.company_id || route.params.cid
      router.replace(`/customers/${cid}`)
    } else {
      error.value = res.data?.message || t('customer.deleteFail')
      deleting.value = false
      showDeleteConfirm.value = false
    }
  } catch (e) {
    error.value = e?.message || t('customer.deleteFail')
    deleting.value = false
    showDeleteConfirm.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-full" :style="[{ background: 'var(--color-bg)' }, kbStyle]">
    <!-- 顶部 NavBar: 编辑模式时右侧改"保存", 默认 "..." 菜单 -->
    <NavBar :title="contact?.name || t('customer.contactHeader')" @back="editMode ? cancelEdit() : onBack()" @more="onMore">
      <template v-if="editMode" #left>
        <span style="color: var(--color-ink-2); font-size: 15px;">{{ t('common.cancel') }}</span>
      </template>
      <template v-if="editMode" #right>
        <button @click.stop="saveEdit" :disabled="saving"
          class="text-[15px] font-semibold active:opacity-70 disabled:opacity-40"
          style="color: var(--color-accent);">
          {{ saving ? t('customer.saving') : t('customer.save') }}
        </button>
      </template>
    </NavBar>

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>
    <div v-else-if="error && !contact" class="flex-1 flex items-center justify-center px-6 text-center">
      <p style="color: #C44; font-size: 13px;">{{ error }}</p>
    </div>

    <div v-else-if="contact" class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      <!-- 头像 + 姓名卡 -->
      <div class="bg-white rounded-2xl px-4 py-4 flex items-center gap-3.5"
        style="border: 1px solid var(--color-divider);">
        <div class="w-14 h-14 rounded-full inline-flex items-center justify-center font-serif font-semibold text-[22px] shrink-0"
          style="background: var(--color-accent-soft); color: var(--color-accent);">
          {{ (editMode ? editForm.name : contact.name)?.[0] || '?' }}
        </div>
        <div class="flex-1 min-w-0">
          <div v-if="!editMode" class="flex items-baseline gap-1.5">
            <p class="font-serif text-[18px]" style="color: var(--color-ink); letter-spacing: -0.2px;">{{ contact.name }}</p>
            <span v-if="contact.is_primary" class="text-[10px] font-bold px-1.5 py-px rounded"
              style="background: var(--color-accent); color: #fff;">{{ t('customer.primary') }}</span>
          </div>
          <input v-else v-model="editForm.name" type="text"
            class="font-serif text-[18px] w-full bg-transparent outline-none border-b"
            style="color: var(--color-ink); border-color: var(--color-divider); padding: 2px 0;"
            :placeholder="t('customer.fieldName')" />
          <p v-if="!editMode" class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
            {{ [contact.position, contact.department].filter(Boolean).join(' · ') || '—' }}
          </p>
          <p class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
            {{ contact.company_name }}
          </p>
        </div>
      </div>

      <!-- 编辑模式额外字段: 职位 / 部门 -->
      <div v-if="editMode" class="bg-white rounded-2xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
          <div class="text-[11px] font-semibold uppercase mb-1"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.cPosition') }}</div>
          <input v-model="editForm.position" type="text" :placeholder="t('customer.optional')"
            class="w-full text-[14px] outline-none bg-transparent" style="color: var(--color-ink);" />
        </div>
        <div class="px-4 py-3">
          <div class="text-[11px] font-semibold uppercase mb-1"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.cDepartment') }}</div>
          <input v-model="editForm.department" type="text" :placeholder="t('customer.optional')"
            class="w-full text-[14px] outline-none bg-transparent" style="color: var(--color-ink);" />
        </div>
      </div>

      <!-- 联系方式 -->
      <div class="bg-white rounded-2xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-2.5"
          style="border-bottom: 1px solid var(--color-divider);">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.contactWay') }}</span>
        </div>
        <!-- 电话 -->
        <div v-if="!editMode && contact.phone"
          @click="callPhone"
          class="px-4 py-3.5 flex items-center gap-3 active:bg-gray-50 cursor-pointer"
          style="border-bottom: 1px solid var(--color-divider);">
          <div class="w-8 h-8 rounded-full inline-flex items-center justify-center shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
                fill="currentColor" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[11px]" style="color: var(--color-ink-3);">{{ t('customer.cPhone') }}</div>
            <div class="tabular text-[14px] font-medium" style="color: var(--color-ink);">{{ contact.phone }}</div>
          </div>
          <span style="font-size: 11px; color: var(--color-accent);">{{ t('customer.tapCall') }}</span>
        </div>
        <div v-if="editMode" class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
          <div class="text-[11px] font-semibold uppercase mb-1"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.cPhone') }}</div>
          <input v-model="editForm.phone" type="tel" :placeholder="t('customer.optional')"
            class="w-full text-[14px] outline-none bg-transparent tabular" style="color: var(--color-ink);" />
        </div>
        <!-- 邮箱 -->
        <div v-if="!editMode && contact.email"
          @click="sendEmail"
          class="px-4 py-3.5 flex items-center gap-3 active:bg-gray-50 cursor-pointer">
          <div class="w-8 h-8 rounded-full inline-flex items-center justify-center shrink-0"
            style="background: var(--color-accent-soft); color: var(--color-accent);">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="3" width="12" height="8" rx="1" stroke="currentColor" stroke-width="1.4" />
              <path d="M1 4l6 4 6-4" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[11px]" style="color: var(--color-ink-3);">{{ t('customer.cEmail') }}</div>
            <div class="text-[13px] font-medium truncate" style="color: var(--color-ink);">{{ contact.email }}</div>
          </div>
          <span style="font-size: 11px; color: var(--color-accent);">{{ t('customer.sendMail') }}</span>
        </div>
        <div v-if="editMode" class="px-4 py-3">
          <div class="text-[11px] font-semibold uppercase mb-1"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.cEmail') }}</div>
          <input v-model="editForm.email" type="email" :placeholder="t('customer.optional')"
            class="w-full text-[14px] outline-none bg-transparent tabular" style="color: var(--color-ink);" />
        </div>
        <div v-if="!editMode && !contact.phone && !contact.email"
          class="px-4 py-4 text-center text-[12px]" style="color: var(--color-ink-3);">
          {{ t('customer.noPhoneEmail') }}
        </div>
      </div>

      <!-- 备注 -->
      <div v-if="!editMode && contact.notes" class="bg-white rounded-2xl px-4 py-3"
        style="border: 1px solid var(--color-divider);">
        <div class="text-[11px] font-semibold uppercase mb-2"
          style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.notes') }}</div>
        <p class="text-[13px]" style="color: var(--color-ink-2); line-height: 1.55; white-space: pre-wrap;">{{ contact.notes }}</p>
      </div>
      <div v-if="editMode" class="bg-white rounded-2xl px-4 py-3"
        style="border: 1px solid var(--color-divider);">
        <div class="text-[11px] font-semibold uppercase mb-1"
          style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.notes') }}</div>
        <textarea v-model="editForm.notes" :placeholder="t('customer.optional')" rows="3"
          class="w-full text-[14px] outline-none bg-transparent resize-none"
          style="color: var(--color-ink); line-height: 1.5;"></textarea>
      </div>

      <!-- 名片原图 (有就显示, 编辑模式也显示但只读) -->
      <div v-if="contact.business_card_image_url" class="bg-white rounded-2xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-2.5"
          style="border-bottom: 1px solid var(--color-divider);">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('customer.cardImage') }}</span>
        </div>
        <button @click="showCard = true" class="block w-full active:opacity-80">
          <img :src="cardImageFullUrl" class="w-full block"
            style="max-height: 240px; object-fit: contain; background: var(--color-bg);" />
        </button>
      </div>

      <p v-if="error" class="text-[12px] text-center pt-2" style="color: #C44;">{{ error }}</p>
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

    <!-- 顶部 ... 弹出: 编辑 / 删除 -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showActions" class="fixed inset-0 z-50">
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.4);"
            @click="showActions = false" />
          <div class="absolute left-0 right-0 bottom-0 pb-7 pt-2.5"
            style="background: var(--color-bg); border-top-left-radius: 18px; border-top-right-radius: 18px;">
            <div class="mx-auto" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin-bottom: 14px;"></div>
            <button @click="startEdit"
              class="w-full px-5 py-4 flex items-center gap-3 active:bg-gray-100 text-left"
              style="border-top: 1px solid var(--color-divider);">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
                style="color: var(--color-accent);">
                <path d="M12 20h9" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4L16.5 3.5z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span style="font-size: 15px; color: var(--color-ink);">{{ t('customer.editContact') }}</span>
            </button>
            <button @click="askDelete"
              class="w-full px-5 py-4 flex items-center gap-3 active:bg-gray-100 text-left"
              style="border-top: 1px solid var(--color-divider);">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
                style="color: #DC3545;">
                <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"
                  stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span style="font-size: 15px; color: #DC3545;">{{ t('customer.deleteContact') }}</span>
            </button>
            <button @click="showActions = false"
              class="w-full px-5 py-3.5 mt-2 active:bg-gray-100"
              style="background: var(--color-card); font-size: 15px; color: var(--color-ink-2); margin-top: 8px;">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 删除确认 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showDeleteConfirm" class="fixed inset-0 z-[60] flex items-center justify-center px-6">
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.4);"
            @click="showDeleteConfirm = false" />
          <div class="relative bg-white rounded-2xl px-6 py-5 w-full" style="max-width: 320px;">
            <div class="text-center">
              <div class="text-[36px] mb-1">⚠️</div>
              <p class="font-serif text-[17px] font-semibold mb-1" style="color: var(--color-ink);">
                {{ t('customer.deleteTitle', { name: contact?.name }) }}
              </p>
              <p class="text-[12.5px]" style="color: var(--color-ink-3); line-height: 1.55;">
                {{ t('customer.deleteHint') }}
              </p>
            </div>
            <div class="flex gap-2 mt-4">
              <button @click="showDeleteConfirm = false" :disabled="deleting"
                class="flex-1 py-3 rounded-xl text-[14px] disabled:opacity-40"
                style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">
                {{ t('common.cancel') }}
              </button>
              <button @click="confirmDelete" :disabled="deleting"
                class="flex-1 py-3 rounded-xl text-[14px] font-semibold text-white disabled:opacity-40"
                style="background: #DC3545;">
                {{ deleting ? t('customer.deleting') : t('customer.confirmDelete') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.sheet-enter-active, .sheet-leave-active { transition: opacity .18s ease, transform .22s ease; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-from > div:last-child, .sheet-leave-to > div:last-child { transform: translateY(20px); }
</style>
