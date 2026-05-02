import { defineStore } from 'pinia'
import { fetchDictionary } from '@/api/dictionaries'

// 字典 Pinia store —— 进程内缓存（避免重复 fetch）
//
// 字典项格式（从后端 Dictionary.to_dict()）：
//   { id, type, key, value, value_en, is_active, sort_order, ... }
//
// 用法：
//   const ds = useDictionariesStore()
//   await ds.ensure('project_stage')
//   const list = ds.list('project_stage')           // [{key, label, label_en, sort_order}, ...]
//   const map  = ds.labelMap('project_stage')       // {key: label}
//   const lbl  = ds.label('project_stage', 'embed') // '植入'
export const useDictionariesStore = defineStore('dictionaries', {
  state: () => ({
    cache: {},        // type -> [{key, label, label_en, sort_order, is_active}]
    inflight: {},     // type -> Promise（避免并发重复 fetch）
    loadedAt: {},     // type -> timestamp
  }),

  getters: {
    list: (state) => (type) => state.cache[type] || [],
    labelMap: (state) => (type) => {
      const m = {}
      for (const it of (state.cache[type] || [])) m[it.key] = it.label
      return m
    },
    label: (state) => (type, key) => {
      const list = state.cache[type] || []
      const it = list.find(x => x.key === key)
      return it ? it.label : (key || '')
    },
  },

  actions: {
    /** 拉取并缓存指定字典类型；已缓存且未过期则跳过 */
    async ensure(type, { force = false, ttl = 30 * 60 * 1000 } = {}) {
      if (!force && this.cache[type]) {
        if (!this.loadedAt[type] || Date.now() - this.loadedAt[type] < ttl) return this.cache[type]
      }
      if (this.inflight[type]) return this.inflight[type]

      const p = (async () => {
        try {
          const r = await fetchDictionary(type, true)
          const rows = r.data?.success ? (r.data.data || []) : []
          // 标准化：把 {value, value_en} 映射为 {label, label_en}
          this.cache[type] = rows.map(d => ({
            key: d.key,
            label: d.value,
            label_en: d.value_en || d.value,
            sort_order: d.sort_order ?? 0,
            is_active: d.is_active ?? true,
          }))
          this.loadedAt[type] = Date.now()
          return this.cache[type]
        } catch (e) {
          console.warn(`fetch dictionary "${type}" failed:`, e)
          if (!this.cache[type]) this.cache[type] = []
          return this.cache[type]
        } finally {
          delete this.inflight[type]
        }
      })()
      this.inflight[type] = p
      return p
    },
  },
})
