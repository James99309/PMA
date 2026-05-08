<script setup>
// 名片识别核对页 — 显示 OCR 字段, 用户编辑确认 → 重复检测 → 创建客户+联系人
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCardScanStore } from '@/stores/cardScan'
import { createCustomer, addContact, checkContactDuplicate } from '@/api/customers'

const router = useRouter()
const scanStore = useCardScanStore()

// 字段编辑状态
const form = ref({
  name: '',
  company: '',
  position: '',
  department: '',
  phone: '',
  email: '',
  address: '',
})
const confidence = ref({})
const saving = ref(false)
const error = ref('')

// 重复检测对话框
const showDupDialog = ref(false)
const duplicates = ref([])

onMounted(() => {
  if (!scanStore.fields || !Object.keys(scanStore.fields).length) {
    // 直接到这页 (没经过 capture) → 退回
    router.replace('/customers')
    return
  }
  const f = scanStore.fields
  form.value = {
    name:       f.name       || '',
    company:    f.company    || '',
    position:   f.position   || '',
    department: f.department || '',
    phone:      f.phone      || '',
    email:      f.email      || '',
    address:    f.address    || '',
  }
  confidence.value = scanStore.confidence || {}
})

// 字段视觉提示: 0.9+ 正常, 0.7-0.9 黄, <0.7 黄+图标
function fieldStyle(key) {
  const c = confidence.value[key]
  if (c == null || c >= 0.9) return { borderColor: 'var(--color-divider)' }
  if (c >= 0.7) return { borderColor: '#F0E1A8', background: '#FBF5E5' }
  return { borderColor: '#E8C588', background: '#F9F1E6' }
}
function fieldWarn(key) {
  const c = confidence.value[key]
  return c != null && c < 0.7
}

const canSave = computed(() => form.value.name.trim() && form.value.company.trim())

async function tryStartSave() {
  error.value = ''
  if (!canSave.value) {
    error.value = '姓名和公司名为必填'
    return
  }
  // 重复检测
  if (form.value.phone || form.value.email) {
    try {
      const res = await checkContactDuplicate(form.value.phone, form.value.email)
      const dups = res.data?.data?.duplicates || []
      if (dups.length) {
        duplicates.value = dups
        showDupDialog.value = true
        return
      }
    } catch {
      // 检测失败也不阻塞用户
    }
  }
  await doSave()
}

async function doSave() {
  saving.value = true
  error.value = ''
  showDupDialog.value = false
  try {
    // 1) 创建客户
    const cRes = await createCustomer({
      name: form.value.company.trim(),
      address: form.value.address || undefined,
    })
    const cd = cRes.data
    if (!cd?.success || !cd?.data?.id) {
      error.value = cd?.message || '客户创建失败'
      saving.value = false
      return
    }
    const companyId = cd.data.id
    // 2) 创建联系人 (带名片图 URL + OCR JSON)
    const contRes = await addContact(companyId, {
      name: form.value.name.trim(),
      position: form.value.position || undefined,
      department: form.value.department || undefined,
      phone: form.value.phone || undefined,
      email: form.value.email || undefined,
      business_card_image_url: scanStore.fileUrl || undefined,
      ocr_json_data: scanStore.ocrJson || undefined,
    })
    const td = contRes.data
    if (!td?.success) {
      error.value = td?.message || '联系人保存失败'
      saving.value = false
      return
    }
    // 成功 → 清存储, 跳客户详情
    scanStore.clear()
    router.replace(`/customers/${companyId}`)
  } catch (e) {
    error.value = `保存失败: ${e?.message || e}`
    saving.value = false
  }
}

function onCancel() {
  scanStore.clear()
  router.back()
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">
    <!-- Nav -->
    <div class="flex items-center justify-between px-4 py-3 shrink-0"
      style="background: var(--color-card); border-bottom: 1px solid var(--color-divider);">
      <button @click="onCancel" class="text-[14px] active:opacity-70" style="color: var(--color-ink-2);">取消</button>
      <span class="font-serif text-[16px] font-medium">核对名片信息</span>
      <button @click="tryStartSave" :disabled="!canSave || saving"
        class="text-[14px] font-semibold active:opacity-70 disabled:opacity-40"
        style="color: var(--color-accent);">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      <!-- 名片缩略 -->
      <div v-if="scanStore.cropDataUrl" class="rounded-xl overflow-hidden"
        style="border: 1px solid var(--color-divider);">
        <img :src="scanStore.cropDataUrl" class="w-full block" style="max-height: 200px; object-fit: contain; background: #000;" />
        <div class="px-3 py-2 text-[11px]" style="background: var(--color-card); color: var(--color-ink-3);">
          AI 已识别 · 黄色字段建议核对
        </div>
      </div>

      <!-- 必填: 姓名 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('name') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">姓名 *</span>
          <span v-if="fieldWarn('name')" class="text-[10px]" style="color: #C77B22;">⚠ 请检查</span>
        </div>
        <input v-model="form.name" type="text" placeholder="联系人姓名"
          class="w-full text-[15px] outline-none bg-transparent"
          style="color: var(--color-ink);" />
      </div>

      <!-- 必填: 公司 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('company') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">公司 *</span>
          <span v-if="fieldWarn('company')" class="text-[10px]" style="color: #C77B22;">⚠ 请检查</span>
        </div>
        <input v-model="form.company" type="text" placeholder="公司名"
          class="w-full text-[15px] outline-none bg-transparent"
          style="color: var(--color-ink);" />
      </div>

      <!-- 职位 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('position') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">职位</span>
          <span v-if="fieldWarn('position')" class="text-[10px]" style="color: #C77B22;">⚠</span>
        </div>
        <input v-model="form.position" type="text" placeholder="（可选）"
          class="w-full text-[15px] outline-none bg-transparent"
          style="color: var(--color-ink);" />
      </div>

      <!-- 部门 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('department') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">部门</span>
          <span v-if="fieldWarn('department')" class="text-[10px]" style="color: #C77B22;">⚠</span>
        </div>
        <input v-model="form.department" type="text" placeholder="（可选）"
          class="w-full text-[15px] outline-none bg-transparent"
          style="color: var(--color-ink);" />
      </div>

      <!-- 电话 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('phone') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">电话</span>
          <span v-if="fieldWarn('phone')" class="text-[10px]" style="color: #C77B22;">⚠ 请检查</span>
        </div>
        <input v-model="form.phone" type="tel" placeholder="（可选）"
          class="w-full text-[15px] outline-none bg-transparent tabular"
          style="color: var(--color-ink);" />
      </div>

      <!-- 邮箱 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('email') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">邮箱</span>
          <span v-if="fieldWarn('email')" class="text-[10px]" style="color: #C77B22;">⚠ 请检查</span>
        </div>
        <input v-model="form.email" type="email" placeholder="（可选）"
          class="w-full text-[15px] outline-none bg-transparent tabular"
          style="color: var(--color-ink);" />
      </div>

      <!-- 公司地址 -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...fieldStyle('address') }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">公司地址</span>
          <span v-if="fieldWarn('address')" class="text-[10px]" style="color: #C77B22;">⚠</span>
        </div>
        <textarea v-model="form.address" placeholder="（可选）" rows="2"
          class="w-full text-[14px] outline-none bg-transparent resize-none"
          style="color: var(--color-ink); line-height: 1.45;"></textarea>
      </div>

      <p v-if="error" class="text-[12px] text-center" style="color: #C44;">{{ error }}</p>
    </div>

    <!-- 重复检测 dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showDupDialog" class="fixed inset-0 z-50 flex items-center justify-center px-6">
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.4);"
            @click="showDupDialog = false" />
          <div class="relative bg-white rounded-2xl px-5 py-5 w-full"
            style="max-width: 360px;">
            <div class="text-center">
              <div class="text-[32px] mb-1">⚠️</div>
              <p class="font-serif text-[17px] font-semibold mb-1" style="color: var(--color-ink);">
                可能已有该联系人
              </p>
              <p class="text-[12.5px] leading-relaxed" style="color: var(--color-ink-3);">
                找到 {{ duplicates.length }} 条电话/邮箱命中, 仍要新建吗?
              </p>
            </div>
            <div class="mt-3 space-y-2 max-h-[180px] overflow-y-auto">
              <div v-for="d in duplicates" :key="d.contact_id"
                class="rounded-xl px-3 py-2 text-[12.5px]"
                style="background: var(--color-bg); border: 1px solid var(--color-divider);">
                <div class="font-medium" style="color: var(--color-ink);">{{ d.name }}</div>
                <div class="mt-0.5" style="color: var(--color-ink-3);">
                  {{ d.company_name }}<span v-if="d.phone"> · {{ d.phone }}</span>
                </div>
              </div>
            </div>
            <div class="flex gap-2 mt-4">
              <button @click="showDupDialog = false"
                class="flex-1 py-3 rounded-xl text-[14px]"
                style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">
                返回核对
              </button>
              <button @click="doSave"
                class="flex-1 py-3 rounded-xl text-[14px] font-semibold text-white"
                style="background: var(--color-accent);">
                仍然新建
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
