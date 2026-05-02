<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, updateProject, getVendorSalesManagers } from '@/api/projects'
import EditField from '@/components/common/EditField.vue'
import EditFormHeader from '@/components/common/EditFormHeader.vue'
import PickerSheet from '@/components/common/PickerSheet.vue'
import PersonPickerSheet from '@/components/common/PersonPickerSheet.vue'
import AddressPickerSheet from '@/components/common/AddressPickerSheet.vue'
import { useDictionariesStore } from '@/stores/dictionaries'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const dirty = ref(false)

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
const PRODUCT_SITUATION_OPTIONS = [
  { value: 'qualified',    label: '入围' },
  { value: 'controlled',   label: '受控' },
  { value: 'not_required', label: '无要求' },
  { value: 'unqualified',  label: '未入围' },
]
const PROJECT_TYPE_OPTIONS = computed(() =>
  dictStore.list('project_type').map(d => ({ value: d.key, label: d.label }))
)

// 厂商销售
const vendorSalesManagers = ref([])
const vsmDisplay = computed(() => {
  const u = vendorSalesManagers.value.find(x => x.id === form.value.vendor_sales_manager_id)
  return u ? (u.department ? `${u.name} · ${u.department}` : u.name) : ''
})
// 适配 PersonPickerSheet 的 options 格式
const VSM_PERSON_OPTIONS = computed(() => vendorSalesManagers.value.map(u => ({
  id: u.id, name: u.name, department: u.department,
})))

// labels for display
const projectTypeLabel = computed(() => dictStore.label('project_type', form.value.project_type))
const industryLabel = computed(() => INDUSTRY_OPTIONS.find(o => o.value === form.value.industry)?.label || form.value.industry)
const productSituationLabel = computed(() =>
  PRODUCT_SITUATION_OPTIONS.find(o => o.value === form.value.product_situation)?.label || ''
)

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
  dirty.value = true
}

// 必填检查（项目名 + 厂商销售）
const missingCount = computed(() => {
  let n = 0
  if (!form.value.project_name?.trim()) n++
  if (!form.value.vendor_sales_manager_id) n++
  return n
})

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
    dirty.value = false
  } finally {
    loading.value = false
  }
}

async function loadVsm() {
  try {
    const r = await getVendorSalesManagers()
    vendorSalesManagers.value = r.data?.data || []
  } catch (e) {
    console.warn('load vsm failed', e)
  }
}

async function save() {
  if (isLocked.value) { alert('项目已锁定，无法编辑'); return }
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

// 任何字段变化标记 dirty
function onChange() { dirty.value = true }

onMounted(() => {
  dictStore.ensure('project_type')
  loadVsm()
  load()
})
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <EditFormHeader
      title="编辑项目"
      :saving="saving"
      :dirty="dirty"
      :missing-count="missingCount"
      @cancel="router.back()"
      @save="save" />

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <div v-else class="flex-1 overflow-y-auto" style="padding: 8px 0 100px;">
      <div v-if="isLocked" class="mx-6 mt-3 px-4 py-3 rounded-xl text-[13px]"
        style="background: #FEF3C7; color: #92400E;">
        ⚠️ 项目已锁定，所有字段只读
      </div>

      <!-- 基本信息 -->
      <div style="padding: 20px 24px 10px;">
        <div style="font-size: 11px; font-weight: 600; color: var(--color-ink-3); letter-spacing: 1px; text-transform: uppercase;">基本信息</div>
      </div>
      <div class="mx-6 overflow-hidden"
        style="background: var(--color-card); border-radius: 14px; border: 1px solid var(--color-divider);">
        <EditField label="项目名称" v-model="form.project_name" required @update:modelValue="onChange" />
        <EditField label="项目类型" :model-value="projectTypeLabel" arrow placeholder="请选择"
          @click="showProjectTypePicker = true" />
        <EditField label="行业" :model-value="industryLabel" arrow placeholder="请选择"
          @click="showIndustryPicker = true" />
        <EditField label="地址" :model-value="form.address" arrow placeholder="请选择地址"
          @click="showAddressPicker = true" />
        <EditField label="预计交付" v-model="form.delivery_forecast" type="date" last
          @update:modelValue="onChange" />
      </div>

      <!-- 详细 -->
      <div style="padding: 20px 24px 10px;">
        <div style="font-size: 11px; font-weight: 600; color: var(--color-ink-3); letter-spacing: 1px; text-transform: uppercase;">详细</div>
      </div>
      <div class="mx-6 overflow-hidden"
        style="background: var(--color-card); border-radius: 14px; border: 1px solid var(--color-divider);">
        <EditField label="产品情况" :model-value="productSituationLabel" arrow placeholder="请选择" last
          @click="showProductSituationPicker = true" />
      </div>

      <!-- 厂商销售（必填，未填高亮）-->
      <div style="height: 12px;" />
      <div class="mx-6 overflow-hidden"
        :style="{
          background: !form.vendor_sales_manager_id ? '#FBE9DF' : 'var(--color-card)',
          borderRadius: '14px',
          border: !form.vendor_sales_manager_id
            ? '1px solid var(--color-accent-soft)'
            : '1px solid var(--color-divider)',
        }">
        <EditField
          label="厂商销售"
          required
          arrow
          :highlight="!form.vendor_sales_manager_id"
          :model-value="vsmDisplay"
          placeholder="请选择销售负责人"
          last
          @click="showVsmPicker = true" />
      </div>

      <!-- 备注/详细 -->
      <div style="height: 12px;" />
      <div class="mx-6 overflow-hidden"
        style="background: var(--color-card); border-radius: 14px; border: 1px solid var(--color-divider);">
        <EditField label="设计要点" v-model="form.design_issues" placeholder="补充设计要点（选填）"
          @update:modelValue="onChange" />
        <EditField label="阶段说明" v-model="form.stage_description"
          placeholder="补充阶段说明（选填）" multiline last
          @update:modelValue="onChange" />
      </div>
    </div>

    <!-- Pickers -->
    <PickerSheet v-model="showProjectTypePicker" title="选择项目类型"
      :options="PROJECT_TYPE_OPTIONS" :selected="form.project_type"
      @update:selected="(v) => { form.project_type = v; onChange() }" />
    <PickerSheet v-model="showIndustryPicker" title="选择行业"
      :options="INDUSTRY_OPTIONS" :selected="form.industry"
      @update:selected="(v) => { form.industry = v; onChange() }" />
    <PickerSheet v-model="showProductSituationPicker" title="选择产品情况"
      :options="PRODUCT_SITUATION_OPTIONS" :selected="form.product_situation"
      @update:selected="(v) => { form.product_situation = v; onChange() }" />
    <AddressPickerSheet v-model="showAddressPicker"
      :initial-address="form.address" @select="onAddressSelect" />
    <PersonPickerSheet v-model="showVsmPicker" title="选择厂商销售负责人"
      :options="VSM_PERSON_OPTIONS"
      :selected="form.vendor_sales_manager_id"
      @update:selected="(v) => { form.vendor_sales_manager_id = v; onChange() }" />
  </div>
</template>
