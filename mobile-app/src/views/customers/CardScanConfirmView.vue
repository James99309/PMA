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
const dupChoice = ref('merge')         // 'merge' (合并到选中的) | 'new' (仍然新建)
const dupSelectedIdx = ref(0)          // 选中第几条 candidate (默认推荐 0)

// 重复检测: 公司级 (公司名 fuzzy 命中) — attachTo 模式下不需要
const showCompanyDupDialog = ref(false)
const companyDuplicates = ref([])
const companyDupChoice = ref('merge')
const companyDupSelectedIdx = ref(0)

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
        dupSelectedIdx.value = 0
        dupChoice.value = 'merge'
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
        companyDupSelectedIdx.value = 0
        companyDupChoice.value = 'merge'
        showCompanyDupDialog.value = true
        return
      }
    } catch {
      // ignore, 继续保存
    }
  }
  await doSave()
}

// dup sheet 确认按钮: 根据 radio 选择执行合并 or 新建
function confirmDupSheet() {
  if (dupChoice.value === 'merge') {
    const d = duplicates.value[dupSelectedIdx.value]
    if (d) doMerge(d)
  } else {
    doSave()
  }
}
function confirmCompanyDupSheet() {
  if (companyDupChoice.value === 'merge') {
    const c = companyDuplicates.value[companyDupSelectedIdx.value]
    if (c) mergeToExistingCompany(c)
  } else {
    doSave()
  }
}

// 公司级合并: 用户选了某个已有客户 → 直接 addContact 到那个公司
async function mergeToExistingCompany(c) {
  if (saving.value) return
  saving.value = true
  error.value = ''
  showCompanyDupDialog.value = false
  const companyId = c.id || c.company_id
  const companyName = c.name || c.company_name || form.value.company
  try {
    const res = await addContact(companyId, {
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
    scanStore.setSaveResult({
      contactId: td.data?.id,
      contactName: form.value.name.trim(),
      position: form.value.position,
      phone: form.value.phone,
      email: form.value.email,
      companyId,
      companyName,
      fileUrl: scanStore.fileUrl,
      fieldCount: countFilledFields(),
      lowConfidenceCount: countLowConfidence(),
      mergeMode: 'merge',
    })
    router.replace('/customers/scan/success')
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
    // 进成功页, 显示"合并到已有联系人"
    scanStore.setSaveResult({
      contactId: rd.data?.contact?.id || d.contact_id,
      contactName: rd.data?.contact?.name || d.name,
      position: form.value.position || rd.data?.contact?.position || '',
      phone: form.value.phone || rd.data?.contact?.phone || '',
      email: form.value.email || rd.data?.contact?.email || '',
      companyId: d.company_id,
      companyName: d.company_name || form.value.company,
      fileUrl: scanStore.fileUrl,
      fieldCount: countFilledFields(),
      lowConfidenceCount: countLowConfidence(),
      mergeMode: 'merge',
    })
    router.replace('/customers/scan/success')
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
  // 用于成功页判断 "新建" vs "加到现有客户"
  const wasAttach = isAttachMode.value
  try {
    // attachTo 模式: 直接给指定客户加联系人, 不新建客户
    let companyId = scanStore.attachToCompanyId
    let companyName = scanStore.attachToCompanyName || form.value.company
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
      companyName = form.value.company.trim()
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
    scanStore.setSaveResult({
      contactId: td.data?.id,
      contactName: form.value.name.trim(),
      position: form.value.position,
      phone: form.value.phone,
      email: form.value.email,
      companyId,
      companyName,
      fileUrl: scanStore.fileUrl,
      fieldCount: countFilledFields(),
      lowConfidenceCount: countLowConfidence(),
      mergeMode: wasAttach ? 'attach' : 'new',
    })
    router.replace('/customers/scan/success')
  } catch (e) {
    error.value = `保存失败: ${e?.message || e}`
    saving.value = false
  }
}

// 统计填了几个字段 (供成功页副标"N 个字段已保存")
function countFilledFields() {
  let n = 0
  for (const k of ['name','company','position','department','phone','email','address']) {
    if ((form.value[k] || '').trim()) n++
  }
  return n
}
// 低置信度字段数 (供副标"M 个待你后续核对")
function countLowConfidence() {
  let n = 0
  for (const k of ['name','company','position','department','phone','email','address']) {
    const c = confidence.value[k]
    if ((form.value[k] || '').trim() && c != null && c < 0.9) n++
  }
  return n
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

    <!-- 联系人级重复 sheet (设计稿 ScanDuplicate 风格) -->
    <Teleport to="body">
      <Transition name="dup-sheet">
        <div v-if="showDupDialog" class="fixed inset-0 z-50 flex items-end justify-center">
          <div class="absolute inset-0" style="background: rgba(20,20,20,0.42);"
            @click="showDupDialog = false" />
          <div class="relative w-full"
            style="background: var(--color-card); border-top-left-radius: 20px; border-top-right-radius: 20px; max-height: 85vh; display: flex; flex-direction: column;">
            <div class="mx-auto shrink-0" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin: 10px auto 4px;"></div>

            <!-- 标题 (⚠️ 黄三角 + 文字) -->
            <div class="px-5 pt-3 pb-1 flex items-center gap-2.5 shrink-0">
              <div class="shrink-0 inline-flex items-center justify-center"
                style="width: 36px; height: 36px; border-radius: 10px; background: #FBF1DF; border: 1px solid #F6E4BE;">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 1.5L17 15.5H1L9 1.5z" stroke="#B8762A" stroke-width="1.4" stroke-linejoin="round" />
                  <path d="M9 7v4M9 13v0.5" stroke="#B8762A" stroke-width="1.6" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-serif" style="font-size: 18px; color: var(--color-ink);">检测到重复</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
                  「{{ duplicates[0]?.name || form.name }}」联系人已存在
                </div>
              </div>
            </div>

            <!-- 候选 list — 第一个推荐, 都是 radio 风格 -->
            <div class="flex-1 overflow-y-auto px-4 pt-2">
              <!-- 合并选项 -->
              <div v-for="(d, i) in duplicates" :key="d.contact_id"
                @click="dupChoice = 'merge'; dupSelectedIdx = i"
                class="rounded-xl mb-2 active:opacity-80 cursor-pointer"
                :style="{
                  background: dupChoice === 'merge' && dupSelectedIdx === i ? 'rgba(217,119,87,0.06)' : 'var(--color-card)',
                  border: dupChoice === 'merge' && dupSelectedIdx === i ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
                  padding: '14px',
                }">
                <div class="flex items-center gap-2.5">
                  <!-- radio circle -->
                  <div class="shrink-0 inline-flex items-center justify-center"
                    :style="{
                      width: '22px', height: '22px', borderRadius: '11px',
                      background: dupChoice === 'merge' && dupSelectedIdx === i ? 'var(--color-accent)' : 'transparent',
                      border: dupChoice === 'merge' && dupSelectedIdx === i ? 'none' : '1.5px solid var(--color-ink-3)',
                    }">
                    <svg v-if="dupChoice === 'merge' && dupSelectedIdx === i" width="10" height="10" viewBox="0 0 10 10">
                      <path d="M1 5l3 3 5-6" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline gap-1">
                      <span style="font-size: 14.5px; font-weight: 600; color: var(--color-ink);">合并到已有联系人</span>
                      <span v-if="i === 0" style="font-size: 10.5px; color: var(--color-accent); margin-left: 4px;">· 推荐</span>
                    </div>
                    <div style="font-size: 12px; color: var(--color-ink-3); margin-top: 2px;">
                      把这次扫到的字段补进已有联系人, 并更新名片图
                    </div>
                  </div>
                </div>
                <!-- 联系人预览卡 -->
                <div class="mt-3 px-3 py-2.5 rounded-lg"
                  style="background: #fff; border: 1px solid var(--color-divider);">
                  <div class="flex items-center gap-2.5">
                    <div class="rounded-full inline-flex items-center justify-center font-serif shrink-0"
                      style="width: 32px; height: 32px; background: var(--color-accent); color: #fff; font-size: 14px;">
                      {{ d.name?.[0] || '?' }}
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-baseline gap-1.5">
                        <span style="font-size: 13.5px; font-weight: 500; color: var(--color-ink);">{{ d.name }}</span>
                        <span v-if="d.has_business_card" style="font-size: 9px; font-weight: 600; padding: 1px 4px; border-radius: 3px; background: var(--color-accent-soft); color: var(--color-accent);">名片</span>
                      </div>
                      <div style="font-size: 11.5px; color: var(--color-ink-3); margin-top: 1px;" class="truncate">
                        {{ [d.position, d.company_name].filter(Boolean).join(' · ') }}
                      </div>
                      <div v-if="d.phone || d.email" style="font-size: 11px; color: var(--color-ink-3); margin-top: 2px;" class="tabular truncate">
                        {{ [d.phone, d.email].filter(Boolean).join(' · ') }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 仍然新建独立联系人 -->
              <div @click="dupChoice = 'new'"
                class="rounded-xl mb-2 active:opacity-80 cursor-pointer flex items-center gap-2.5"
                :style="{
                  border: dupChoice === 'new' ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
                  background: dupChoice === 'new' ? 'rgba(217,119,87,0.06)' : 'var(--color-card)',
                  padding: '14px',
                }">
                <div class="shrink-0 inline-flex items-center justify-center"
                  :style="{
                    width: '22px', height: '22px', borderRadius: '11px',
                    background: dupChoice === 'new' ? 'var(--color-accent)' : 'transparent',
                    border: dupChoice === 'new' ? 'none' : '1.5px solid var(--color-ink-3)',
                  }">
                  <svg v-if="dupChoice === 'new'" width="10" height="10" viewBox="0 0 10 10">
                    <path d="M1 5l3 3 5-6" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div style="font-size: 14px; font-weight: 500; color: var(--color-ink);">仍然新建独立联系人</div>
                  <div style="font-size: 11.5px; color: var(--color-ink-3); margin-top: 2px;">
                    当作不同人处理 · 不合并到任何已有联系人
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部确认/取消 -->
            <div class="flex gap-2 px-4 pt-3 shrink-0"
              style="border-top: 1px solid var(--color-divider); padding-bottom: calc(env(safe-area-inset-bottom) + 14px);">
              <button @click="showDupDialog = false" :disabled="saving"
                class="flex-1 py-3.5 rounded-xl active:opacity-70 disabled:opacity-40"
                style="border: 1px solid var(--color-divider-strong); background: #fff; color: var(--color-ink); font-size: 14.5px; font-weight: 500;">
                取消
              </button>
              <button @click="confirmDupSheet" :disabled="saving"
                class="rounded-xl text-white font-semibold active:opacity-70 disabled:opacity-40"
                style="flex: 1.6; padding: 14px 0; background: var(--color-accent); font-size: 14.5px;">
                {{ saving ? '处理中…' : '确定' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 公司级重复 sheet (设计稿 ScanDuplicate, 公司维度) -->
    <Teleport to="body">
      <Transition name="dup-sheet">
        <div v-if="showCompanyDupDialog" class="fixed inset-0 z-50 flex items-end justify-center">
          <div class="absolute inset-0" style="background: rgba(20,20,20,0.42);"
            @click="showCompanyDupDialog = false" />
          <div class="relative w-full"
            style="background: var(--color-card); border-top-left-radius: 20px; border-top-right-radius: 20px; max-height: 85vh; display: flex; flex-direction: column;">
            <div class="mx-auto shrink-0" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin: 10px auto 4px;"></div>

            <div class="px-5 pt-3 pb-1 flex items-center gap-2.5 shrink-0">
              <div class="shrink-0 inline-flex items-center justify-center"
                style="width: 36px; height: 36px; border-radius: 10px; background: #FBF1DF; border: 1px solid #F6E4BE;">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 1.5L17 15.5H1L9 1.5z" stroke="#B8762A" stroke-width="1.4" stroke-linejoin="round" />
                  <path d="M9 7v4M9 13v0.5" stroke="#B8762A" stroke-width="1.6" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-serif" style="font-size: 18px; color: var(--color-ink);">检测到重复</div>
                <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
                  「{{ form.company }}」客户已存在
                </div>
              </div>
            </div>

            <div class="flex-1 overflow-y-auto px-4 pt-2">
              <!-- 合并选项 (含富预览卡: 累计金额/进行中/联系人数) -->
              <div v-for="(c, i) in companyDuplicates" :key="c.id || c.company_id || i"
                @click="companyDupChoice = 'merge'; companyDupSelectedIdx = i"
                class="rounded-xl mb-2 active:opacity-80 cursor-pointer"
                :style="{
                  background: companyDupChoice === 'merge' && companyDupSelectedIdx === i ? 'rgba(217,119,87,0.06)' : 'var(--color-card)',
                  border: companyDupChoice === 'merge' && companyDupSelectedIdx === i ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
                  padding: '14px',
                }">
                <div class="flex items-center gap-2.5">
                  <div class="shrink-0 inline-flex items-center justify-center"
                    :style="{
                      width: '22px', height: '22px', borderRadius: '11px',
                      background: companyDupChoice === 'merge' && companyDupSelectedIdx === i ? 'var(--color-accent)' : 'transparent',
                      border: companyDupChoice === 'merge' && companyDupSelectedIdx === i ? 'none' : '1.5px solid var(--color-ink-3)',
                    }">
                    <svg v-if="companyDupChoice === 'merge' && companyDupSelectedIdx === i" width="10" height="10" viewBox="0 0 10 10">
                      <path d="M1 5l3 3 5-6" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline gap-1">
                      <span style="font-size: 14.5px; font-weight: 600; color: var(--color-ink);">合并到现有客户</span>
                      <span v-if="i === 0" style="font-size: 10.5px; color: var(--color-accent); margin-left: 4px;">· 推荐</span>
                    </div>
                    <div style="font-size: 12px; color: var(--color-ink-3); margin-top: 2px;">
                      {{ form.name }} 将作为新联系人加入「{{ c.name }}」
                    </div>
                  </div>
                </div>
                <!-- 客户预览卡 (富信息) -->
                <div class="mt-3 px-3 py-2.5 rounded-lg"
                  style="background: #fff; border: 1px solid var(--color-divider);">
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="font-serif truncate" style="font-size: 14.5px; color: var(--color-ink);">{{ c.name }}</span>
                  </div>
                  <div class="tabular flex items-center gap-3.5"
                    style="font-size: 11.5px; color: var(--color-ink-3);">
                    <span>累计 <b style="color: var(--color-ink); font-weight: 600;">{{ c.value_wan ?? 0 }}</b> 万</span>
                    <span>{{ c.open_count ?? 0 }} 进行中</span>
                    <span>{{ c.contact_count ?? 0 }} 联系人</span>
                  </div>
                  <div class="mt-2 pt-2"
                    style="border-top: 1px dashed var(--color-divider);">
                    <div style="font-size: 10.5px; color: var(--color-accent); font-weight: 600; letter-spacing: 0.4px; margin-bottom: 4px;">
                      新增 · 第 {{ (c.contact_count ?? 0) + 1 }} 位联系人
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="rounded-full inline-flex items-center justify-center font-serif shrink-0"
                        style="width: 26px; height: 26px; background: var(--color-accent); color: #fff; font-size: 13px;">
                        {{ form.name?.[0] || '?' }}
                      </div>
                      <span style="font-size: 12.5px; color: var(--color-ink);">
                        {{ form.name }}
                        <span v-if="form.position" style="color: var(--color-ink-3);">· {{ form.position }}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 仍然新建客户 radio -->
              <div @click="companyDupChoice = 'new'"
                class="rounded-xl mb-2 active:opacity-80 cursor-pointer flex items-center gap-2.5"
                :style="{
                  border: companyDupChoice === 'new' ? '1.5px solid var(--color-accent)' : '1px solid var(--color-divider)',
                  background: companyDupChoice === 'new' ? 'rgba(217,119,87,0.06)' : 'var(--color-card)',
                  padding: '14px',
                }">
                <div class="shrink-0 inline-flex items-center justify-center"
                  :style="{
                    width: '22px', height: '22px', borderRadius: '11px',
                    background: companyDupChoice === 'new' ? 'var(--color-accent)' : 'transparent',
                    border: companyDupChoice === 'new' ? 'none' : '1.5px solid var(--color-ink-3)',
                  }">
                  <svg v-if="companyDupChoice === 'new'" width="10" height="10" viewBox="0 0 10 10">
                    <path d="M1 5l3 3 5-6" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div style="font-size: 14px; font-weight: 500; color: var(--color-ink);">仍然新建客户</div>
                  <div style="font-size: 11.5px; color: var(--color-ink-3); margin-top: 2px;">
                    当作不同分公司处理
                  </div>
                </div>
              </div>
            </div>

            <div class="flex gap-2 px-4 pt-3 shrink-0"
              style="border-top: 1px solid var(--color-divider); padding-bottom: calc(env(safe-area-inset-bottom) + 14px);">
              <button @click="showCompanyDupDialog = false" :disabled="saving"
                class="flex-1 py-3.5 rounded-xl active:opacity-70 disabled:opacity-40"
                style="border: 1px solid var(--color-divider-strong); background: #fff; color: var(--color-ink); font-size: 14.5px; font-weight: 500;">
                取消
              </button>
              <button @click="confirmCompanyDupSheet" :disabled="saving"
                class="rounded-xl text-white font-semibold active:opacity-70 disabled:opacity-40"
                style="flex: 1.6; padding: 14px 0; background: var(--color-accent); font-size: 14.5px;">
                {{ saving ? '处理中…' : '确定' }}
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
.dup-sheet-enter-active, .dup-sheet-leave-active { transition: opacity .18s ease, transform .22s ease; }
.dup-sheet-enter-from, .dup-sheet-leave-to { opacity: 0; }
.dup-sheet-enter-from > div:last-child, .dup-sheet-leave-to > div:last-child { transform: translateY(20px); }
</style>
