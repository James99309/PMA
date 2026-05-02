<script setup>
// 在程序内显示地图（OSM iframe 嵌入），两种模式：
//   mode='share' → 取当前定位 + 「发送」按钮
//   mode='view'  → 已知 lat/lon 的查看
import { ref, watch, computed } from 'vue'
import { Geolocation } from '@capacitor/geolocation'
import { Browser } from '@capacitor/browser'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mode:       { type: String,  default: 'share' },        // 'share' | 'view'
  lat:        { type: Number,  default: null },
  lon:        { type: Number,  default: null },
  send:       { type: Function, default: null },          // mode=share 必传 (lat,lon)
})
const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const error   = ref('')
const lat = ref(props.lat)
const lon = ref(props.lon)
const sending = ref(false)

watch(() => props.modelValue, async v => {
  if (!v) { sending.value = false; return }
  if (props.mode === 'share') {
    await locate()
  } else {
    lat.value = props.lat
    lon.value = props.lon
  }
})

async function locate() {
  loading.value = true
  error.value = ''
  try {
    const pos = await Geolocation.getCurrentPosition({
      enableHighAccuracy: false,
      timeout: 10000,
    })
    lat.value = pos.coords.latitude
    lon.value = pos.coords.longitude
  } catch (e) {
    error.value = e?.message || '定位失败'
  } finally {
    loading.value = false
  }
}

// OSM 嵌入 URL — bbox 中心 + marker
const mapUrl = computed(() => {
  if (lat.value == null || lon.value == null) return ''
  const d = 0.005  // ~500m 半径
  const minLon = (lon.value - d).toFixed(6)
  const minLat = (lat.value - d).toFixed(6)
  const maxLon = (lon.value + d).toFixed(6)
  const maxLat = (lat.value + d).toFixed(6)
  return `https://www.openstreetmap.org/export/embed.html?bbox=${minLon}%2C${minLat}%2C${maxLon}%2C${maxLat}&layer=mapnik&marker=${lat.value}%2C${lon.value}`
})

function close() {
  if (sending.value) return
  emit('update:modelValue', false)
}
async function onSend() {
  if (!props.send || sending.value || lat.value == null) return
  sending.value = true
  try {
    await props.send(lat.value, lon.value)
    emit('update:modelValue', false)
  } catch (e) {
    alert('发送失败：' + (e?.message || e))
  } finally {
    sending.value = false
  }
}
function openInSystemMap() {
  if (lat.value == null) return
  const u = `https://maps.apple.com/?q=${lat.value},${lon.value}`
  Browser.open({ url: u }).catch(() => window.open(u, '_blank'))
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/40" @click="close" />
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl overflow-hidden flex flex-col"
          :style="{
            background: 'var(--color-bg)',
            maxHeight: '78vh',
            paddingBottom: 'calc(12px + env(safe-area-inset-bottom))',
          }">
          <div class="w-10 h-1 rounded-full mx-auto mt-3 mb-3"
            style="background: var(--color-divider-strong);" />
          <div class="px-5 pb-3 flex items-center justify-between">
            <button @click="close" class="text-[14px] active:opacity-60"
              style="color: var(--color-ink-3);">取消</button>
            <p class="font-serif text-[16px] font-semibold" style="color: var(--color-ink);">
              {{ mode === 'share' ? '共享位置' : '位置详情' }}
            </p>
            <button v-if="mode==='share' && lat" @click="locate" :disabled="loading"
              class="text-[14px] active:opacity-60 disabled:opacity-50"
              style="color: var(--color-accent);">{{ loading ? '定位中…' : '重定位' }}</button>
            <span v-else style="width: 50px;"></span>
          </div>

          <!-- map -->
          <div class="mx-4 mb-3 rounded-2xl overflow-hidden"
            style="height: 38vh; min-height: 240px; background: #E8E4DA; border: 1px solid var(--color-divider);">
            <div v-if="loading" class="w-full h-full flex items-center justify-center text-[13px]"
              style="color: var(--color-ink-3);">定位中…</div>
            <div v-else-if="error" class="w-full h-full flex flex-col items-center justify-center gap-2 px-6 text-center">
              <span class="text-[13px]" style="color: #C44;">{{ error }}</span>
              <button @click="locate" class="text-[12px] underline"
                style="color: var(--color-accent);">重试</button>
            </div>
            <iframe v-else-if="mapUrl" :src="mapUrl"
              class="w-full h-full block"
              style="border: 0;" loading="lazy" referrerpolicy="no-referrer" />
          </div>

          <!-- 坐标 + 操作 -->
          <div v-if="lat" class="mx-4 mb-3 rounded-2xl px-4 py-3 flex items-center gap-3"
            style="background: var(--color-card); border: 1px solid var(--color-divider);">
            <span class="inline-flex items-center justify-center w-9 h-9 rounded-full"
              style="background: #E5EDFA; color: #4D82E0;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/>
              </svg>
            </span>
            <div class="min-w-0 flex-1">
              <div class="text-[13.5px] font-medium" style="color: var(--color-ink);">当前位置</div>
              <div class="text-[11px] tabular mt-0.5" style="color: var(--color-ink-3);">
                {{ Number(lat).toFixed(5) }}, {{ Number(lon).toFixed(5) }}
              </div>
            </div>
            <button @click="openInSystemMap"
              class="text-[12px] active:opacity-60"
              style="color: var(--color-accent);">系统地图打开</button>
          </div>

          <div v-if="mode==='share'" class="mx-4 flex gap-2">
            <button @click="close"
              class="flex-1 rounded-xl py-3 text-[14px]"
              style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">取消</button>
            <button @click="onSend" :disabled="sending || !lat"
              class="flex-1 rounded-xl py-3 text-[14px] font-semibold text-white disabled:opacity-50"
              style="background: var(--color-accent);">
              {{ sending ? '发送中…' : '发送位置' }}
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
