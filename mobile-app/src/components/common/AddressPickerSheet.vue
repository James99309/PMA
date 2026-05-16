<script setup>
// 地址选择器 sheet —— 自动匹配 + GPS 定位
// 用法：
//   <AddressPickerSheet
//     v-model="show"
//     :initial-address="form.address"
//     @select="onSelect" />
//
// emit('select', { country, region, city, address, latitude, longitude })
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Geolocation } from '@capacitor/geolocation'
import { searchAddress, reverseGeocode, getAddressDetail } from '@/api/customers'
const { t } = useI18n()

const props = defineProps({
  modelValue:    { type: Boolean, default: false },
  initialAddress:{ type: String,  default: '' },
})
const emit = defineEmits(['update:modelValue', 'select'])

const query = ref('')
const suggestions = ref([])
const searching = ref(false)
const locating = ref(false)
let timer = null

watch(() => props.modelValue, (v) => {
  if (v) {
    query.value = props.initialAddress || ''
    suggestions.value = []
  }
})

function close() { emit('update:modelValue', false) }

function onInput() {
  clearTimeout(timer)
  const q = query.value.trim()
  if (q.length < 2) { suggestions.value = []; return }
  searching.value = true
  timer = setTimeout(async () => {
    try {
      const r = await searchAddress(q)
      suggestions.value = r.data?.data?.suggestions || []
    } catch (e) {
      console.error('address search', e)
      suggestions.value = []
    } finally {
      searching.value = false
    }
  }, 400)
}

function emitSelected(d) {
  emit('select', {
    country:  d.country  || '',
    region:   d.region   || '',
    city:     d.city     || '',
    address:  d.address  || '',
    latitude: d.latitude  ?? null,
    longitude:d.longitude ?? null,
  })
  close()
}

async function selectSuggestion(s) {
  if (s.latitude && s.longitude) {
    try {
      const r = await reverseGeocode(s.latitude, s.longitude)
      const d = r.data?.data || {}
      emitSelected({
        country: d.country, region: d.region, city: d.city,
        address: d.address || s.address || s.name,
        latitude: s.latitude, longitude: s.longitude,
      })
      return
    } catch {}
  }
  if (s.place_id) {
    try {
      const r = await getAddressDetail(s.place_id)
      const d = r.data?.data || {}
      emitSelected({
        country: d.country, region: d.region, city: d.city,
        address: d.address || s.address || s.name,
        latitude: d.latitude, longitude: d.longitude,
      })
      return
    } catch {}
  }
  emitSelected({
    address: s.address || s.name,
    city: s.district || '',
  })
}

async function getLocation() {
  if (locating.value) return
  locating.value = true
  try {
    const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true })
    const r = await reverseGeocode(pos.coords.latitude, pos.coords.longitude)
    const d = r.data?.data || {}
    emitSelected({
      country: d.country, region: d.region, city: d.city,
      address: d.address || t('common.addrCurrent'),
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
    })
  } catch (e) {
    alert(t('common.addrLocateFail', { msg: e.message || e }))
  } finally {
    locating.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <transition name="ap">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(0,0,0,0.32);" @click.self="close">
        <div class="mt-auto rounded-t-3xl flex flex-col"
          style="background: var(--color-bg); max-height: 88vh; min-height: 60vh;">

          <!-- Header -->
          <div class="px-5 pt-4 pb-2 flex items-center justify-between shrink-0">
            <button @click="close" class="text-[13px]"
              style="color: var(--color-ink-3);">{{ t('common.cancel') }}</button>
            <span class="font-serif" style="font-size: 16px; font-weight: 500;">{{ t('common.addrTitle') }}</span>
            <span class="w-8" />
          </div>

          <!-- Search bar + GPS -->
          <div class="px-5 pb-3 shrink-0 flex items-center gap-2">
            <div class="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <circle cx="7" cy="7" r="5" stroke="#7A7570" stroke-width="1.4" />
                <path d="M11 11l3 3" stroke="#7A7570" stroke-width="1.4" stroke-linecap="round" />
              </svg>
              <input v-model="query" @input="onInput"
                type="text" :placeholder="t('common.addrSearchPh')"
                autocomplete="off"
                class="flex-1 bg-transparent outline-none text-[14px]"
                style="font-family: var(--font-sans);" />
              <div v-if="searching" class="w-3 h-3 border-2 rounded-full animate-spin"
                style="border-color: var(--color-accent); border-top-color: transparent;" />
            </div>
            <button @click="getLocation" :disabled="locating"
              class="w-11 h-11 rounded-xl flex items-center justify-center active:opacity-70 disabled:opacity-50"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <svg v-if="!locating" width="18" height="18" fill="none" stroke="var(--color-accent)" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <div v-else class="w-4 h-4 border-2 rounded-full animate-spin"
                style="border-color: var(--color-accent); border-top-color: transparent;" />
            </button>
          </div>

          <!-- Suggestions -->
          <div class="flex-1 overflow-y-auto px-3 pb-6">
            <div v-if="suggestions.length">
              <button v-for="(s, i) in suggestions" :key="(s.name||'') + (s.address||'') + i"
                @click="selectSuggestion(s)" type="button"
                class="w-full text-left px-4 py-3 active:bg-bg"
                :style="i < suggestions.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
                <div class="text-[14px]" style="color: var(--color-ink); font-weight: 500;">{{ s.name }}</div>
                <div v-if="s.district || s.address" class="text-[12px] mt-0.5"
                  style="color: var(--color-ink-3);">{{ s.district || s.address }}</div>
              </button>
            </div>
            <div v-else-if="!searching && query.length >= 2" class="text-center py-10 text-[13px]"
              style="color: var(--color-ink-3);">没找到匹配地址</div>
            <div v-else-if="query.length < 2" class="text-center py-10 text-[13px]"
              style="color: var(--color-ink-3);">{{ t('common.addrHint') }}</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.ap-enter-active, .ap-leave-active { transition: opacity .18s; }
.ap-enter-from, .ap-leave-to { opacity: 0; }
</style>
