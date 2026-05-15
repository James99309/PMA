// 上传前处理图片：按 EXIF 方向翻正 + 缩放压缩
// iOS WKWebView (Safari 14+) 完整支持 createImageBitmap({ imageOrientation: 'from-image' })

const MAX_SIDE = 1600       // 长边最大像素
const JPEG_QUALITY = 0.82   // JPEG 质量

export async function processImage(file, opts = {}) {
  if (!file || !file.type?.startsWith('image/')) return file
  // GIF 直接放过（动图压缩会丢帧）
  if (file.type === 'image/gif') return file

  const maxSide = opts.maxSide ?? MAX_SIDE
  const quality = opts.quality ?? JPEG_QUALITY

  let bitmap
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  } catch {
    // 老内核回退：不传 imageOrientation
    try { bitmap = await createImageBitmap(file) }
    catch { return file }   // 实在不行，原图上传
  }

  const { width: w0, height: h0 } = bitmap
  const ratio = Math.min(1, maxSide / Math.max(w0, h0))
  const w = Math.round(w0 * ratio)
  const h = Math.round(h0 * ratio)

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d', { alpha: false })
  ctx.drawImage(bitmap, 0, 0, w, h)
  bitmap.close?.()

  const blob = await new Promise((resolve) => {
    canvas.toBlob(b => resolve(b), 'image/jpeg', quality)
  })
  if (!blob) return file

  // 仅在压缩有收益时返回新文件（避免反而变大）
  if (blob.size >= file.size) return file

  const baseName = (file.name || 'image').replace(/\.[^.]+$/, '')
  return new File([blob], `${baseName}.jpg`, { type: 'image/jpeg', lastModified: Date.now() })
}
