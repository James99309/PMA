<script setup>
// 4 角拖拽 + canvas 透视变换裁剪
// 用法: <ImageCrop4Corners :src="blobUrl" @crop="onCropped" @cancel="..." />
//   src: 图片 URL (blob:/file:/http: 都行)
//   @crop(blob, dataUrl): 用户点完成后回调, 给出裁剪后的 JPEG blob + data URL
//
// 逻辑:
//   1. 加载图原始尺寸到 imgEl
//   2. 在覆盖层显示 4 个圆形 handle, 默认收缩到图四角内 8% (引导用户对准名片)
//   3. 用户拖 handle → 更新 4 个像素坐标 (基于原始图坐标系)
//   4. 完成时: canvas perspective transform, 把四边形 → 矩形输出
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  src: { type: String, required: true },
  outputMaxLong: { type: Number, default: 1600 },  // 输出长边像素上限
  jpegQuality: { type: Number, default: 0.88 },
})
const emit = defineEmits(['crop', 'cancel'])

const imgEl = ref(null)
const containerEl = ref(null)
const naturalW = ref(0)
const naturalH = ref(0)
const displayW = ref(0)
const displayH = ref(0)
const offsetX = ref(0)  // 图在容器内左上角偏移
const offsetY = ref(0)
const ratio = ref(1)    // display:natural 比例

// 四角 (基于显示坐标 px)。顺序: TL, TR, BR, BL
const corners = ref([
  { x: 0, y: 0 },
  { x: 0, y: 0 },
  { x: 0, y: 0 },
  { x: 0, y: 0 },
])
const draggingIdx = ref(-1)

function onImgLoaded() {
  if (!imgEl.value) return
  naturalW.value = imgEl.value.naturalWidth
  naturalH.value = imgEl.value.naturalHeight
  recomputeLayout()
  // 初始 4 角默认离边 8% (留点空间提示用户拖)
  const inset = 0.08
  corners.value = [
    { x: offsetX.value + displayW.value * inset,            y: offsetY.value + displayH.value * inset },
    { x: offsetX.value + displayW.value * (1 - inset),      y: offsetY.value + displayH.value * inset },
    { x: offsetX.value + displayW.value * (1 - inset),      y: offsetY.value + displayH.value * (1 - inset) },
    { x: offsetX.value + displayW.value * inset,            y: offsetY.value + displayH.value * (1 - inset) },
  ]
}

function recomputeLayout() {
  if (!containerEl.value || !naturalW.value) return
  const cw = containerEl.value.clientWidth
  const ch = containerEl.value.clientHeight
  // 等比缩放 fit-contain
  const r = Math.min(cw / naturalW.value, ch / naturalH.value)
  ratio.value = r
  displayW.value = naturalW.value * r
  displayH.value = naturalH.value * r
  offsetX.value = (cw - displayW.value) / 2
  offsetY.value = (ch - displayH.value) / 2
}

function onResize() {
  // 重新计算同时按比例迁移角点
  if (!naturalW.value) return
  const oldOX = offsetX.value, oldOY = offsetY.value
  const oldDW = displayW.value, oldDH = displayH.value
  recomputeLayout()
  // 把 corner 从旧坐标 → 新坐标 (转成原图比例再回投)
  corners.value = corners.value.map(c => {
    const nx = (c.x - oldOX) / oldDW
    const ny = (c.y - oldOY) / oldDH
    return {
      x: offsetX.value + nx * displayW.value,
      y: offsetY.value + ny * displayH.value,
    }
  })
}

function clientToContainer(e) {
  const rect = containerEl.value.getBoundingClientRect()
  const t = e.touches?.[0] || e.changedTouches?.[0] || e
  return { x: t.clientX - rect.left, y: t.clientY - rect.top }
}
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }
function clampToImage(p) {
  return {
    x: clamp(p.x, offsetX.value, offsetX.value + displayW.value),
    y: clamp(p.y, offsetY.value, offsetY.value + displayH.value),
  }
}

function startDrag(idx, e) {
  draggingIdx.value = idx
  e.preventDefault()
}
function onMove(e) {
  if (draggingIdx.value < 0) return
  const p = clampToImage(clientToContainer(e))
  corners.value[draggingIdx.value] = p
  e.preventDefault()
}
function endDrag() { draggingIdx.value = -1 }

onMounted(() => {
  window.addEventListener('resize', onResize)
})

watch(() => props.src, () => {
  // src 换了等图 onload 重置
  naturalW.value = 0
  naturalH.value = 0
})

// 把显示坐标 → 原图像素坐标
function toNatural(c) {
  return {
    x: (c.x - offsetX.value) / ratio.value,
    y: (c.y - offsetY.value) / ratio.value,
  }
}

// SVG 多边形描边 (4 角连接, 显示坐标)
const polyPoints = computed(() =>
  corners.value.map(c => `${c.x},${c.y}`).join(' '))

async function doCrop() {
  if (!naturalW.value) return
  const natCorners = corners.value.map(toNatural)
  // 估算输出宽高: 取上下两边平均长度作输出宽, 左右两边作输出高
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y)
  const widthTop = dist(natCorners[0], natCorners[1])
  const widthBottom = dist(natCorners[3], natCorners[2])
  const heightLeft = dist(natCorners[0], natCorners[3])
  const heightRight = dist(natCorners[1], natCorners[2])
  let outW = Math.round((widthTop + widthBottom) / 2)
  let outH = Math.round((heightLeft + heightRight) / 2)
  // 长边限制 outputMaxLong
  const longSide = Math.max(outW, outH)
  if (longSide > props.outputMaxLong) {
    const scale = props.outputMaxLong / longSide
    outW = Math.round(outW * scale)
    outH = Math.round(outH * scale)
  }

  // canvas 绘制源图到 offscreen, 然后做 perspective sampling
  const srcCanvas = document.createElement('canvas')
  srcCanvas.width = naturalW.value
  srcCanvas.height = naturalH.value
  const sCtx = srcCanvas.getContext('2d')
  sCtx.drawImage(imgEl.value, 0, 0)
  const srcData = sCtx.getImageData(0, 0, naturalW.value, naturalH.value)

  const dstCanvas = document.createElement('canvas')
  dstCanvas.width = outW
  dstCanvas.height = outH
  const dCtx = dstCanvas.getContext('2d')
  const dstData = dCtx.createImageData(outW, outH)

  // 透视采样: 对输出每个像素 (u, v) ∈ [0,1]^2,
  // 在源四边形内做双线性 (沿四边比例插值) — 简化版无矩阵, 名片直拍场景够用
  const [tl, tr, br, bl] = natCorners
  const sw = naturalW.value, sh = naturalH.value
  for (let y = 0; y < outH; y++) {
    const v = y / (outH - 1)
    // 上边线 tl→tr 在 v=0, 下边线 bl→br 在 v=1
    // 当前行起点 = lerp(tl, bl, v); 终点 = lerp(tr, br, v)
    const startX = tl.x + (bl.x - tl.x) * v
    const startY = tl.y + (bl.y - tl.y) * v
    const endX   = tr.x + (br.x - tr.x) * v
    const endY   = tr.y + (br.y - tr.y) * v
    for (let x = 0; x < outW; x++) {
      const u = x / (outW - 1)
      const sx = startX + (endX - startX) * u
      const sy = startY + (endY - startY) * u
      // 最近邻 (够快, 名片不需要太精细)
      const ix = Math.round(sx)
      const iy = Math.round(sy)
      if (ix < 0 || ix >= sw || iy < 0 || iy >= sh) continue
      const si = (iy * sw + ix) * 4
      const di = (y * outW + x) * 4
      dstData.data[di]     = srcData.data[si]
      dstData.data[di + 1] = srcData.data[si + 1]
      dstData.data[di + 2] = srcData.data[si + 2]
      dstData.data[di + 3] = 255
    }
  }
  dCtx.putImageData(dstData, 0, 0)

  // 输出 JPEG blob
  return new Promise(resolve => {
    dstCanvas.toBlob(blob => {
      const dataUrl = dstCanvas.toDataURL('image/jpeg', props.jpegQuality)
      emit('crop', { blob, dataUrl, width: outW, height: outH })
      resolve()
    }, 'image/jpeg', props.jpegQuality)
  })
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: #000;">
    <!-- 顶部 nav -->
    <div class="flex items-center justify-between px-4 py-3 shrink-0"
      style="background: rgba(0,0,0,0.85);">
      <button @click="$emit('cancel')" class="text-white text-[15px] active:opacity-70">{{ t('scan.cancel') }}</button>
      <span class="text-white text-[14px] opacity-75">{{ t('scan.cropTip') }}</span>
      <button @click="doCrop" class="text-white text-[15px] font-semibold active:opacity-70"
        style="color: #FBB040;">{{ t('scan.cropDone') }}</button>
    </div>

    <!-- 图片 + 拖拽层 -->
    <div ref="containerEl" class="flex-1 relative overflow-hidden"
      @mousemove="onMove" @mouseup="endDrag" @mouseleave="endDrag"
      @touchmove.passive="onMove" @touchend="endDrag" @touchcancel="endDrag">
      <img ref="imgEl" :src="src" @load="onImgLoaded"
        class="absolute pointer-events-none"
        :style="{
          left: offsetX + 'px', top: offsetY + 'px',
          width: displayW + 'px', height: displayH + 'px',
        }" />
      <!-- SVG 多边形描边 -->
      <svg v-if="naturalW" class="absolute inset-0 pointer-events-none"
        :width="containerEl?.clientWidth || 0"
        :height="containerEl?.clientHeight || 0">
        <polygon :points="polyPoints"
          fill="rgba(217,119,87,0.18)" stroke="#FBB040" stroke-width="2" />
      </svg>
      <!-- 4 个角 handle -->
      <div v-for="(c, i) in corners" :key="i"
        class="absolute rounded-full"
        @mousedown="startDrag(i, $event)"
        @touchstart="startDrag(i, $event)"
        :style="{
          left: (c.x - 18) + 'px', top: (c.y - 18) + 'px',
          width: '36px', height: '36px',
          background: 'rgba(255,255,255,0.92)',
          border: '3px solid #FBB040',
          boxShadow: '0 2px 6px rgba(0,0,0,0.35)',
          touchAction: 'none',
        }"></div>
    </div>

    <!-- 底部提示 -->
    <div class="px-5 py-3 shrink-0 text-center"
      style="background: rgba(0,0,0,0.85); color: rgba(255,255,255,0.75); font-size: 12px;">
      {{ t('scan.cropHint') }}
    </div>
  </div>
</template>
