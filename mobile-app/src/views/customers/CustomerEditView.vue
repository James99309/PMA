<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer, updateCustomer, archiveCustomer } from '@/api/customers'
import EditField from '@/components/common/EditField.vue'
import EditFormHeader from '@/components/common/EditFormHeader.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'
import AddressPickerSheet from '@/components/common/AddressPickerSheet.vue'
import { useDictionariesStore } from '@/stores/dictionaries'

const route = useRoute()
const router = useRouter()

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

// 行业（PMA 没存 DB 字典，硬编码）
const INDUSTRY_OPTIONS = [
  { value: 'manufacturing', label: '制造业' },
  { value: 'datacenter',    label: '数据中心' },
  { value: 'chemical',      label: '化工' },
  { value: 'energy',        label: '能源' },
  { value: 'transportation',label: '交通' },
  { value: 'tunnel_underground', label: '隧道/地下' },
  { value: 'real_estate',   label: '地产' },
  { value: 'hospitality',   label: '酒店' },
  { value: 'government',    label: '政府' },
  { value: 'education',     label: '教育' },
  { value: 'healthcare',    label: '医疗' },
  { value: 'technology',    label: '科技' },
  { value: 'semiconductor', label: '半导体' },
  { value: 'shipbuilding',  label: '造船' },
  { value: 'finance',       label: '金融' },
  { value: 'other',         label: '其他' },
]
const STATUS_OPTIONS = [
  { value: '高度活跃', label: '高度活跃' },
  { value: '活跃',     label: '活跃' },
  { value: '正常',     label: '正常' },
  { value: '待跟进',   label: '待跟进' },
  { value: '休眠',     label: '休眠' },
  { value: '流失',     label: '流失' },
]
const SOURCE_OPTIONS = computed(() =>
  dictStore.list('report_source').map(d => ({ value: d.label, label: d.displayLabel || d.label }))
  // source 后端存中文，所以 value 仍用原始 label, 显示用 displayLabel
)
const COMPANY_TYPE_OPTIONS = computed(() =>
  dictStore.list('company_type').map(d => ({ value: d.key, label: d.displayLabel || d.label }))
)

// 显示用 label
const companyTypeLabel = computed(() => dictStore.label('company_type', form.value.company_type))
const industryLabel = computed(() => INDUSTRY_OPTIONS.find(o => o.value === form.value.industry)?.label || form.value.industry)

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
      status:       c.status || '活跃',
      source:       c.source || '',
    }
    totalCount.value = c.total_count || 0
  } finally {
    loading.value = false
  }
}

const subtitle = computed(() => totalCount.value > 0
  ? `修改客户档案，改动会同步到名下 ${totalCount.value} 个项目。`
  : '修改客户档案。')

async function save() {
  saving.value = true
  try {
    await updateCustomer(route.params.id, form.value)
    router.back()
  } catch (e) {
    alert(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function archive() {
  alert('归档功能开发中（流程未确定）')
}

function transferOwner() {
  alert('转交功能开发中')
}

function deleteCustomer() {
  alert(totalCount.value > 0
    ? `客户名下还有 ${totalCount.value} 个项目，无法直接删除。请先归档。`
    : '硬删除功能开发中，请先归档客户。')
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
      title="编辑客户"
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
        style="color: var(--color-ink-3); letter-spacing: 1px;">基本信息</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="公司名称" v-model="form.company_name"
          :focused="focusedKey === 'company_name'" @click="focusedKey = 'company_name'" />
        <EditField label="企业类型" :model-value="companyTypeLabel" arrow
          :focused="focusedKey === 'company_type'"
          @click="focusedKey = 'company_type'; showCompanyTypePicker = true" />
        <EditField label="行业" :model-value="industryLabel" arrow
          :focused="focusedKey === 'industry'"
          @click="focusedKey = 'industry'; showIndustryPicker = true" />
        <EditField label="地址" :model-value="form.address" arrow
          :focused="focusedKey === 'address'"
          @click="focusedKey = 'address'; showAddressPicker = true" />
      </div>

      <!-- 来源 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">来源</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="来源" :model-value="form.source" arrow
          :focused="focusedKey === 'source'"
          @click="focusedKey = 'source'; showSourcePicker = true" />
      </div>

      <!-- 危险区 -->
      <div class="px-7 pt-6 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">其他</div>
      <div class="mx-5 mb-6 flex flex-col gap-2">
        <button @click="transferOwner"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] flex justify-between items-center active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: var(--color-ink-2);">
          转交给其他同事
          <svg width="7" height="11" viewBox="0 0 7 11">
            <path d="M1 1l4 4.5L1 10" stroke="var(--color-ink-3)" stroke-width="1.4" fill="none" stroke-linecap="round" />
          </svg>
        </button>
        <button @click="archive"
          class="px-4 py-3.5 rounded-xl text-left text-[14px] active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: #A8533A;">
          归档客户
        </button>
        <button @click="deleteCustomer"
          class="px-4 py-3.5 rounded-xl text-center text-[14px] font-medium active:opacity-70 mt-2"
          style="background: transparent; border: none; color: #B83C3C;">
          删除客户<template v-if="totalCount > 0">（及全部 {{ totalCount }} 个项目）</template>
        </button>
      </div>

      <div class="h-16" />
    </template>

    <!-- Pickers -->
    <PickerSheet v-model="showCompanyTypePicker" title="选择企业类型"
      :options="COMPANY_TYPE_OPTIONS" v-model:selected="form.company_type" />
    <PickerSheet v-model="showIndustryPicker" title="选择行业"
      :options="INDUSTRY_OPTIONS" v-model:selected="form.industry" />
    <PickerSheet v-model="showSourcePicker" title="选择来源"
      :options="SOURCE_OPTIONS" v-model:selected="form.source" />
    <AddressPickerSheet v-model="showAddressPicker"
      :initial-address="form.address" @select="onAddressSelect" />
  </div>
</template>
