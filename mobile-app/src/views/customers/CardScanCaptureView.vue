<script setup>
// 名片扫描 · 拍照 → 4 角裁剪 → 上传 + Claude vision OCR → 跳转核对页
// 状态机: capture (调相机) → crop (4 角拖拽) → processing (上传+OCR) → 跳转
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import ImageCrop4Corners from '@/components/common/ImageCrop4Corners.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'
import { Capacitor } from '@capacitor/core'

const router = useRouter()
const scanStore = useCardScanStore()

const step = ref('capture')          // 'capture' | 'crop' | 'processing'
const photoUrl = ref('')             // blob/data URL of original photo
const photoBlob = ref(null)
const cameraInputEl = ref(null)
const error = ref('')

async function startCamera() {
  error.value = ''
  if (Capacitor.isNativePlatform?.()) {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
      const photo = await Camera.getPhoto({
        quality: 90,
        allowEditing: false,
        resultType: CameraResultType.Uri,
        source: CameraSource.Camera,
        saveToGallery: false,
      })
      const res = await fetch(photo.webPath)
      const blob = await res.blob()
      photoBlob.value = blob
      photoUrl.value = URL.createObjectURL(blob)
      step.value = 'crop'
    } catch (e) {
      const msg = e?.message || String(e || '')
      if (msg.includes('cancelled') || msg.includes('canceled') || msg.includes('User cancelled')) {
        // 用户取消 → 返回上一页
        router.back()
        return
      }
      error.value = `相机调用失败: ${msg.slice(0, 80)}`
    }
  } else {
    // Web 端 fallback: HTML <input capture>
    cameraInputEl.value?.click()
  }
}

function onWebPhoto(e) {
  const f = e.target.files?.[0]
  if (!f) return
  photoBlob.value = f
  photoUrl.value = URL.createObjectURL(f)
  step.value = 'crop'
  e.target.value = ''
}

async function onCropped({ blob, dataUrl }) {
  if (!blob) {
    error.value = '裁剪失败'
    return
  }
  step.value = 'processing'
  scanStore.cropDataUrl = dataUrl
  try {
    const res = await scanBusinessCard(blob, `business_card_${Date.now()}.jpg`)
    const data = res.data?.data
    if (!res.data?.success || !data?.fields) {
      error.value = res.data?.message || '识别失败'
      step.value = 'crop'
      return
    }
    scanStore.setOcr({
      cropDataUrl: dataUrl,
      fileUrl: data.file_url || '',
      fields: data.fields,
      ocrJson: data.ocr_json || '',
    })
    router.replace('/customers/scan/confirm')
  } catch (e) {
    error.value = `请求失败: ${e?.message || e}`
    step.value = 'crop'
  }
}

function onCropCancel() {
  // 重新拍
  if (photoUrl.value && photoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(photoUrl.value)
  }
  photoUrl.value = ''
  photoBlob.value = null
  step.value = 'capture'
  startCamera()
}

onMounted(() => {
  scanStore.clear()
  startCamera()
})
onBeforeUnmount(() => {
  if (photoUrl.value && photoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(photoUrl.value)
  }
})
</script>

<template>
  <div class="flex flex-col h-full" style="background: #000;">
    <!-- Web fallback input (隐藏) -->
    <input ref="cameraInputEl" type="file" accept="image/*" capture="environment"
      @change="onWebPhoto" style="display: none;" />

    <!-- step: capture (调相机中) -->
    <div v-if="step === 'capture'" class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="text-[14px] opacity-80">正在打开相机…</div>
      <div v-if="error" class="mt-4 text-[13px]" style="color: #FF6B6B;">{{ error }}</div>
      <button v-if="error" @click="router.back()"
        class="mt-6 px-5 py-2 rounded-full text-[13px]"
        style="background: rgba(255,255,255,0.15); color: #fff;">返回</button>
    </div>

    <!-- step: crop (4 角裁剪) -->
    <ImageCrop4Corners v-else-if="step === 'crop' && photoUrl"
      :src="photoUrl"
      @crop="onCropped"
      @cancel="onCropCancel" />

    <!-- step: processing (上传+OCR) -->
    <div v-else-if="step === 'processing'"
      class="flex-1 flex flex-col items-center justify-center text-white px-6 text-center">
      <div class="inline-block animate-spin"
        style="width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 18px;"></div>
      <div class="mt-4 text-[14px]">AI 正在识别名片字段…</div>
      <div class="mt-2 text-[12px] opacity-60">通常 2-5 秒</div>
    </div>
  </div>
</template>
