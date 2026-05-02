<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, updateProject, getVendorSalesManagers } from '@/api/projects'
import EditField from '@/components/common/EditField.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'
import AddressPickerSheet from '@/components/common/AddressPickerSheet.vue'
import { useDictionariesStore } from '@/stores/dictionaries'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const focusedKey = ref('project_name')

const form = ref({
  project_name: '',
  project_type: '',
  industry: '',
  product_situation: '',
  design_issues: '',
  stage_description: '',
  delivery_forecast: '',
  address: '',
  country: '',
  region: '',
  city: '',
  latitude: null,
  longitude: null,
  vendor_sales_manager_id: null,
})

// 厂商销售负责人候选 + label
const vendorSalesManagers = ref([])
const vsmLabel = computed(() => {
  const u = vendorSalesManagers.value.find(x => x.id === form.value.vendor_sales_manager_id)
  return u ? u.name : ''
})
const VSM_OPTIONS = computed(() => vendorSalesManagers.value.map(u => ({
  value: u.id,
  label: u.department ? `${u.name} · ${u.department}` : u.name,
})))

// 产品情况
const PRODUCT_SITUATION_OPTIONS = [
  { value: 'qualified',    label: '入围' },
  { value: 'controlled',   label: '受控' },
  { value: 'not_required', label: '无要求' },
  { value: 'unqualified',  label: '未入围' },
]
const productSituationLabel = computed(() =>
  PRODUCT_SITUATION_OPTIONS.find(o => o.value === form.value.product_situation)?.label || ''
)

const isLocked = ref(false)
const dictStore = useDictionariesStore()

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
const PROJECT_TYPE_OPTIONS = computed(() =>
  dictStore.list('project_type').map(d => ({ value: d.key, label: d.label }))
)
const projectTypeLabel = computed(() => dictStore.label('project_type', form.value.project_type))
const industryLabel = computed(() => INDUSTRY_OPTIONS.find(o => o.value === form.value.industry)?.label || form.value.industry)

// Picker 开关
const showProjectTypePicker = ref(false)
const showIndustryPicker = ref(false)
const showAddressPicker = ref(false)
const showProductSituationPicker = ref(false)
const showVsmPicker = ref(false)

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
    const r = await getProject(route.params.id)
    const p = r.data.data
    isLocked.value = !!p.is_locked
    form.value = {
      project_name: p.name || '',
      project_type: p.project_type || '',
      industry:     p.industry || '',
      product_situation: p.product_situation || '',
      design_issues:     p.design_issues || '',
      stage_description: p.stage_description || '',
      delivery_forecast: p.delivery_forecast ? p.delivery_forecast.split('T')[0] : '',
      address:      p.address || '',
      country:      p.country || '',
      region:       p.region  || '',
      city:         p.city    || '',
      latitude:     p.latitude  || null,
      longitude:    p.longitude || null,
      vendor_sales_manager_id: p.vendor_sales_manager_id || null,
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  if (isLocked.value) {
    alert('项目已锁定，无法编辑')
    return
  }
  saving.value = true
  try {
    await updateProject(route.params.id, form.value)
    router.back()
  } catch (e) {
    alert(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function loadVsm() {
  try {
    const r = await getVendorSalesManagers()
    vendorSalesManagers.value = r.data?.data || []
  } catch (e) {
    console.warn('load vendor sales managers failed', e)
  }
}

onMounted(() => {
  dictStore.ensure('project_type')
  loadVsm()
  load()
})
</script>

<template>
  <div class="flex flex-col h-full overflow-y-auto" style="background: var(--color-bg);">

    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-3 shrink-0">
      <button @click="router.back()" class="text-[15px] active:opacity-60"
        style="color: var(--color-accent);">取消</button>
      <span class="font-serif text-[16px] font-medium">编辑项目</span>
      <button @click="save" :disabled="saving || !form.project_name.trim() || isLocked"
        class="text-[15px] font-bold active:opacity-60 disabled:opacity-40"
        style="color: var(--color-accent);">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <template v-else>
      <div v-if="isLocked" class="mx-5 mt-3 px-4 py-3 rounded-xl text-[13px]"
        style="background: #FEF3C7; color: #92400E;">
        ⚠️ 项目已锁定，所有字段只读。如需修改请先解锁。
      </div>

      <!-- 基本信息 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">基本信息</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="项目名称" v-model="form.project_name"
          :focused="focusedKey === 'project_name'" @click="focusedKey = 'project_name'" />
        <EditField label="项目类型" :model-value="projectTypeLabel" arrow
          :focused="focusedKey === 'project_type'"
          @click="focusedKey = 'project_type'; showProjectTypePicker = true" />
        <EditField label="行业" :model-value="industryLabel" arrow
          :focused="focusedKey === 'industry'"
          @click="focusedKey = 'industry'; showIndustryPicker = true" />
        <EditField label="地址" :model-value="form.address" arrow
          :focused="focusedKey === 'address'"
          @click="focusedKey = 'address'; showAddressPicker = true" />
        <EditField label="预计交付" v-model="form.delivery_forecast" type="date"
          :focused="focusedKey === 'delivery_forecast'" @click="focusedKey = 'delivery_forecast'" />
      </div>

      <!-- 详细描述 -->
      <div class="px-7 pt-5 pb-1 text-[11px] font-semibold uppercase"
        style="color: var(--color-ink-3); letter-spacing: 1px;">详细</div>
      <div class="mx-5 rounded-2xl py-1"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <EditField label="产品情况" :model-value="productSituationLabel" arrow
          :focused="focusedKey === 'product_situation'"
          @click="focusedKey = 'product_situation'; showProductSituationPicker = true" />
        <EditField label="厂商销售" :model-value="vsmLabel" arrow
          :focused="focusedKey === 'vsm'"
          @click="focusedKey = 'vsm'; showVsmPicker = true" />
        <EditField label="设计要点" v-model="form.design_issues"
          :focused="focusedKey === 'design_issues'" @click="focusedKey = 'design_issues'" />
        <EditField label="阶段说明" v-model="form.stage_description"
          :focused="focusedKey === 'stage_description'" @click="focusedKey = 'stage_description'" />
      </div>

      <div class="h-16" />
    </template>

    <!-- Pickers -->
    <PickerSheet v-model="showProjectTypePicker" title="选择项目类型"
      :options="PROJECT_TYPE_OPTIONS" v-model:selected="form.project_type" />
    <PickerSheet v-model="showIndustryPicker" title="选择行业"
      :options="INDUSTRY_OPTIONS" v-model:selected="form.industry" />
    <AddressPickerSheet v-model="showAddressPicker"
      :initial-address="form.address" @select="onAddressSelect" />
    <PickerSheet v-model="showProductSituationPicker" title="选择产品情况"
      :options="PRODUCT_SITUATION_OPTIONS" v-model:selected="form.product_situation" />
    <PickerSheet v-model="showVsmPicker" title="选择厂商销售负责人"
      :options="VSM_OPTIONS" v-model:selected="form.vendor_sales_manager_id" />
  </div>
</template>
