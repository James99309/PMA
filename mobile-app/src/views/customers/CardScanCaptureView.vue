<!--
  CardScanCaptureView · 名片扫描 - 复用 DocumentScanFlow 公用组件
  本视图只负责: 接收 done 事件 → 调 OCR API → 跳到 confirm 页
  与 ReceiptCaptureView 共享同一套 capture/crop/preview UI
-->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DocumentScanFlow from '@/components/common/DocumentScanFlow.vue'
import OcrProcessingAnimation from '@/components/common/OcrProcessingAnimation.vue'
import { useCardScanStore } from '@/stores/cardScan'
import { scanBusinessCard } from '@/api/customers'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const scanStore = useCardScanStore()

const processing = ref(false)
const error = ref('')

// Field-reveal animation rows (aligned with the OCR-returned fields)
const ocrFields = computed(() => {
  const v = t('cardScan.capRecognizing')
  return [
    { label: t('cardScan.capFName'),     val: v, confident: true },
    { label: t('cardScan.capFCompany'),  val: v, confident: true },
    { label: t('cardScan.capFPosition'), val: v, confident: true },
    { label: t('cardScan.capFPhone'),    val: v, confident: true },
    { label: t('cardScan.capFEmail'),    val: v, confident: false },
  ]
})

onMounted(() => {
  scanStore.clear()
  if (route.query.attachTo) {
    scanStore.setAttachTo(Number(route.query.attachTo), route.query.attachToName || '')
  }
})

async function onDone(pages) {
  if (!pages || pages.length === 0) {
    router.back()
    return
  }
  // 名片是单张
  const { blob, dataUrl } = pages[0]
  await uploadAndOCR(blob, dataUrl)
}

async function uploadAndOCR(blob, dataUrl) {
  processing.value = true
  error.value = ''
  scanStore.cropDataUrl = dataUrl
  try {
    const res = await scanBusinessCard(blob, `business_card_${Date.now()}.jpg`)
    const data = res.data?.data
    if (!res.data?.success || !data?.fields) {
      error.value = res.data?.message || t('cardScan.capScanFail')
      processing.value = false
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
    error.value = t('cardScan.capRequestFailFmt', { err: e?.message || e })
    processing.value = false
  }
}
</script>

<template>
  <div class="h-full">
    <!-- OCR 进行中: 复用通用 OCR 动画 (单卡 + 字段揭示, 替代黑屏 spinner) -->
    <div v-if="processing" class="h-full" style="background: var(--color-ex-bg, #F7F5F2);">
      <OcrProcessingAnimation
        :card-count="1"
        :title="t('cardScan.capScanTitle')"
        :subtitle="t('cardScan.capScanSubtitle')"
        :fields="ocrFields"
        :error="error"
        @retry="processing = false; error = ''"
      />
    </div>

    <!-- 扫描流(VisionKit / Camera fallback) -->
    <DocumentScanFlow
      v-else
      :allow-multi="false"
      :capture-tip="t('cardScan.capCaptureTip')"
      :preview-tip="t('cardScan.capPreviewTip')"
      :primary-label="t('cardScan.capPrimaryLabel')"
      @done="onDone"
      @cancel="$router.back()"
    />
  </div>
</template>
