<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCustomer, addCustomerNote, addContact, getCustomerSharing, updateCustomerSharing } from '@/api/customers'
import client      from '@/api/client'
import NavBar      from '@/components/common/NavBar.vue'
import Section     from '@/components/common/Section.vue'
import StageDot    from '@/components/common/StageDot.vue'
import Avatar      from '@/components/common/Avatar.vue'
import FilledField from '@/components/common/FilledField.vue'
import NoteSheet   from '@/components/common/NoteSheet.vue'
import MultiPersonPickerSheet from '@/components/common/MultiPersonPickerSheet.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const company = ref(null)
const loading = ref(true)

// 跟进
const showNoteBox = ref(false)

// 新增联系人 sheet（对标 customer-screens.jsx AddContactSheet）
const showContactSheet = ref(false)
const showAddContactChooser = ref(false)   // + 添加 → 选 "拍名片" / "手动" 的 sheet
function pickScanContact() {
  showAddContactChooser.value = false
  // 带 attachTo 给扫描页, 让其跳过新建客户, 直接给该客户加联系人
  // 注: 后端 mobile_customer_detail 用 _company_summary 返回 'name' (不是 company_name)
  router.push({
    path: '/customers/scan',
    query: { attachTo: company.value.id, attachToName: company.value.name || '' },
  })
}
function pickManualContact() {
  showAddContactChooser.value = false
  showContactSheet.value = true
}
const newContact = ref({ name: '', position: '', phone: '', email: '', is_primary: false })
const addingContact = ref(false)

// 阶段 → tier 颜色（A=ink, B=ink3, C=ink4）— 对标 SearchCustomerRow tierColor
const TIER_COLOR = { A: '#1A1A1A', B: '#7A7570', C: '#C2BBB3' }

const statusColor = computed(() => {
  const s = company.value?.status
  if (s === '活跃' || s === 'Active') return '#2F7A45'
  if (s === '冷却' || s === 'Cooling') return '#7A7570'
  return '#7A7570'
})

const visibleProjects = computed(() => (company.value?.projects || []).slice(0, 4))

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    company.value = res.data.data
  } finally {
    loading.value = false
  }
}

async function submitNote(text) {
  await addCustomerNote(route.params.id, text)
  await load()
}

async function submitContact() {
  if (!newContact.value.name.trim()) return
  addingContact.value = true
  try {
    await addContact(route.params.id, newContact.value)
    newContact.value = { name: '', position: '', phone: '', email: '', is_primary: false }
    showContactSheet.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.message || t('customer.addFailed'))
  } finally {
    addingContact.value = false
  }
}

function callPhone(phone) { if (phone) window.open(`tel:${phone}`) }

// 名片图全屏查看 — 后端 /mobile/chat/file 要 ?token= 鉴权
const viewingCardUrl = ref('')
const viewingCardFullUrl = computed(() => {
  const u = viewingCardUrl.value
  if (!u) return ''
  if (/^https?:\/\//.test(u)) return u
  const baseHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
  const token = localStorage.getItem('access_token') || ''
  const sep = u.includes('?') ? '&' : '?'
  return `${baseHost}${u}${sep}token=${encodeURIComponent(token)}`
})
function viewCardImage(url) { viewingCardUrl.value = url }
function closeCardImage() { viewingCardUrl.value = '' }
function newProject() {
  router.push({ path: '/projects/new', query: { company_id: route.params.id } })
}
function openProject(id) {
  router.push(`/projects/${id}`)
}

// ─── Sharing (reuses web SharingService via mobile API + common picker) ───
const canShare = ref(false)
const shareOptions = ref([])
const shareSelected = ref([])
const showSharePicker = ref(false)
const shareToast = ref('')
async function loadSharing() {
  try {
    const res = await getCustomerSharing(route.params.id)
    const d = res.data?.data || {}
    canShare.value = !!d.can_edit
    shareOptions.value = d.options || []
    shareSelected.value = d.selected || []
  } catch {
    canShare.value = false
  }
}
async function onShareSelected(ids) {
  const prev = shareSelected.value
  shareSelected.value = ids
  try {
    const res = await updateCustomerSharing(route.params.id, ids)
    shareSelected.value = res.data?.data?.selected || ids
    shareToast.value = ids.length
      ? t('customer.shareSavedN', { n: ids.length })
      : t('customer.shareCleared')
    setTimeout(() => { shareToast.value = '' }, 1800)
  } catch (e) {
    shareSelected.value = prev
    alert(e.response?.data?.message || t('customer.shareFail'))
  }
}

onMounted(() => { load(); loadSharing() })
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- Nav -->
    <NavBar :back-label="t('common.customer')" @back="router.back()"
      @more="router.push(`/customers/${route.params.id}/edit`)">
      <template #right>
        <span style="font-size: 15px; color: var(--color-accent); font-weight: 500;">{{ t('common.edit') }}</span>
      </template>
    </NavBar>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <div v-else-if="company" class="flex-1 overflow-y-auto pb-24">

      <!-- ─── Hero ─────────────────────────────────────── -->
      <div class="px-7 pt-5 pb-6">
        <div class="flex items-center gap-2.5 mb-3.5 flex-wrap">
          <span class="inline-flex items-center gap-1.5 text-[11px] font-semibold"
            :style="{ color: statusColor, letterSpacing: '0.4px' }">
            <span class="w-[5px] h-[5px] rounded-[3px]" :style="{ background: statusColor }" />
            {{ company.status || t('customer.statusActive') }}
          </span>
          <span v-if="company.industry" class="text-[11px]" style="color: var(--color-ink-3);">
            · {{ company.industry }}
          </span>
        </div>

        <h1 class="font-serif font-medium leading-tight m-0"
          style="font-size: 28px; letter-spacing: -0.3px; color: var(--color-ink);">
          {{ company.name }}
        </h1>

        <div class="mt-3 text-[13px]" style="color: var(--color-ink-3);">
          <template v-if="company.tier">{{ company.tier }} {{ t('customer.tierClient') }} · </template>
          {{ [company.region, company.company_size].filter(Boolean).join(' · ') || '—' }}
        </div>

        <!-- 累计客户价值 -->
        <div class="mt-6 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular"
            style="font-size: 44px; color: var(--color-ink);">
            {{ company.value_display || '—' }}
          </span>
          <span class="text-[14px]" style="color: var(--color-ink-3);">{{ t('customer.cumulativeValue') }}</span>
        </div>
      </div>

      <!-- ─── CTA row ──────────────────────────────────── -->
      <div class="px-5 pb-2 flex gap-2.5">
        <button @click="newProject" type="button"
          class="flex-1 h-12 rounded-2xl text-white text-[15px] font-semibold active:opacity-90"
          style="background: var(--color-accent); border: none;">
          {{ t('customer.newProject') }}
        </button>
        <button @click="showNoteBox = true" type="button"
          class="h-12 px-3.5 rounded-2xl flex items-center gap-1.5 active:opacity-70 shrink-0"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <svg width="14" height="14" viewBox="0 0 18 18" fill="none" style="pointer-events: none;">
            <path d="M9 2v14M2 9h14" stroke="var(--color-ink-2)" stroke-width="2" stroke-linecap="round" />
          </svg>
          <span class="text-[12px]" style="color: var(--color-ink-2); pointer-events: none;">{{ t('customer.followUp') }}</span>
        </button>
        <button v-if="canShare" @click="showSharePicker = true" type="button"
          class="h-12 px-3.5 rounded-2xl flex items-center gap-1.5 active:opacity-70 shrink-0"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style="pointer-events: none;">
            <path d="M18 8a3 3 0 100-6 3 3 0 000 6zM6 15a3 3 0 100-6 3 3 0 000 6zM18 22a3 3 0 100-6 3 3 0 000 6zM8.6 13.5l6.8 4M15.4 6.5l-6.8 4"
              stroke="var(--color-ink-2)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="text-[12px]" style="color: var(--color-ink-2); pointer-events: none;">
            {{ shareSelected.length ? t('customer.sharedN', { n: shareSelected.length }) : t('customer.share') }}
          </span>
        </button>
      </div>

      <!-- ─── 项目概览 4 数 ──────────────────────────── -->
      <Section :title="t('customer.overview')">
        <div class="grid grid-cols-4 rounded-2xl p-4"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink);">
              {{ company.total_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ t('customer.statTotal') }}</div>
          </div>
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-accent);">
              {{ company.open_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ t('customer.statOpen') }}</div>
          </div>
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink);">
              {{ company.won_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ t('customer.statSigned') }}</div>
          </div>
          <div class="text-center">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink-4);">
              {{ company.lost_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">{{ t('customer.statLost') }}</div>
          </div>
        </div>
      </Section>

      <!-- ─── 名下项目 ─────────────────────────────────── -->
      <Section :title="t('customer.ownedProjects')">
        <template #action>
          <span class="text-[12px]" style="color: var(--color-ink-3);">
            {{ t('customer.ownedTotal', { n: company.total_count ?? 0 }) }}
          </span>
        </template>
        <div v-if="visibleProjects.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(p, i) in visibleProjects" :key="p.id"
            @click="openProject(p.id)"
            class="px-4 py-3 flex items-baseline justify-between gap-3 active:bg-bg cursor-pointer"
            :style="i < visibleProjects.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="flex-1 min-w-0">
              <div class="font-serif font-medium leading-tight truncate"
                style="font-size: 15px; color: var(--color-ink);">{{ p.name }}</div>
              <div class="mt-1"><StageDot :tone="p.tone" :label="p.stage_label" /></div>
            </div>
            <div class="text-[14px] font-semibold tabular whitespace-nowrap">
              <template v-if="p.amount_display">
                {{ p.amount_display }}
              </template>
              <span v-else class="text-[13px]" style="color: var(--color-ink-3);">—</span>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">{{ t('customer.noProjects') }}</div>
      </Section>

      <!-- ─── 详情 definition list ─────────────────────── -->
      <Section :title="t('customer.detail')">
        <div class="grid text-[14px]" style="grid-template-columns: 90px 1fr; row-gap: 12px; column-gap: 16px;">
          <span style="color: var(--color-ink-3);">{{ t('customer.fOwner') }}</span>
          <span>{{ company.owner_name || '—' }}</span>
          <span style="color: var(--color-ink-3);">{{ t('customer.fTier') }}</span>
          <span><b class="font-semibold">{{ company.tier || '—' }}</b><template v-if="company.tier"> {{ t('customer.tierSuffix') }}</template></span>
          <span style="color: var(--color-ink-3);">{{ t('customer.fAddress') }}</span>
          <span>{{ company.address || '—' }}</span>
          <template v-if="company.established">
            <span style="color: var(--color-ink-3);">{{ t('customer.fEstablished') }}</span>
            <span class="tabular">{{ company.established }}</span>
          </template>
          <span style="color: var(--color-ink-3);">{{ t('customer.fSource') }}</span>
          <span>{{ company.source || '—' }}</span>
        </div>
      </Section>

      <!-- ─── 联系人 ───────────────────────────────────── -->
      <Section :title="t('customer.contacts')">
        <template #action>
          <button @click="showAddContactChooser = true"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">{{ t('customer.addBtn') }}</button>
        </template>
        <div v-if="company.contacts?.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(p, i) in company.contacts" :key="p.id"
            @click="router.push(`/customers/${company.id}/contacts/${p.id}`)"
            class="p-3.5 flex items-center gap-3.5 active:bg-gray-50 cursor-pointer"
            :style="i < company.contacts.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <Avatar :text="p.name" :size="40" :primary="p.is_primary" />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-[15px] font-semibold truncate">{{ p.name }}</span>
                <!-- 名片 chip: 这条联系人是名片扫描录入的 -->
                <button v-if="p.business_card_image_url"
                  @click.stop="viewCardImage(p.business_card_image_url)"
                  class="text-[9px] font-bold px-1.5 py-px rounded active:opacity-70"
                  style="color: var(--color-accent); background: var(--color-accent-soft);">
                  {{ t('customer.cardChip') }}
                </button>
              </div>
              <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
                {{ [p.position, p.department].filter(Boolean).join(' · ') || '—' }}
              </div>
            </div>
            <button v-if="p.phone" @click.stop="callPhone(p.phone)"
              class="w-9 h-9 rounded-full flex items-center justify-center active:opacity-70"
              style="background: transparent; border: 1px solid var(--color-divider);">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
                  fill="var(--color-ink-2)" />
              </svg>
            </button>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">{{ t('customer.noContacts') }}</div>
      </Section>

      <!-- ─── 跟进时间轴 ─────────────────────────────── -->
      <div class="px-7 pt-5 pb-24">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('customer.noteRecords') }}</div>
          <button @click="showNoteBox = true"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">{{ t('customer.addBtn') }}</button>
        </div>
        <div v-if="company.actions?.length">
          <div v-for="(a, i) in company.actions" :key="a.id"
            class="pl-3.5"
            :style="{
              borderLeft: '2px solid ' + (i === 0 ? 'var(--color-accent)' : 'var(--color-divider)'),
              marginTop: i ? '16px' : '0',
            }">
            <div class="text-[11px] tabular mb-1" style="color: var(--color-ink-3);">
              {{ a.date }} — {{ a.owner_name }}
            </div>
            <div :style="{
                fontSize: '14px',
                lineHeight: '1.5',
                color: i === 0 ? 'var(--color-ink)' : 'var(--color-ink-2)',
                fontFamily: 'var(--font-sans)',
              }">
              {{ a.communication }}
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">{{ t('customer.noNotes') }}</div>
      </div>
    </div>

    <!-- ─── 跟进输入弹层（公用组件，与 ProjectDetailView 共用） ────── -->
    <NoteSheet v-model="showNoteBox" :submit="submitNote" />

    <!-- + 添加联系人: 拍名片 vs 手动 选择 sheet -->
    <Transition name="sheet">
      <div v-if="showAddContactChooser" class="absolute inset-0 z-40">
        <div class="absolute inset-0" style="background: rgba(0,0,0,0.4);"
          @click="showAddContactChooser = false" />
        <div class="absolute left-0 right-0 bottom-0 pb-7 pt-2.5"
          style="background: var(--color-bg); border-top-left-radius: 18px; border-top-right-radius: 18px;">
          <div class="mx-auto" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin-bottom: 14px;"></div>
          <div class="px-6 pb-2 flex items-center justify-between">
            <div class="font-serif" style="font-size: 20px; line-height: 1.25; color: var(--color-ink);">
              {{ t('customer.addContact') }}
            </div>
            <span style="font-size: 12px; color: var(--color-ink-3);">
              {{ t('customer.currentCustomer') }}: {{ company.company_name }}
            </span>
          </div>
          <!-- 主推: 拍名片 (橘色渐变) -->
          <button @click="pickScanContact"
            class="block w-full mx-4 mt-3 mb-2 rounded-2xl px-4 py-4 text-left active:opacity-80 relative overflow-hidden"
            style="width: calc(100% - 32px); background: linear-gradient(135deg, var(--color-accent) 0%, #C5613F 100%); color: #fff;">
            <div class="flex items-center gap-3.5">
              <div class="shrink-0 inline-flex items-center justify-center"
                style="width: 50px; height: 50px; border-radius: 14px; background: rgba(255,255,255,0.18);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                  <rect x="3" y="6" width="18" height="13" rx="2" stroke-linejoin="round" />
                  <circle cx="12" cy="12.5" r="3.5" />
                  <path d="M9 6V5a1 1 0 011-1h4a1 1 0 011 1v1" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div style="font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                  {{ t('customer.scanCardOption') }}
                </div>
                <div style="font-size: 12px; opacity: 0.85; margin-top: 4px; line-height: 1.5;">
                  {{ t('customer.scanCardDesc') }}
                </div>
              </div>
            </div>
          </button>
          <!-- 手动 -->
          <button @click="pickManualContact"
            class="block w-full mx-4 mb-2 rounded-2xl px-4 py-3.5 text-left active:opacity-80"
            style="width: calc(100% - 32px); background: var(--color-card); border: 1px solid var(--color-divider);">
            <div class="flex items-center gap-3">
              <div class="shrink-0 inline-flex items-center justify-center"
                style="width: 36px; height: 36px; border-radius: 10px; background: var(--color-bg); color: var(--color-ink-2);">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M12 5v14M5 12h14" stroke-linecap="round" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div style="font-size: 14.5px; font-weight: 500; color: var(--color-ink);">{{ t('customer.manualFill') }}</div>
                <div style="font-size: 11.5px; margin-top: 2px; color: var(--color-ink-3);">{{ t('customer.formFields') }}</div>
              </div>
              <span style="font-size: 18px; color: var(--color-ink-3);">›</span>
            </div>
          </button>
          <button @click="showAddContactChooser = false"
            class="block w-full mx-4 mt-2 py-3 rounded-xl text-[14px] active:opacity-70"
            style="width: calc(100% - 32px); background: transparent; border: 1px solid var(--color-divider-strong); color: var(--color-ink-2);">
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- ─── 新增联系人 sheet（对标 AddContactSheet） ───── -->
    <Transition name="sheet">
      <div v-if="showContactSheet" class="absolute inset-0 z-40">
        <div class="absolute inset-0" style="background: rgba(20,20,20,0.32);"
          @click="showContactSheet = false" />
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl overflow-hidden"
          style="background: var(--color-bg); box-shadow: 0 -10px 40px rgba(0,0,0,0.18);">
          <div class="flex justify-center pt-3 pb-2">
            <div class="w-9 h-1 rounded-full" style="background: rgba(0,0,0,0.15);" />
          </div>
          <div class="flex justify-between items-center px-6 pt-1 pb-4">
            <button @click="showContactSheet = false" class="text-[14px] active:opacity-60"
              style="color: var(--color-accent);">{{ t('common.cancel') }}</button>
            <span class="font-serif text-[18px] font-medium">{{ t('customer.addContact') }}</span>
            <button @click="submitContact"
              :disabled="addingContact || !newContact.name.trim()"
              class="text-[14px] font-bold active:opacity-60 disabled:opacity-40"
              :style="{ color: newContact.name.trim() ? 'var(--color-accent)' : 'var(--color-ink-4)' }">
              {{ addingContact ? t('customer.adding') : t('customer.addAction') }}
            </button>
          </div>
          <div class="px-5 pb-6">
            <div class="rounded-2xl py-1"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ t('customer.fieldName') }}</div>
                <input v-model="newContact.name" type="text"
                  class="w-full font-serif text-[17px] font-medium outline-none bg-transparent"
                  placeholder="—" />
              </div>
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ t('customer.fieldPosition') }}</div>
                <input v-model="newContact.position" type="text"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ t('customer.fieldPhone') }}</div>
                <input v-model="newContact.phone" type="tel"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
              <div class="px-4 py-3">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">{{ t('customer.fieldEmail') }}</div>
                <input v-model="newContact.email" type="email"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
            </div>

            <div class="mt-4 rounded-xl px-4 py-3.5 flex items-center justify-between"
              style="background: var(--color-accent-bg);">
              <div>
                <div class="text-[13px] font-semibold" style="color: var(--color-ink);">{{ t('customer.setPrimary') }}</div>
                <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                  {{ t('customer.currentPrimary') }}{{ company.contacts?.find(c => c.is_primary)?.name || t('customer.none') }}
                </div>
              </div>
              <button @click="newContact.is_primary = !newContact.is_primary"
                class="w-11 h-[26px] rounded-full relative transition-colors"
                :style="{ background: newContact.is_primary ? 'var(--color-accent)' : 'var(--color-divider)' }">
                <div class="absolute top-0.5 w-[22px] h-[22px] rounded-full transition-all"
                  :style="{
                    left: newContact.is_primary ? '20px' : '2px',
                    background: 'var(--color-card)',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.18)',
                  }" />
              </button>
            </div>

            <div class="mt-5 text-center text-[12px] font-serif italic"
              style="color: var(--color-ink-3);">
              {{ t('customer.addContactHint') }}
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 名片图全屏 lightbox -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="viewingCardUrl" class="fixed inset-0 z-50 flex items-center justify-center"
          style="background: rgba(0,0,0,0.92);" @click="closeCardImage">
          <button class="absolute top-3 right-3 w-10 h-10 rounded-full inline-flex items-center justify-center"
            style="background: rgba(255,255,255,0.15); color: #fff; font-size: 22px; font-weight: 200;"
            @click.stop="closeCardImage">×</button>
          <img :src="viewingCardFullUrl" class="block"
            style="max-width: 95vw; max-height: 80vh; object-fit: contain;" />
        </div>
      </Transition>
    </Teleport>

    <!-- Customer sharing: reuse the common multi-person picker -->
    <MultiPersonPickerSheet
      v-model="showSharePicker"
      :title="t('customer.shareTitle')"
      :options="shareOptions"
      :selected="shareSelected"
      @update:selected="onShareSelected" />

    <!-- Sharing-saved toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="shareToast" class="fixed left-1/2 z-[60]"
          style="bottom: 90px; transform: translateX(-50%); background: rgba(20,20,20,0.88);
                 color: #fff; font-size: 13px; padding: 9px 16px; border-radius: 999px; white-space: nowrap;">
          {{ shareToast }}
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
