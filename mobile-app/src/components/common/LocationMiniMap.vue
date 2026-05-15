<script setup>
// 聊天气泡内的缩略地图预览（设计 chat-location.jsx MiniMap 同款）
// 不可拖动/缩放，纯展示；中国用高德瓦片，海外用 OSM
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'

const props = defineProps({
  lat:    { type: Number, required: true },
  lon:    { type: Number, required: true },
  width:  { type: Number, default: 252 },
  height: { type: Number, default: 132 },
})

const mapEl = ref(null)
let map = null

const PIN_ICON = L.divIcon({
  html: `<svg width="22" height="28" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 3px 4px rgba(0,0,0,0.22));">
    <path d="M16 38C16 38 4 22 4 14a12 12 0 1124 0c0 8-12 24-12 24z" fill="#D97757"/>
    <circle cx="16" cy="14" r="5" fill="#fff"/>
  </svg>`,
  className: 'pma-mini-pin',
  iconSize: [22, 28],
  iconAnchor: [11, 28],
})

const isChina = (la, lo) =>
  la >= 18 && la <= 54 && lo >= 73 && lo <= 135

function init() {
  if (!mapEl.value || map) return
  map = L.map(mapEl.value, {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
    tap: false,
    touchZoom: false,
  }).setView([props.lat, props.lon], 15)

  if (isChina(props.lat, props.lon)) {
    L.tileLayer(
      'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
      { subdomains: ['1', '2', '3', '4'], maxZoom: 18 }
    ).addTo(map)
  } else {
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map)
  }
  L.marker([props.lat, props.lon], { icon: PIN_ICON, interactive: false }).addTo(map)
  setTimeout(() => map?.invalidateSize(), 60)
}

watch([() => props.lat, () => props.lon], ([la, lo]) => {
  if (map && la != null && lo != null) map.setView([la, lo], 15)
})

onMounted(init)
onBeforeUnmount(() => { map?.remove(); map = null })
</script>

<template>
  <div class="lmm-wrap"
    :style="{
      width: width + 'px',
      height: height + 'px',
      background: '#E8E4DC',
    }">
    <div ref="mapEl" class="lmm-inner" />
  </div>
</template>

<style scoped>
.lmm-wrap {
  position: relative;
  overflow: hidden;
  contain: strict;
  isolation: isolate;
  pointer-events: none;
}
.lmm-inner {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
</style>
