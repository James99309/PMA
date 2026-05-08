<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Geolocation } from '@capacitor/geolocation'
import { checkProjectName, createProject } from '@/api/projects'
import { reverseGeocode, searchAddress, getAddressDetail } from '@/api/customers'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()

const router = useRouter()

const form = ref({
  name: '',
  industry: '',
  description: '',
  report_source: '',
  project_type: '',
  product_situation: '',
  delivery_forecast: '',
  country: '',
  region: '',
  city: '',
  address: '',
  latitude: null,
  longitude: null,
})

const submitting = ref(false)
const locating = ref(false)
const similar = ref([])
const checking = ref(false)
const dupAcknowledged = ref(false)
const selectedDup = ref(null)
let checkTimer = null

const addressQuery = ref('')
const addressSuggestions = ref([])
const addressSearching = ref(false)
const addressSelected = ref(false)
let addressTimer = null

const activeSheet = ref(null) // 'industry' | 'report_source' | 'project_type' | 'product_situation' | 'address'

const INDUSTRIES = [
  { value: 'manufacturing', label: '制造' },
  { value: 'datacenter', label: '数据' },
  { value: 'chemical', label: '化工' },
  { value: 'energy', label: '能源' },
  { value: 'transportation', label: '交通' },
  { value: 'tunnel_underground', label: '隧道' },
  { value: 'real_estate', label: '地产' },
  { value: 'hospitality', label: '酒店' },
  { value: 'government', label: '政府' },
  { value: 'education', label: '教育' },
  { value: 'healthcare', label: '医疗' },
  { value: 'technology', label: '科技' },
  { value: 'semiconductor', label: '半导体' },
  { value: 'shipbuilding', label: '造船' },
  { value: 'finance', label: '金融' },
  { value: 'other', label: '其他' },
]

const REPORT_SOURCES = [
  { value: 'channel', label: '渠道' },
  { value: 'sales', label: '销售' },
  { value: 'marketing', label: '市场' },
]

const PROJECT_TYPES = [
  { value: 'channel_follow', label: '渠道' },
  { value: 'sales_focus', label: '销售' },
  { value: 'business_opportunity', label: '服务' },
]

const PRODUCT_SITUATIONS = [
  { value: 'qualified', label: '入围' },
  { value: 'controlled', label: '受控' },
  { value: 'not_required', label: '无要求' },
  { value: 'unqualified', label: '未入围' },
]

const industryLabel = computed(() => INDUSTRIES.find(o => o.value === form.value.industry)?.label || '')
const reportSourceLabel = computed(() => REPORT_SOURCES.find(o => o.value === form.value.report_source)?.label || '')
const projectTypeLabel = computed(() => PROJECT_TYPES.find(o => o.value === form.value.project_type)?.label || '')
const productSituationLabel = computed(() => PRODUCT_SITUATIONS.find(o => o.value === form.value.product_situation)?.label || '')

const validCount = computed(() => {
  let n = 0
  if (form.value.name.trim()) n++
  if (form.value.industry) n++
  if (form.value.description.trim()) n++
  return n
})
const totalCount = 3

const deliveryDisplay = computed(() => {
  if (!form.value.delivery_forecast) return ''
  const [y, m, d] = form.value.delivery_forecast.split('-')
  return `${y} · ${m} · ${d}`
})

watch(() => form.value.name, (val) => {
  clearTimeout(checkTimer)
  similar.value = []
  dupAcknowledged.value = false
  selectedDup.value = null
  const trimmed = val.trim()
  if (trimmed.length < 2) return
  checking.value = true
  checkTimer = setTimeout(async () => {
    try {
      const res = await checkProjectName(trimmed)
      similar.value = res.data.data?.similar || []
    } catch (e) {
      console.error('check name error', e)
    } finally {
      checking.value = false
    }
  }, 600)
})

function onAddressInput() {
  addressSelected.value = false
  clearTimeout(addressTimer)
  const q = addressQuery.value.trim()
  if (q.length < 2) { addressSuggestions.value = []; return }
  addressSearching.value = true
  addressTimer = setTimeout(async () => {
    try {
      const res = await searchAddress(q)
      addressSuggestions.value = res.data.data?.suggestions || []
    } catch (e) {
      console.error('address search error', e)
      addressSuggestions.value = []
    } finally {
      addressSearching.value = false
    }
  }, 400)
}

async function selectSuggestion(s) {
  addressSuggestions.value = []
  addressSelected.value = true
  addressQuery.value = s.name
  if (s.latitude && s.longitude) {
    try {
      const res = await reverseGeocode(s.latitude, s.longitude)
      const d = res.data.data || {}
      form.value.country   = d.country  || ''
      form.value.region    = d.region   || ''
      form.value.city      = d.city     || ''
      form.value.address   = d.address  || s.address || s.name
      form.value.latitude  = s.latitude
      form.value.longitude = s.longitude
    } catch { fillFromSuggestion(s) }
    activeSheet.value = null; return
  }
  if (s.place_id) {
    try {
      const res = await getAddressDetail(s.place_id)
      const d = res.data.data || {}
      form.value.country   = d.country   || ''
      form.value.region    = d.region    || ''
      form.value.city      = d.city      || ''
      form.value.address   = d.address   || s.address || s.name
      form.value.latitude  = d.latitude  || null
      form.value.longitude = d.longitude || null
    } catch { fillFromSuggestion(s) }
    activeSheet.value = null; return
  }
  fillFromSuggestion(s)
  activeSheet.value = null
}

function fillFromSuggestion(s) {
  form.value.address = s.address || s.name
  form.value.city    = s.district || ''
}

function clearAddress() {
  addressQuery.value = ''
  addressSelected.value = false
  addressSuggestions.value = []
  form.value.country = form.value.region = form.value.city = form.value.address = ''
  form.value.latitude = form.value.longitude = null
}

async function getLocation() {
  locating.value = true
  try {
    const pos = await Geolocation.getCurrentPosition({ timeout: 10000 })
    const lat = pos.coords.latitude
    const lng = pos.coords.longitude
    const res = await reverseGeocode(lat, lng)
    const d = res.data.data || {}
    form.value.country    = d.country  || ''
    form.value.region     = d.region   || ''
    form.value.city       = d.city     || ''
    form.value.address    = d.address  || ''
    form.value.latitude   = lat
    form.value.longitude  = lng
    addressQuery.value    = d.address  || d.city || ''
    addressSelected.value = true
    addressSuggestions.value = []
    activeSheet.value = null
  } catch (e) {
    alert('获取位置失败，请检查定位权限')
  } finally {
    locating.value = false
  }
}

async function submit() {
  if (!form.value.name.trim()) return alert('请填写项目名称')
  if (!form.value.industry) return alert('请选择项目行业')
  if (!form.value.description.trim()) return alert('请填写项目描述')
  submitting.value = true
  try {
    const res = await createProject({
      name:              form.value.name.trim(),
      industry:          form.value.industry,
      description:       form.value.description.trim(),
      report_source:     form.value.report_source     || null,
      project_type:      form.value.project_type      || null,
      product_situation: form.value.product_situation || null,
      delivery_forecast: form.value.delivery_forecast || null,
      country:           form.value.country           || null,
      region:            form.value.region            || null,
      city:              form.value.city              || null,
      address:           form.value.address           || null,
      latitude:          form.value.latitude          || null,
      longitude:         form.value.longitude         || null,
    })
    const id = res.data.data?.id
    if (id) router.replace(`/projects/${id}`)
    else router.back()
  } catch (e) {
    alert(e.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="na-root" :style="kbStyle">

    <!-- Nav bar -->
    <div class="na-nav">
      <button class="na-nav-cancel" @click="router.back()">取消</button>
      <div class="na-nav-title">
        <div class="na-serif" style="font-size:18px; font-weight:500; color:#1A1A1A;">新建项目</div>
        <div style="font-size:11px; color:#7A7570; margin-top:1px;">第 1 / 1 步</div>
      </div>
      <button class="na-btn-create" @click="submit" :disabled="submitting"
        :style="{ opacity: validCount === totalCount ? 1 : 0.4 }">
        {{ submitting ? '提交中…' : '创建' }}
      </button>
    </div>

    <!-- Progress bar -->
    <div class="na-progress">
      <div class="na-progress-track">
        <div class="na-progress-fill" :style="{ width: (validCount / totalCount * 100) + '%' }" />
      </div>
      <span class="na-progress-label">{{ validCount }} / {{ totalCount }} 必填</span>
    </div>

    <!-- Scrollable content -->
    <div class="na-scroll">

      <!-- 基本 -->
      <div class="na-sec-header"><span class="na-sec-label">基本</span></div>
      <div class="na-bigfield">
        <div class="na-field-label">项目名称<span class="na-required">*</span></div>
        <input
          v-model="form.name"
          class="na-big-input"
          type="text"
          placeholder="给这个项目起个名字…"
          autocomplete="off"
        />
        <p v-if="checking" class="na-checking">查重中…</p>
        <!-- Direction A dedup warning -->
        <div v-if="similar.length && !dupAcknowledged" class="na-dup-card">
          <div class="na-dup-header">
            <span class="na-dup-icon">
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                <path d="M6 3v3.5M6 8.5v.5" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/>
                <circle cx="6" cy="6" r="5" stroke="#fff" stroke-width="1.4"/>
              </svg>
            </span>
            <div>
              <div class="na-dup-title na-serif">发现 {{ similar.length }} 个名称相似的项目</div>
              <div class="na-dup-sub na-serif">报备前请确认是否重复</div>
            </div>
          </div>
          <div class="na-dup-list">
            <div v-for="(s, i) in similar" :key="s.id" class="na-dup-row" :class="{ 'na-dup-row-last': i === similar.length - 1 }">
              <div class="na-dup-row-top">
                <span class="na-dup-name na-serif">{{ s.name }}</span>
                <span v-if="s.auth_code" class="na-dup-authcode">{{ s.auth_code }}</span>
              </div>
              <div class="na-dup-row-meta">
                <span class="na-dup-badge" :class="s.score >= 80 ? 'na-dup-badge-high' : 'na-dup-badge-low'">
                  {{ s.score >= 80 ? '高度相似' : '部分相似' }}
                </span>
              </div>
            </div>
          </div>
          <div class="na-dup-actions">
            <button class="na-dup-btn-view" @click="selectedDup = similar[0]">查看已有项目</button>
            <button class="na-dup-btn-create" @click="dupAcknowledged = true">仍要创建</button>
          </div>
        </div>
      </div>

      <!-- 地址 card (under 基本, no section header) -->
      <div class="na-card" style="margin-bottom: 4px;">
        <div class="na-row" @click="activeSheet = 'address'">
          <span class="na-row-label">项目地址</span>
          <span class="na-row-val-wrap">
            <span class="na-row-val na-row-val-address" :class="{ 'na-placeholder': !form.address }">{{ form.address || '搜索地址或选点' }}</span>
            <span class="na-pin-circle">
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                <path d="M8 14s5-4.5 5-9a5 5 0 10-10 0c0 4.5 5 9 5 9z" stroke="#D97757" stroke-width="1.4"/>
                <circle cx="8" cy="5" r="1.6" fill="#D97757"/>
              </svg>
            </span>
          </span>
        </div>
      </div>

      <!-- 分类 -->
      <div class="na-sec-header"><span class="na-sec-label">分类</span></div>
      <div class="na-card">
        <div class="na-row na-row-border" @click="activeSheet = 'industry'">
          <span class="na-row-label">项目行业<span class="na-required">*</span></span>
          <span class="na-row-val-wrap">
            <span class="na-row-val" :class="{ 'na-placeholder': !form.industry }">{{ industryLabel || '请选择' }}</span>
            <svg width="8" height="12" viewBox="0 0 8 12" fill="none"><path d="M2 2l4 4-4 4" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round"/></svg>
          </span>
        </div>
        <div class="na-row na-row-border" @click="activeSheet = 'report_source'">
          <span class="na-row-label">报备来源</span>
          <span class="na-row-val-wrap">
            <span class="na-row-val" :class="{ 'na-placeholder': !form.report_source }">{{ reportSourceLabel || '请选择' }}</span>
            <svg width="8" height="12" viewBox="0 0 8 12" fill="none"><path d="M2 2l4 4-4 4" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round"/></svg>
          </span>
        </div>
        <div class="na-row na-row-border" @click="activeSheet = 'project_type'">
          <span class="na-row-label">项目类型</span>
          <span class="na-row-val-wrap">
            <span class="na-row-val" :class="{ 'na-placeholder': !form.project_type }">{{ projectTypeLabel || '请选择' }}</span>
            <svg width="8" height="12" viewBox="0 0 8 12" fill="none"><path d="M2 2l4 4-4 4" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round"/></svg>
          </span>
        </div>
        <div class="na-row" @click="activeSheet = 'product_situation'">
          <span class="na-row-label">品牌情况</span>
          <span class="na-row-val-wrap">
            <span class="na-row-val" :class="{ 'na-placeholder': !form.product_situation }">{{ productSituationLabel || '请选择' }}</span>
            <svg width="8" height="12" viewBox="0 0 8 12" fill="none"><path d="M2 2l4 4-4 4" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round"/></svg>
          </span>
        </div>
      </div>

      <!-- 项目描述 -->
      <div class="na-sec-header">
        <span class="na-sec-label">项目描述</span>
        <span style="font-size:11px; color:#7A7570;">必填</span>
      </div>
      <div class="na-bigfield">
        <textarea
          v-model="form.description"
          class="na-notes-textarea"
          placeholder="项目背景、客户痛点、初步方案…"
          rows="4"
        />
      </div>

      <!-- 时间 -->
      <div class="na-sec-header"><span class="na-sec-label">时间</span></div>
      <div class="na-card">
        <div class="na-row" style="position:relative;">
          <span class="na-row-label">交付预测</span>
          <span class="na-row-val-wrap">
            <span class="na-row-val" :class="{ 'na-placeholder': !form.delivery_forecast }">{{ deliveryDisplay || '选择日期' }}</span>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"
              :style="{ opacity: form.delivery_forecast ? 1 : 0.4 }">
              <rect x="2" y="3" width="12" height="11" rx="2"
                :stroke="form.delivery_forecast ? '#D97757' : '#7A7570'" stroke-width="1.3"/>
              <path d="M2 6h12M5 1v3M11 1v3"
                :stroke="form.delivery_forecast ? '#D97757' : '#7A7570'" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </span>
          <input v-model="form.delivery_forecast" type="date"
            style="position:absolute; inset:0; width:100%; height:100%; opacity:0; cursor:pointer;" />
        </div>
      </div>

    </div><!-- /scroll -->

    <!-- Footer hint -->
    <div class="na-footer-hint" :class="{ 'na-footer-complete': validCount === totalCount }">
      <template v-if="validCount === totalCount">所有必填已完成 · 可以创建</template>
      <template v-else>* 为必填项 · 其他可在详情页随时补充</template>
    </div>

    <!-- ── Sheet: 行业 ── -->
    <div v-if="activeSheet === 'industry'" class="na-overlay">
      <div class="na-overlay-bg" @click="activeSheet = null" />
      <div class="na-sheet">
        <div class="na-sheet-handle" />
        <div class="na-sheet-head">
          <div class="na-sec-label" style="margin-bottom:4px;">选择</div>
          <div class="na-serif" style="font-size:22px; font-weight:500;">项目行业</div>
        </div>
        <div class="na-chip-grid">
          <button v-for="o in INDUSTRIES" :key="o.value" class="na-chip"
            :class="{ 'na-chip-on': form.industry === o.value }"
            @click="form.industry = o.value; activeSheet = null">{{ o.label }}</button>
        </div>
      </div>
    </div>

    <!-- ── Sheet: 报备来源 ── -->
    <div v-if="activeSheet === 'report_source'" class="na-overlay">
      <div class="na-overlay-bg" @click="activeSheet = null" />
      <div class="na-sheet">
        <div class="na-sheet-handle" />
        <div class="na-sheet-head">
          <div class="na-sec-label" style="margin-bottom:4px;">选择</div>
          <div class="na-serif" style="font-size:22px; font-weight:500;">报备来源</div>
        </div>
        <div class="na-chip-grid">
          <button v-for="o in REPORT_SOURCES" :key="o.value" class="na-chip"
            :class="{ 'na-chip-on': form.report_source === o.value }"
            @click="form.report_source = o.value; activeSheet = null">{{ o.label }}</button>
        </div>
      </div>
    </div>

    <!-- ── Sheet: 项目类型 ── -->
    <div v-if="activeSheet === 'project_type'" class="na-overlay">
      <div class="na-overlay-bg" @click="activeSheet = null" />
      <div class="na-sheet">
        <div class="na-sheet-handle" />
        <div class="na-sheet-head">
          <div class="na-sec-label" style="margin-bottom:4px;">选择</div>
          <div class="na-serif" style="font-size:22px; font-weight:500;">项目类型</div>
        </div>
        <div class="na-chip-grid">
          <button v-for="o in PROJECT_TYPES" :key="o.value" class="na-chip"
            :class="{ 'na-chip-on': form.project_type === o.value }"
            @click="form.project_type = o.value; activeSheet = null">{{ o.label }}</button>
        </div>
      </div>
    </div>

    <!-- ── Sheet: 品牌情况 ── -->
    <div v-if="activeSheet === 'product_situation'" class="na-overlay">
      <div class="na-overlay-bg" @click="activeSheet = null" />
      <div class="na-sheet">
        <div class="na-sheet-handle" />
        <div class="na-sheet-head">
          <div class="na-sec-label" style="margin-bottom:4px;">选择</div>
          <div class="na-serif" style="font-size:22px; font-weight:500;">品牌情况</div>
        </div>
        <div class="na-chip-grid">
          <button v-for="o in PRODUCT_SITUATIONS" :key="o.value" class="na-chip"
            :class="{ 'na-chip-on': form.product_situation === o.value }"
            @click="form.product_situation = o.value; activeSheet = null">{{ o.label }}</button>
        </div>
      </div>
    </div>

    <!-- ── Sheet: 地址 ── -->
    <div v-if="activeSheet === 'address'" class="na-overlay">
      <div class="na-overlay-bg" @click="activeSheet = null" />
      <div class="na-sheet na-sheet-address">
        <div class="na-sheet-handle" />
        <div class="na-addr-header">
          <button class="na-addr-cancel" @click="activeSheet = null">取消</button>
          <div class="na-serif" style="font-size:18px; font-weight:500;">选择地址</div>
          <div style="width:40px;" />
        </div>
        <div class="na-addr-search-row">
          <div class="na-addr-search-wrap">
            <svg class="na-addr-search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="5" stroke="#7A7570" stroke-width="1.4"/>
              <path d="M11 11l3 3" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round"/>
            </svg>
            <input
              v-model="addressQuery"
              class="na-addr-input"
              type="text"
              placeholder="搜索地址…"
              autocomplete="off"
              @input="onAddressInput"
            />
            <div v-if="addressSearching" class="na-addr-spin" />
          </div>
          <button class="na-gps-btn" @click="getLocation" :disabled="locating" :style="{ opacity: locating ? 0.5 : 1 }">
            <svg v-if="!locating" width="20" height="20" fill="none" stroke="#D97757" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            <div v-else class="na-gps-spin" />
          </button>
        </div>
        <div class="na-addr-results">
          <div v-if="addressSuggestions.length" class="na-suggestions">
            <div v-for="(s, i) in addressSuggestions" :key="s.name + s.address" class="na-suggestion"
              :class="{ 'na-suggestion-last': i === addressSuggestions.length - 1 }"
              @click="selectSuggestion(s)">
              <p class="na-suggestion-name">{{ s.name }}</p>
              <p v-if="s.district || s.address" class="na-suggestion-sub">{{ s.district || s.address }}</p>
            </div>
          </div>
          <div v-if="addressSelected && form.address" class="na-addr-selected">
            <div class="na-addr-selected-info">
              <p v-if="form.region || form.city" class="na-addr-region">{{ [form.region, form.city].filter(Boolean).join(' · ') }}</p>
              <p class="na-addr-text">{{ form.address }}</p>
            </div>
            <button class="na-addr-clear" @click="clearAddress">清除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Sheet: 查重详情 ── -->
    <div v-if="selectedDup" class="na-overlay">
      <div class="na-overlay-bg" @click="selectedDup = null" />
      <div class="na-sheet na-sheet-dup">
        <div class="na-sheet-handle" />
        <div class="na-dup-detail-header">
          <button class="na-addr-cancel" @click="selectedDup = null">返回表单</button>
          <div class="na-serif" style="font-size:16px; font-weight:500;">已有项目</div>
          <div style="width:60px;" />
        </div>
        <div class="na-dup-detail-scroll">
          <!-- Hero -->
          <div class="na-dup-hero">
            <div v-if="selectedDup.auth_code" class="na-dup-hero-code">{{ selectedDup.auth_code }}</div>
            <div class="na-serif na-dup-hero-name">{{ selectedDup.name }}</div>
          </div>
          <!-- Name comparison -->
          <div class="na-dup-compare-card">
            <div class="na-dup-compare-header">
              <span class="na-sec-label">名称对比</span>
            </div>
            <div class="na-dup-compare-row na-dup-compare-row-border">
              <span class="na-dup-compare-label">已有</span>
              <span class="na-serif na-dup-compare-val">{{ selectedDup.name }}</span>
            </div>
            <div class="na-dup-compare-row">
              <span class="na-dup-compare-label na-dup-compare-label-accent">本次</span>
              <span class="na-serif na-dup-compare-val">{{ form.name }}</span>
              <span class="na-dup-badge na-dup-badge-sm" :class="selectedDup.score >= 80 ? 'na-dup-badge-high' : 'na-dup-badge-low'">
                {{ selectedDup.score >= 80 ? '高度相似' : '部分相似' }}
              </span>
            </div>
          </div>
        </div>
        <!-- Footer -->
        <div class="na-dup-detail-footer">
          <button class="na-dup-detail-back" @click="selectedDup = null">返回修改</button>
          <button class="na-dup-detail-go" @click="router.push(`/projects/${selectedDup.id}`)">
            跳到这个项目
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 6h6m-2-3l3 3-3 3" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ── Design tokens ── */
.na-root {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #F7F5F2;
  color: #1A1A1A;
  font-family: -apple-system, 'SF Pro Text', 'PingFang SC', system-ui, sans-serif;
  padding-top: 54px;
}
.na-serif { font-family: 'Noto Serif SC', Georgia, serif; }

/* ── Nav ── */
.na-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px 8px;
}
.na-nav-cancel {
  font-size: 15px;
  color: #3A3A3A;
  font-weight: 500;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}
.na-nav-title { text-align: center; }
.na-btn-create {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: #D97757;
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

/* ── Progress ── */
.na-progress {
  padding: 0 24px 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.na-progress-track {
  flex: 1;
  height: 3px;
  background: rgba(0,0,0,0.06);
  border-radius: 2px;
  overflow: hidden;
}
.na-progress-fill {
  height: 100%;
  background: #D97757;
  border-radius: 2px;
  transition: width 0.3s;
}
.na-progress-label {
  font-size: 11px;
  color: #7A7570;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* ── Scroll area ── */
.na-scroll {
  flex: 1;
  overflow: auto;
  padding: 8px 0 100px;
  -webkit-overflow-scrolling: touch;
}

/* ── Section header ── */
.na-sec-header {
  padding: 20px 24px 10px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.na-sec-label {
  font-size: 11px;
  font-weight: 600;
  color: #7A7570;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* ── BigField ── */
.na-bigfield { padding: 0 24px 16px; }
.na-field-label {
  font-size: 11px;
  font-weight: 600;
  color: #7A7570;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}
.na-required { color: #D97757; margin-left: 3px; }
.na-big-input {
  width: 100%;
  font-family: 'Noto Serif SC', Georgia, serif;
  font-size: 22px;
  font-weight: 500;
  color: #1A1A1A;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 10px 0 12px;
  outline: none;
  line-height: 1.3;
  box-sizing: border-box;
}
.na-big-input::placeholder {
  font-style: italic;
  color: #7A7570;
}
.na-notes-textarea {
  width: 100%;
  font-family: 'Noto Serif SC', Georgia, serif;
  font-size: 16px;
  font-weight: 500;
  color: #1A1A1A;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 12px;
  padding: 14px 16px;
  outline: none;
  resize: none;
  line-height: 1.55;
  min-height: 90px;
  box-sizing: border-box;
}
.na-notes-textarea::placeholder {
  font-style: italic;
  color: #7A7570;
}

/* ── Dedup ── */
.na-checking { margin-top: 4px; font-size: 11px; color: #7A7570; }
.na-similar-list { margin-top: 8px; }
.na-similar-title { font-size: 11px; color: #D97757; font-weight: 600; margin-bottom: 4px; }
.na-similar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FEF3EE;
  border: 1px solid rgba(217,119,87,0.2);
  border-radius: 10px;
  padding: 8px 12px;
  margin-bottom: 6px;
  cursor: pointer;
}
.na-similar-name { font-size: 12px; color: #1A1A1A; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 8px; }
.na-similar-score { font-size: 11px; color: #D97757; flex-shrink: 0; }

/* ── Card + Row ── */
.na-card {
  margin: 0 24px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.06);
  overflow: hidden;
}
.na-row {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  gap: 10px;
}
.na-row-border { border-bottom: 1px solid rgba(0,0,0,0.06); }
.na-row-label { font-size: 14px; color: #3A3A3A; font-weight: 500; flex-shrink: 0; }
.na-row-val-wrap { display: inline-flex; align-items: center; gap: 8px; flex: 1; justify-content: flex-end; overflow: hidden; }
.na-row-val { font-size: 14px; color: #1A1A1A; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.na-row-val-address { max-width: 170px; }
.na-placeholder { color: #7A7570 !important; font-weight: 400 !important; }
.na-pin-circle {
  width: 30px;
  height: 30px;
  border-radius: 15px;
  background: #F4E4D8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ── Footer hint ── */
.na-footer-hint {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  padding: 10px 20px 28px;
  background: linear-gradient(to bottom, rgba(247,245,242,0), rgba(247,245,242,0.95) 30%);
  font-size: 12px;
  color: #7A7570;
  text-align: center;
  font-family: 'Noto Serif SC', Georgia, serif;
  font-style: italic;
  pointer-events: none;
  transition: color 0.3s;
}
.na-footer-complete { color: #D97757; }

/* ── Overlay / Sheets ── */
.na-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
}
.na-overlay-bg {
  position: absolute;
  inset: 0;
  background: rgba(20,20,20,0.36);
}
.na-sheet {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  background: #F7F5F2;
  border-radius: 24px 24px 0 0;
  box-shadow: 0 -10px 40px rgba(0,0,0,0.18);
  padding: 12px 0 34px;
  max-height: 72%;
  overflow: auto;
}
.na-sheet-address {
  max-height: 82%;
  display: flex;
  flex-direction: column;
  padding-bottom: 0;
  overflow: hidden;
}
.na-sheet-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: rgba(0,0,0,0.15);
  margin: 0 auto 14px;
}
.na-sheet-head { padding: 0 24px 16px; }
.na-chip-grid {
  padding: 0 24px 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.na-chip {
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  background: #fff;
  color: #3A3A3A;
  border: 1px solid rgba(0,0,0,0.10);
  cursor: pointer;
  font-family: inherit;
}
.na-chip-on {
  background: #1A1A1A;
  color: #fff;
  border-color: transparent;
}

/* ── Address sheet ── */
.na-addr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px 12px;
  flex-shrink: 0;
}
.na-addr-cancel {
  font-size: 15px;
  color: #7A7570;
  background: none;
  border: none;
  cursor: pointer;
}
.na-addr-search-row {
  padding: 0 16px 8px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}
.na-addr-search-wrap {
  flex: 1;
  position: relative;
}
.na-addr-search-icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.na-addr-input {
  width: 100%;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 12px;
  padding: 10px 12px 10px 34px;
  font-size: 15px;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}
.na-addr-spin {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  border: 2px solid #D97757;
  border-top-color: transparent;
  border-radius: 50%;
  animation: na-spin 0.7s linear infinite;
}
.na-gps-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 12px;
  cursor: pointer;
  flex-shrink: 0;
}
.na-gps-spin {
  width: 16px;
  height: 16px;
  border: 2px solid #D97757;
  border-top-color: transparent;
  border-radius: 50%;
  animation: na-spin-plain 0.7s linear infinite;
}
.na-addr-results {
  flex: 1;
  overflow: auto;
  padding: 4px 16px 28px;
  -webkit-overflow-scrolling: touch;
}
.na-suggestions {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 8px;
}
.na-suggestion {
  padding: 12px 14px;
  cursor: pointer;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.na-suggestion-last { border-bottom: none; }
.na-suggestion-name { font-size: 14px; color: #1A1A1A; font-weight: 500; }
.na-suggestion-sub { font-size: 12px; color: #7A7570; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.na-addr-selected {
  background: #FEF3EE;
  border: 1px solid rgba(217,119,87,0.15);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.na-addr-selected-info { flex: 1; min-width: 0; }
.na-addr-region { font-size: 11px; color: #D97757; margin-bottom: 2px; }
.na-addr-text { font-size: 13px; color: #1A1A1A; word-break: break-all; }
.na-addr-clear { font-size: 12px; color: #7A7570; background: none; border: none; cursor: pointer; flex-shrink: 0; margin-top: 2px; }

/* ── Animations ── */
@keyframes na-spin {
  0%   { transform: translateY(-50%) rotate(0deg); }
  100% { transform: translateY(-50%) rotate(360deg); }
}
@keyframes na-spin-plain {
  to { transform: rotate(360deg); }
}

/* ── Dedup warning card ── */
.na-dup-card {
  margin: 0 24px 12px;
  background: rgba(217,119,87,0.08);
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.na-dup-header { display: flex; align-items: flex-start; gap: 10px; }
.na-dup-icon {
  width: 22px; height: 22px; border-radius: 11px; background: #D97757;
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.na-dup-title { font-size: 15px; font-weight: 500; color: #1A1A1A; line-height: 1.4; }
.na-dup-sub { font-size: 12px; color: #7A7570; margin-top: 2px; line-height: 1.5; font-style: italic; }
.na-dup-list { background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06); }
.na-dup-row { padding: 12px 14px; border-bottom: 1px solid rgba(0,0,0,0.06); display: flex; flex-direction: column; gap: 5px; }
.na-dup-row-last { border-bottom: none; }
.na-dup-row-top { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.na-dup-name { font-size: 14px; font-weight: 500; color: #1A1A1A; flex: 1; line-height: 1.3; }
.na-dup-authcode { font-size: 11px; color: #7A7570; flex-shrink: 0; font-variant-numeric: tabular-nums; }
.na-dup-row-meta { display: flex; align-items: center; gap: 8px; }
.na-dup-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; color: #fff; font-weight: 600; letter-spacing: 0.3px; }
.na-dup-badge-high { background: #D97757; }
.na-dup-badge-low { background: #C2BBB3; }
.na-dup-badge-sm { font-size: 10px; padding: 2px 6px; }
.na-dup-actions { display: flex; gap: 8px; }
.na-dup-btn-view {
  flex: 1; padding: 10px 12px; border-radius: 10px;
  background: #fff; border: 1px solid rgba(0,0,0,0.10);
  font-size: 13px; font-weight: 500; color: #3A3A3A; cursor: pointer; font-family: inherit;
}
.na-dup-btn-create {
  flex: 1; padding: 10px 12px; border-radius: 10px;
  background: #1A1A1A; border: none;
  font-size: 13px; font-weight: 600; color: #fff; cursor: pointer; font-family: inherit;
}

/* ── Dedup detail sheet ── */
.na-sheet-dup {
  max-height: 78%; display: flex; flex-direction: column; overflow: hidden; padding-bottom: 0;
}
.na-dup-detail-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px 12px; flex-shrink: 0;
}
.na-dup-detail-scroll { flex: 1; overflow: auto; -webkit-overflow-scrolling: touch; }
.na-dup-hero { padding: 8px 24px 20px; }
.na-dup-hero-code { font-size: 11px; font-weight: 500; color: #7A7570; letter-spacing: 0.5px; margin-bottom: 6px; }
.na-dup-hero-name { font-size: 26px; font-weight: 500; color: #1A1A1A; line-height: 1.25; letter-spacing: -0.3px; }
.na-dup-compare-card {
  margin: 0 24px 20px; background: #fff;
  border-radius: 14px; border: 1px solid rgba(0,0,0,0.06); overflow: hidden;
}
.na-dup-compare-header { padding: 14px 16px 10px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.na-dup-compare-row { padding: 12px 16px; display: flex; align-items: center; gap: 10px; }
.na-dup-compare-row-border { border-bottom: 1px solid rgba(0,0,0,0.06); }
.na-dup-compare-label { font-size: 11px; color: #7A7570; width: 36px; flex-shrink: 0; }
.na-dup-compare-label-accent { color: #D97757; font-weight: 600; }
.na-dup-compare-val { font-size: 15px; color: #1A1A1A; flex: 1; }
.na-dup-detail-footer {
  padding: 10px 16px 28px; background: rgba(247,245,242,0.95);
  border-top: 1px solid rgba(0,0,0,0.06); display: flex; gap: 8px; flex-shrink: 0;
}
.na-dup-detail-back {
  flex: 1; padding: 14px 12px; border-radius: 14px;
  background: #fff; border: 1px solid rgba(0,0,0,0.10);
  font-size: 14px; font-weight: 600; color: #3A3A3A; cursor: pointer; font-family: inherit;
}
.na-dup-detail-go {
  flex: 1.4; padding: 14px 12px; border-radius: 14px;
  background: #1A1A1A; border: none;
  font-size: 14px; font-weight: 600; color: #fff;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  cursor: pointer; font-family: inherit;
}
</style>
