// 名片扫描临时状态 — Capture/Crop/Confirm 三屏共享
import { defineStore } from 'pinia'

export const useCardScanStore = defineStore('cardScan', {
  state: () => ({
    cropDataUrl: '',   // 裁剪后图 dataURL (用作预览缩略)
    fileUrl: '',       // NAS 上的图 URL (用作存档 + 联系人 business_card_image_url)
    fields: {},        // OCR 字段 {name, company, position, phone, email, department, address}
    ocrJson: '',       // 原始 JSON 字符串 (供备审计)
    confidence: {},    // 各字段置信度 {name: 0.95, ...}
    attachToCompanyId: null,    // 若有, 跳过新建客户, 直接给该客户加联系人
    attachToCompanyName: '',
    // 保存成功后展示给 SuccessView 用的数据 (保留到用户离开 success 页)
    // { contactId, contactName, position, phone, email, companyId, companyName,
    //   fileUrl, fieldCount, mergeMode: 'merge'|'new'|'attach' }
    saveResult: null,
  }),
  actions: {
    setOcr({ cropDataUrl, fileUrl, fields, ocrJson }) {
      this.cropDataUrl = cropDataUrl || ''
      this.fileUrl = fileUrl || ''
      this.fields = fields || {}
      this.ocrJson = ocrJson || ''
      this.confidence = (fields && fields.confidence) || {}
    },
    setAttachTo(companyId, companyName) {
      this.attachToCompanyId = companyId || null
      this.attachToCompanyName = companyName || ''
    },
    setSaveResult(data) { this.saveResult = data || null },
    clearSaveResult() { this.saveResult = null },
    // 完整重置 — 跳出整个名片扫描流程时调用
    clear() {
      this.cropDataUrl = ''
      this.fileUrl = ''
      this.fields = {}
      this.ocrJson = ''
      this.confidence = {}
      this.attachToCompanyId = null
      this.attachToCompanyName = ''
      this.saveResult = null
    },
    // 继续拍下一张 — 保留 attachTo (如果有), 清掉本次结果
    resetForNextScan() {
      this.cropDataUrl = ''
      this.fileUrl = ''
      this.fields = {}
      this.ocrJson = ''
      this.confidence = {}
      this.saveResult = null
      // attachToCompanyId / attachToCompanyName 保留, 让连拍继续挂同一客户
    },
  },
})
