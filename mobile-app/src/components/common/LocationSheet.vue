<script setup>
// 共享位置（设计稿对齐 chat-pickers.jsx LocationPicker）：
//   - 顶部搜索 → 调 Nominatim search 出候选
//   - Leaflet 地图（中国高德瓦片 / 海外 OSM）
//   - 附近地点列表（reverse geocode 当前位置 + 半径搜索）
//   - 选中后「发送」带 name + address，而非裸坐标
import { ref, watch, computed, nextTick, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { Geolocation } from '@capacitor/geolocation'

const { t } = useI18n()
import { Browser } from '@capacitor/browser'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbOffset } = useKeyboardOffset()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mode:       { type: String,  default: 'share' },
  lat:        { type: Number,  default: null },
  lon:        { type: Number,  default: null },
  name:       { type: String,  default: '' },
  address:    { type: String,  default: '' },
  send:       { type: Function, default: null },   // (lat, lon, meta) => Promise
})
const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const error   = ref('')
const lat = ref(props.lat)
const lon = ref(props.lon)
const sending = ref(false)
const baseLat = ref(null)   // 起点（当前位置）
const baseLon = ref(null)
const search  = ref('')
const places  = ref([])     // [{name, address, lat, lon, distance}]
const selectedIdx = ref(0)
const searching = ref(false)

const isChina = computed(() => {
  if (lat.value == null || lon.value == null) return false
  return lat.value >= 18 && lat.value <= 54 && lon.value >= 73 && lon.value <= 135
})

// ── Nominatim 客户端（无 key, 1 req/s 限速；UA 必须）
const NOM = 'https://nominatim.openstreetmap.org'
const UA_HEADERS = { 'Accept-Language': 'zh-CN,zh,en' }

async function reverseGeocode(la, lo) {
  try {
    const r = await fetch(`${NOM}/reverse?lat=${la}&lon=${lo}&format=json&zoom=18&addressdetails=1`, {
      headers: UA_HEADERS,
    })
    if (!r.ok) return null
    const j = await r.json()
    return {
      name: j.name || j.display_name?.split(',')[0]?.trim() || t('location.nameHere'),
      address: j.display_name || '',
    }
  } catch { return null }
}

async function searchPlaces(q, la, lo) {
  searching.value = true
  try {
    // viewbox 限制在当前位置 ~5km 范围内（lon,lat,lon,lat 顺序：左下右上）
    const d = 0.05
    const vb = `${lo - d},${la - d},${lo + d},${la + d}`
    const url = `${NOM}/search?q=${encodeURIComponent(q)}&format=json&limit=8`
      + `&viewbox=${vb}&bounded=0&addressdetails=1`
    const r = await fetch(url, { headers: UA_HEADERS })
    if (!r.ok) return []
    const j = await r.json()
    return j.map(x => ({
      name: x.name || x.display_name?.split(',')[0]?.trim() || '',
      address: x.display_name || '',
      lat: parseFloat(x.lat),
      lon: parseFloat(x.lon),
      distance: distMeters(la, lo, parseFloat(x.lat), parseFloat(x.lon)),
    })).sort((a, b) => a.distance - b.distance)
  } catch { return [] }
  finally { searching.value = false }
}

function distMeters(la1, lo1, la2, lo2) {
  const R = 6371000
  const toRad = d => d * Math.PI / 180
  const dLat = toRad(la2 - la1), dLon = toRad(lo2 - lo1)
  const a = Math.sin(dLat/2)**2 + Math.cos(toRad(la1)) * Math.cos(toRad(la2)) * Math.sin(dLon/2)**2
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)))
}
function fmtDist(m) {
  if (m == null) return ''
  if (m < 1000) return `${m} m`
  return `${(m / 1000).toFixed(1)} km`
}

// ── 主流程
watch(() => props.modelValue, async v => {
  if (!v) { sending.value = false; destroyMap(); return }
  search.value = ''
  selectedIdx.value = 0
  if (props.mode === 'share') {
    await locate()
  } else {
    lat.value = props.lat; lon.value = props.lon
    baseLat.value = props.lat; baseLon.value = props.lon
    places.value = [{
      name: props.name || t('location.nameDefault'),
      address: props.address || '',
      lat: props.lat, lon: props.lon, distance: 0,
    }]
    await nextTick(); ensureMap()
  }
})

async function locate() {
  loading.value = true
  error.value = ''
  try {
    const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: false, timeout: 10000 })
    const la = pos.coords.latitude, lo = pos.coords.longitude
    lat.value = la; lon.value = lo
    baseLat.value = la; baseLon.value = lo
    await nextTick(); ensureMap()
    // 反向地理编码当前位置
    const cur = await reverseGeocode(la, lo)
    places.value = [{
      name: cur?.name || t('location.nameHere'),
      address: cur?.address || '',
      lat: la, lon: lo, distance: 0,
    }]
    selectedIdx.value = 0
  } catch (e) {
    error.value = e?.message || t('location.locFail')
  } finally {
    loading.value = false
  }
}

let searchTimer = null
watch(search, q => {
  clearTimeout(searchTimer)
  if (!q.trim() || baseLat.value == null) return
  searchTimer = setTimeout(async () => {
    const results = await searchPlaces(q.trim(), baseLat.value, baseLon.value)
    places.value = [
      ...(places.value[0]?.distance === 0 ? [places.value[0]] : []),
      ...results,
    ]
  }, 350)
})

function selectPlace(i) {
  const p = places.value[i]
  if (!p) return
  selectedIdx.value = i
  lat.value = p.lat; lon.value = p.lon
  if (map) {
    map.setView([p.lat, p.lon], 16)
    if (marker) marker.setLatLng([p.lat, p.lon])
  }
}

// ── Leaflet
const mapEl = ref(null)
let map = null, marker = null

const PIN_ICON = L.divIcon({
  html: `<svg width="28" height="36" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 0C6.27 0 0 6.27 0 14c0 9.5 14 22 14 22s14-12.5 14-22C28 6.27 21.73 0 14 0z" fill="#D97757"/>
    <circle cx="14" cy="14" r="5.5" fill="#fff"/>
  </svg>`,
  className: 'pma-pin',
  iconSize: [28, 36],
  iconAnchor: [14, 36],
})

function ensureMap() {
  if (!mapEl.value || lat.value == null) return
  if (map) {
    map.setView([lat.value, lon.value], 15)
    if (marker) marker.setLatLng([lat.value, lon.value])
    else marker = L.marker([lat.value, lon.value], { icon: PIN_ICON }).addTo(map)
    return
  }
  map = L.map(mapEl.value, { zoomControl: false, attributionControl: false })
    .setView([lat.value, lon.value], 15)

  if (isChina.value) {
    L.tileLayer(
      'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
      { subdomains: ['1', '2', '3', '4'], maxZoom: 18 }
    ).addTo(map)
  } else {
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map)
  }
  marker = L.marker([lat.value, lon.value], { icon: PIN_ICON }).addTo(map)
  setTimeout(() => map?.invalidateSize(), 250)
}

function destroyMap() {
  if (map) { map.remove(); map = null; marker = null }
}
onBeforeUnmount(destroyMap)

// 键盘弹起 → 地图容器高度变化 → 通知 Leaflet 重算
watch(kbOffset, () => {
  setTimeout(() => map?.invalidateSize(), 280)
})

// ── send / cancel
function close() {
  if (sending.value) return
  emit('update:modelValue', false)
}
async function onSend() {
  if (!props.send || sending.value || lat.value == null) return
  const sel = places.value[selectedIdx.value] || {}
  sending.value = true
  try {
    await props.send(lat.value, lon.value, {
      name: sel.name || '',
      address: sel.address || '',
    })
    emit('update:modelValue', false)
  } catch (e) {
    alert(t('location.sendFail') + (e?.message || e))
  } finally {
    sending.value = false
  }
}
function recenterToBase() {
  if (baseLat.value == null) return
  selectPlace(0)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <div class="absolute left-0 right-0 rounded-t-3xl overflow-hidden flex flex-col"
          :style="{
            background: 'var(--color-bg)',
            bottom: kbOffset + 'px',
            height: '85vh',
            maxHeight: `calc(100vh - ${kbOffset}px - 30px)`,
            paddingBottom: kbOffset > 0 ? '8px' : 'calc(8px + env(safe-area-inset-bottom))',
            transition: 'bottom 0.25s cubic-bezier(.25,.46,.45,.94), max-height 0.25s cubic-bezier(.25,.46,.45,.94)',
          }">
          <div class="w-10 h-1 rounded-full mx-auto mt-3 mb-2"
            style="background: var(--color-divider-strong);" />

          <!-- 顶部 nav: 取消 / 共享位置 / 发送 -->
          <div class="px-5 pb-3 flex items-center justify-between shrink-0">
            <button @click="close" class="text-[14px] active:opacity-60"
              style="color: var(--color-ink-3);">{{ t('location.cancel') }}</button>
            <div class="text-center">
              <p class="font-serif text-[16px] font-semibold" style="color: var(--color-ink);">
                {{ mode === 'share' ? t('location.share') : t('location.detail') }}
              </p>
              <p v-if="mode === 'share'" class="text-[11px]" style="color: var(--color-ink-3);">
                {{ t('location.pickOne') }}
              </p>
            </div>
            <button v-if="mode === 'share'"
              @click="onSend" :disabled="sending || lat == null"
              class="text-[14px] font-semibold active:opacity-60 disabled:opacity-40"
              style="color: var(--color-accent);">
              {{ sending ? t('location.sending') : t('location.send') }}
            </button>
            <span v-else style="width: 40px;"></span>
          </div>

          <!-- 搜索框 -->
          <div v-if="mode === 'share'" class="px-4 pb-2 shrink-0">
            <div class="rounded-full px-3 py-2 flex items-center gap-2"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="color: var(--color-ink-3);">
                <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="1.6"/>
                <path d="M16 16l5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              <input v-model="search" type="search"
                :placeholder="t('location.searchPh')"
                class="flex-1 bg-transparent outline-none text-[14px]"
                style="color: var(--color-ink);" />
              <span v-if="searching" class="w-3 h-3 border-2 rounded-full animate-spin"
                style="border-color: var(--color-accent); border-top-color: transparent;" />
            </div>
          </div>

          <!-- 地图 -->
          <div class="mx-4 mb-2 rounded-2xl overflow-hidden relative shrink-0"
            :style="{
              height: kbOffset > 0 ? '22vh' : '32vh',
              minHeight: kbOffset > 0 ? '140px' : '200px',
              background: '#E8E4DA',
              border: '1px solid var(--color-divider)',
              transition: 'height 0.25s ease, min-height 0.25s ease',
              contain: 'strict',
              isolation: 'isolate',
            }">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-[13px]"
              style="color: var(--color-ink-3); z-index: 10;">{{ t('location.locating') }}</div>
            <div v-else-if="error" class="absolute inset-0 flex flex-col items-center justify-center gap-2 px-6 text-center"
              style="z-index: 10;">
              <span class="text-[13px]" style="color: #C44;">{{ error }}</span>
              <button @click="locate" class="text-[12px] underline"
                style="color: var(--color-accent);">{{ t('location.retry') }}</button>
            </div>
            <div ref="mapEl" class="w-full h-full" />
            <button v-if="lat && !loading && !error && mode === 'share'"
              @click="recenterToBase"
              class="absolute bottom-3 right-3 w-9 h-9 rounded-full flex items-center justify-center active:opacity-70"
              :style="{
                background: 'rgba(255,255,255,0.95)',
                border: '1px solid var(--color-divider)',
                boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
              }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="var(--color-ink-2)" stroke-width="1.6" stroke-linecap="round"/>
                <circle cx="12" cy="12" r="6" stroke="var(--color-ink-2)" stroke-width="1.6"/>
                <circle cx="12" cy="12" r="2" fill="var(--color-accent)"/>
              </svg>
            </button>
            <span v-if="lat && !loading && !error" class="absolute top-2 right-2 text-[10px] px-2 py-1 rounded-full"
              :style="{
                background: 'rgba(255,255,255,0.92)',
                color: 'var(--color-ink-2)',
                border: '1px solid var(--color-divider)',
              }">
              {{ isChina ? t('location.mapAmap') : t('location.mapOsm') }}
            </span>
          </div>

          <!-- 附近地点列表 -->
          <div class="flex-1 overflow-y-auto" style="-webkit-overflow-scrolling: touch;">
            <div class="px-5 py-2 text-[11px] font-semibold uppercase"
              style="color: var(--color-ink-3); letter-spacing: 1px;">
              {{ search ? t('location.searchResults') : t('location.nearby') }}
            </div>
            <div v-if="!places.length" class="px-5 py-6 text-center text-[12px]"
              style="color: var(--color-ink-3);">
              {{ searching ? t('location.searching') : (loading ? '' : t('location.none')) }}
            </div>
            <button v-for="(p, i) in places" :key="i"
              @click="selectPlace(i)"
              class="w-full px-4 py-3 flex items-start gap-3 text-left active:opacity-70"
              :style="{
                background: i === selectedIdx ? 'var(--color-accent-soft)' : 'transparent',
                borderTop: i ? '1px solid var(--color-divider)' : 'none',
              }">
              <span class="inline-flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5"
                :style="{
                  background: i === selectedIdx ? 'var(--color-accent)' : '#E5EDFA',
                  color: i === selectedIdx ? '#fff' : '#4D82E0',
                }">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/>
                </svg>
              </span>
              <div class="flex-1 min-w-0">
                <div class="text-[14px] font-medium" style="color: var(--color-ink);">
                  {{ p.name || t('location.nameUntitled') }}
                </div>
                <div v-if="p.address" class="text-[11px] mt-0.5 truncate" style="color: var(--color-ink-3);">
                  {{ p.address }}
                </div>
              </div>
              <span class="text-[11px] tabular shrink-0 mt-0.5"
                :style="{ color: i === selectedIdx ? 'var(--color-accent)' : 'var(--color-ink-3)', fontWeight: i === selectedIdx ? 600 : 400 }">
                {{ i === 0 && !search ? t('location.hereDot') + fmtDist(p.distance) : fmtDist(p.distance) }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
.sheet-enter-from, .sheet-leave-to       { opacity: 0; }
</style>
