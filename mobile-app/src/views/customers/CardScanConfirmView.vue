<script setup>
// 名片识别核对页 — 显示 OCR 字段, 用户编辑确认 → 重复检测 → 创建客户+联系人
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCardScanStore } from '@/stores/cardScan'
import { createCustomer, addContact, checkContactDuplicate, mergeContactFromCard, checkCustomerName } from '@/api/customers'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()

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

// 重复检测: 联系人级 (phone/email)
const showDupDialog = ref(false)
const duplicates = ref([])

// 重复检测: 公司级 (公司名 fuzzy 命中) — attachTo 模式下不需要
const showCompanyDupDialog = ref(false)
const companyDuplicates = ref([])

// attachTo 模式: 直接挂联系人到指定客户, 不新建公司
const isAttachMode = computed(() => !!scanStore.attachToCompanyId)

onMounted(() => {
  if (!scanStore.fields || !Object.keys(scanStore.fields).length) {
    // 直接到这页 (没经过 capture) → 退回
    router.replace('/customers')
    return
  }
  const f = scanStore.fields
  form.value = {
    name:       f.name       || '',
    // attachTo 模式: 公司名锁定为目标客户名 (OCR 出的公司名忽略)
    company:    scanStore.attachToCompanyId ? scanStore.attachToCompanyName : (f.company || ''),
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

const canSave = computed(() => {
  if (!form.value.name.trim()) return false
  // attachTo 模式: 公司用 scanStore.attachToCompanyId 决定, 不靠 form.company 判断
  if (isAttachMode.value) return true
  return !!form.value.company.trim()
})

async function tryStartSave() {
  error.value = ''
  if (!canSave.value) {
    error.value = '姓名和公司名为必填'
    return
  }
  // 联系人级重复检测 (phone/email 命中) — attachTo 模式也查, 让用户避免重复
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
  // 公司级重复检测: 仅"新建客户"路径才查 (attachTo 已指定客户, 跳过)
  if (!isAttachMode.value) {
    try {
      const res = await checkCustomerName(form.value.company.trim())
      // 后端返回 data.similar: [{id, name, score}], 0.6+ 相似度
      const similar = res.data?.data?.similar || []
      // 仅 score >= 70 视为强匹配, 60-70 不打扰
      const strong = similar.filter(x => (x.score || 0) >= 70)
      if (strong.length) {
        companyDuplicates.value = strong.slice(0, 5)
        showCompanyDupDialog.value = true
        return
      }
    } catch {
      // ignore, 继续保存
    }
  }
  await doSave()
}

// 公司级合并: 用户选了某个已有客户 → 直接 addContact 到那个公司
async function mergeToExistingCompany(c) {
  if (saving.value) return
  saving.value = true
  error.value = ''
  showCompanyDupDialog.value = false
  try {
    const res = await addContact(c.id || c.company_id, {
      name: form.value.name.trim(),
      position: form.value.position || undefined,
      department: form.value.department || undefined,
      phone: form.value.phone || undefined,
      email: form.value.email || undefined,
      business_card_image_url: scanStore.fileUrl || undefined,
      ocr_json_data: scanStore.ocrJson || undefined,
    })
    const td = res.data
    if (!td?.success) {
      error.value = td?.message || '保存失败'
      saving.value = false
      return
    }
    scanStore.clear()
    router.replace(`/customers/${c.id || c.company_id}`)
  } catch (e) {
    error.value = `保存失败: ${e?.message || e}`
    saving.value = false
  }
}

async function doMerge(d) {
  if (saving.value) return
  saving.value = true
  error.value = ''
  showDupDialog.value = false
  try {
    const res = await mergeContactFromCard(d.contact_id, {
      position:   form.value.position   || undefined,
      department: form.value.department || undefined,
      phone:      form.value.phone      || undefined,
      email:      form.value.email      || undefined,
      business_card_image_url: scanStore.fileUrl || undefined,
      ocr_json_data: scanStore.ocrJson || undefined,
    })
    const rd = res.data
    if (!rd?.success) {
      error.value = rd?.message || '合并失败'
      saving.value = false
      return
    }
    scanStore.clear()
    router.replace(`/customers/${d.company_id}`)
  } catch (e) {
    error.value = `合并失败: ${e?.message || e}`
    saving.value = false
  }
}

async function doSave() {
  saving.value = true
  error.value = ''
  showDupDialog.value = false
  showCompanyDupDialog.value = false
  try {
    // attachTo 模式: 直接给指定客户加联系人, 不新建客户
    let companyId = scanStore.attachToCompanyId
    if (!companyId) {
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
      companyId = cd.data.id
    }
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
  <div class="flex flex-col h-full" :style="[{ background: 'var(--color-bg)' }, kbStyle]">
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

      <!-- 必填: 公司 (attachTo 模式下锁定为目标客户) -->
      <div class="bg-white rounded-2xl px-4 py-3"
        :style="{ border: '1px solid', ...(isAttachMode ? { borderColor: 'var(--color-divider)' } : fieldStyle('company')) }">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[11px] font-semibold uppercase" style="color: var(--color-ink-3); letter-spacing: 0.6px;">
            公司 *<span v-if="isAttachMode" class="ml-1.5 text-[9px] font-bold px-1.5 py-px rounded"
              style="color: var(--color-accent); background: var(--color-accent-soft); letter-spacing: 0.3px;">已挂到当前客户</span>
          </span>
          <span v-if="!isAttachMode && fieldWarn('company')" class="text-[10px]" style="color: #C77B22;">⚠ 请检查</span>
        </div>
        <input v-model="form.company" type="text" placeholder="公司名"
          :readonly="isAttachMode"
          class="w-full text-[15px] outline-none bg-transparent"
          :style="{ color: isAttachMode ? 'var(--color-ink-2)' : 'var(--color-ink)' }" />
        <p v-if="isAttachMode" class="text-[11px] mt-1" style="color: var(--color-ink-3);">
          联系人会直接加到这个客户下, OCR 识到的"{{ scanStore.fields?.company }}"忽略
        </p>
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
            <div class="mt-3 space-y-2 max-h-[220px] overflow-y-auto">
              <div v-for="d in duplicates" :key="d.contact_id"
                class="rounded-xl px-3 py-2.5 flex items-center gap-2"
                style="background: var(--color-bg); border: 1px solid var(--color-divider);">
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-[12.5px]" style="color: var(--color-ink);">{{ d.name }}</div>
                  <div class="mt-0.5 text-[11.5px] truncate" style="color: var(--color-ink-3);">
                    {{ d.company_name }}<span v-if="d.phone"> · {{ d.phone }}</span>
                  </div>
                </div>
                <button @click="doMerge(d)" :disabled="saving"
                  class="shrink-0 px-3 py-1.5 rounded-full text-[11.5px] font-semibold active:opacity-70 disabled:opacity-40"
                  style="background: var(--color-accent); color: #fff;">
                  合并 →
                </button>
              </div>
            </div>
            <p class="mt-2 px-1 text-[11px]" style="color: var(--color-ink-3); line-height: 1.5;">
              合并: 把这次扫到的字段补进已有联系人 (不覆盖非空), 并更新名片图。
            </p>
            <div class="flex gap-2 mt-3">
              <button @click="showDupDialog = false" :disabled="saving"
                class="flex-1 py-3 rounded-xl text-[14px] disabled:opacity-40"
                style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">
                返回核对
              </button>
              <button @click="doSave" :disabled="saving"
                class="flex-1 py-3 rounded-xl text-[14px] font-semibold text-white disabled:opacity-40"
                style="background: var(--color-ink);">
                新建独立
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 公司级重复 dialog: 公司名命中已有客户 → 推荐合并到那个客户 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCompanyDupDialog" class="fixed inset-0 z-50 flex items-end justify-center">
          <div class="absolute inset-0" style="background: rgba(20,20,20,0.42);"
            @click="showCompanyDupDialog = false" />
          <div class="relative w-full pb-7"
            style="background: var(--color-card); border-top-left-radius: 20px; border-top-right-radius: 20px; max-width: 100%;">
            <div class="mx-auto" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin: 10px auto 4px;"></div>

            <!-- 标题 -->
            <div class="px-5 pt-3 pb-1 flex items-center gap-2.5">
              <div class="shrink-0 inline-flex items-center justify-center"
                style="width: 36px; height: 36px; border-radius: 10px; background: #FBF1DF; border: 1px solid #F6E4BE;">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 1.5L17 15.5H1L9 1.5z" stroke="#B8762A" stroke-width="1.4" stroke-linejoin="round" />
                  <path d="M9 7v4M9 13v0.5" stroke="#B8762A" stroke-width="1.6" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-serif" style="font-size: 18px; color: var(--color-ink);">检测到重复客户</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
                  「{{ form.company }}」可能已存在
                </div>
              </div>
            </div>

            <!-- 推荐: 合并到现有客户列表 -->
            <div class="px-4 pt-3 pb-1 max-h-[320px] overflow-y-auto">
              <div v-for="(c, i) in companyDuplicates" :key="c.id || c.company_id || i"
                @click="mergeToExistingCompany(c)"
                class="rounded-xl px-3 py-3 mb-2 active:opacity-80 cursor-pointer"
                :style="{
                  background: i === 0 ? 'rgba(217,119,87,0.08)' : 'var(--color-card)',
                  border: i === 0 ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
                }">
                <div class="flex items-center gap-2.5">
                  <div class="shrink-0 inline-flex items-center justify-center"
                    :style="{
                      width: '22px', height: '22px', borderRadius: '11px',
                      background: i === 0 ? 'var(--color-accent)' : 'transparent',
                      border: i === 0 ? 'none' : '1.5px solid var(--color-ink-3)',
                      color: '#fff',
                    }">
                    <svg v-if="i === 0" width="10" height="10" viewBox="0 0 10 10">
                      <path d="M1 5l3 3 5-6" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline gap-1.5">
                      <span class="font-serif text-[15px] font-medium truncate" style="color: var(--color-ink);">{{ c.company_name || c.name }}</span>
                      <span v-if="i === 0" class="text-[10px] font-bold" style="color: var(--color-accent);">· 推荐</span>
                    </div>
                    <div class="text-[11.5px] mt-1" style="color: var(--color-ink-3);">
                      合并: {{ form.name }} 加入这家客户的联系人
                    </div>
                  </div>
                  <span style="font-size: 16px; color: var(--color-ink-3);">›</span>
                </div>
              </div>
            </div>

            <!-- 仍然新建 -->
            <div class="px-4 pt-2 pb-3"
              style="border-top: 1px solid var(--color-divider);">
              <button @click="doSave" :disabled="saving"
                class="w-full py-3 rounded-xl active:opacity-70 disabled:opacity-40"
                style="background: var(--color-card); border: 1px solid var(--color-divider-strong); font-size: 14px; color: var(--color-ink-2);">
                仍然新建独立客户
              </button>
              <button @click="showCompanyDupDialog = false" :disabled="saving"
                class="w-full mt-2 py-2 text-[13px] active:opacity-70 disabled:opacity-40"
                style="color: var(--color-ink-3);">
                返回核对
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
