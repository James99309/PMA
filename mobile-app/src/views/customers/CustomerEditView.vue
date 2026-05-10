<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCustomer, updateCustomer, archiveCustomer } from '@/api/customers'
import EditField from '@/components/common/EditField.vue'
import EditFormHeader from '@/components/common/EditFormHeader.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'
import AddressPickerSheet from '@/components/common/AddressPickerSheet.vue'
import { useDictionariesStore } from '@/stores/dictionaries'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const saving = ref(false)
const archiving = ref(false)
const focusedKey = ref('company_name')  // 默认聚焦公司名

const form = ref({
  company_name: '',
  company_type: '',
  industry: '',
  address: '',
  country: '',
  region: '',
  city: '',
  latitude: null,
  longitude: null,
  status: '',
  source: '',
})

const totalCount = ref(0)  // 名下项目数

// 字典 + 静态选项
const dictStore = useDictionariesStore()

// 行业（PMA 没存 DB 字典，复用 project.industry.* 翻译）
const INDUSTRY_KEYS = [
  'manufacturing','datacenter','chemical','energy','transportation','tunnel_underground',
  'real_estate','hospitality','government','education','healthcare','technology',
  'semiconductor','shipbuilding','finance','other',
]
const INDUSTRY_OPTIONS = computed(() =>
  INDUSTRY_KEYS.map(k => ({ value: k, label: t(`project.industry.${k}`) }))
)
// STATUS_OPTIONS 后端用中文 value, 仅显示需要 i18n 化(未在 UI 暴露 picker, 留作后续)
const SOURCE_OPTIONS = computed(() =>
  dictStore.list('report_source').map(d => ({ value: d.label, label: d.displayLabel || d.label }))
  // source 后端存中文，所以 value 仍用原始 label, 显示用 displayLabel
)
const COMPANY_TYPE_OPTIONS = computed(() =>
  dictStore.list('company_type').map(d => ({ value: d.key, label: d.displayLabel || d.label }))
)

// 显示用 label
const companyTypeLabel = computed(() => dictStore.label('company_type', form.value.company_type))
const industryLabel = computed(() => INDUSTRY_OPTIONS.value.find(o => o.value === form.value.industry)?.label || form.value.industry)

// Picker 开关
const showCompanyTypePicker = ref(false)
const showIndustryPicker = ref(false)
const showSourcePicker = ref(false)
const showAddressPicker = ref(false)

function onAddressSelect(d) {
  form.value.country  = d.country
  form.value.region   = d.region
  form.value.city     = d.city
  form.value.address  = d.address
  form.value.latitude = d.latitude
  form.value.longitude = d.longitude
}

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    const c = res.data.data
    form.value = {
      company_name: c.name || '',
      company_type: c.company_type || '',
      industry:     c.industry || '',
      address:      c.address || '',
      country:      c.country || '',
      region:       c.region  || '',
      city:         c.city    || '',
      latitude:     c.latitude  || null,
      longitude:    c.longitude || null,
      status:       c.status || t('customer.statusActiveDefault'),
      source:       c.source || '',
    }
    totalCount.value = c.total_count || 0
  } finally {
    loading.value = false
  }
}

const subtitle = computed(() => totalCount.value > 0
  ? t('customer.editSubtitleWithProjects', { n: totalCount.value })
  : t('customer.editSubtitleNoProjects'))

async function save() {
  saving.value = true
  try {
    await updateCustomer(route.params.id, form.value)
    router.back()
  } catch (e) {
    alert(e.response?.data?.message || t('customer.editSaveFail'))
  } finally {
    saving.value = false
  }
}

function archive() {
  alert(t('customer.editArchiveTodo'))
}

function transferOwner() {
  alert(t('customer.editTransferTodo'))
}

function deleteCustomer() {
  alert(totalCount.value > 0
    ? t('customer.editDeleteBlocked', { n: totalCount.value })
    : t('customer.editDeleteTodo'))
}

onMounted(() => {
  dictStore.ensure('company_type')
  dictStore.ensure('report_source')
  load()
})
</script>

<template>
  <div class="flex flex-col h-full overflow-y-auto" style="background: var(--color-bg);">

    <EditFormHeader
      :title="t('customer.editTitle')"
      :saving="saving"
      :dirty="true"
      :missing-count="form.company_name?.trim() ? 0 : 1"
      @cancel="router.back()"
      @save="save" />

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <template v-else>
      <!-- 副标题（衬线斜体）-->
      <div class="px-7 pt-3 font-serif italic"
        style="font-size: 13px; color: var(--color-ink-3);">
        {{ subtitle }}
      </div>

      <!-- 基本信息 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('customer.editSecBasic') }}</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField :label="t('customer.editFCompanyName')" v-model="form.company_name"
          :focused="focusedKey === 'company_name'" @click="focusedKey = 'company_name'" />
        <EditField :label="t('customer.editFCompanyType')" :model-value="companyTypeLabel" arrow
          :focused="focusedKey === 'company_type'"
          @click="focusedKey = 'company_type'; showCompanyTypePicker = true" />
        <EditField :label="t('customer.editFIndustry')" :model-value="industryLabel" arrow
          :focused="focusedKey === 'industry'"
          @click="focusedKey = 'industry'; showIndustryPicker = true" />
        <EditField :label="t('customer.editFAddress')" :model-value="form.address" arrow
          :focused="focusedKey === 'address'"
          @click="focusedKey = 'address'; showAddressPicker = true" />
      </div>

      <!-- 来源 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('customer.editSecSource') }}</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField :label="t('customer.editFSource')" :model-value="form.source" arrow
          :focused="focusedKey === 'source'"
          @click="focusedKey = 'source'; showSourcePicker = true" />
      </div>

      <!-- 危险区 -->
      <div class="px-7 pt-6 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">{{ t('customer.editSecOther') }}</div>
      <div class="mx-5 mb-6 flex flex-col gap-2">
        <button @click="transferOwner"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] flex justify-between items-center active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: var(--color-ink-2);">
          {{ t('customer.editTransfer') }}
          <svg width="7" height="11" viewBox="0 0 7 11">
            <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" fill="none" stroke-linecap="round" />
          </svg>
        </button>
        <button @click="archive"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: #A8533A;">
          {{ t('customer.editArchive') }}
        </button>
        <button @click="deleteCustomer"
          class="px-4 py-3.5 rounded-xl text-center text-[14px] font-medium active:opacity-70 mt-2"
          style="background: transparent; border: none; color: #B83C3C;">
          {{ t('customer.editDelete') }}<template v-if="totalCount > 0">{{ t('customer.editDeleteSuffix', { n: totalCount }) }}</template>
        </button>
      </div>

      <div class="h-16" />
    </template>

    <!-- Pickers -->
    <PickerSheet v-model="showCompanyTypePicker" :title="t('customer.editPickCompanyType')"
      :options="COMPANY_TYPE_OPTIONS" v-model:selected="form.company_type" />
    <PickerSheet v-model="showIndustryPicker" :title="t('customer.editPickIndustry')"
      :options="INDUSTRY_OPTIONS" v-model:selected="form.industry" />
    <PickerSheet v-model="showSourcePicker" :title="t('customer.editPickSource')"
      :options="SOURCE_OPTIONS" v-model:selected="form.source" />
    <AddressPickerSheet v-model="showAddressPicker"
      :initial-address="form.address" @select="onAddressSelect" />
  </div>
</template>
