// 名片扫描临时状态 — Capture/Crop/Confirm 三屏共享
import { defineStore } from 'pinia'

export const useCardScanStore = defineStore('cardScan', {
  state: () => ({
    cropDataUrl: '',   // 裁剪后图 dataURL (用作预览缩略)
    fileUrl: '',       // NAS 上的图 URL (用作存档 + 联系人 business_card_image_url)
    fields: {},        // OCR 字段 {name, company, position, phone, email, department, address}
    ocrJson: '',       // 原始 JSON 字符串 (供备审计)
    confidence: {},    // 各字段置信度 {name: 0.95, ...}
  }),
  actions: {
    setOcr({ cropDataUrl, fileUrl, fields, ocrJson }) {
      this.cropDataUrl = cropDataUrl || ''
      this.fileUrl = fileUrl || ''
      this.fields = fields || {}
      this.ocrJson = ocrJson || ''
      this.confidence = (fields && fields.confidence) || {}
    },
    clear() {
      this.cropDataUrl = ''
      this.fileUrl = ''
      this.fields = {}
      this.ocrJson = ''
      this.confidence = {}
    },
  },
})
