<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer, addCustomerNote, addContact } from '@/api/customers'
import NavBar      from '@/components/common/NavBar.vue'
import Section     from '@/components/common/Section.vue'
import StageDot    from '@/components/common/StageDot.vue'
import Avatar      from '@/components/common/Avatar.vue'
import FilledField from '@/components/common/FilledField.vue'

const route = useRoute()
const router = useRouter()
const company = ref(null)
const loading = ref(true)

// 跟进
const showNoteBox = ref(false)
const noteText = ref('')
const addingNote = ref(false)

// 新增联系人 sheet（对标 customer-screens.jsx AddContactSheet）
const showContactSheet = ref(false)
const newContact = ref({ name: '', position: '', phone: '', email: '', is_primary: false })
const addingContact = ref(false)

// 阶段 → tier 颜色（A=ink, B=ink3, C=ink4）— 对标 SearchCustomerRow tierColor
const TIER_COLOR = { A: '#1A1A1A', B: '#7A7570', C: '#C2BBB3' }

const statusColor = computed(() => {
  const s = company.value?.status
  if (s === '活跃') return '#2F7A45'
  if (s === '冷却') return '#7A7570'
  return '#7A7570'
})

const visibleProjects = computed(() => (company.value?.projects || []).slice(0, 4))

async function load() {
  try {
    const res = await getCustomer(route.params.id)
    company.value = res.data.data
  } finally {
    loading.value = false
  }
}

async function submitNote() {
  if (!noteText.value.trim()) return
  addingNote.value = true
  try {
    await addCustomerNote(route.params.id, noteText.value.trim())
    noteText.value = ''
    showNoteBox.value = false
    await load()
  } finally {
    addingNote.value = false
  }
}

async function submitContact() {
  if (!newContact.value.name.trim()) return
  addingContact.value = true
  try {
    await addContact(route.params.id, newContact.value)
    newContact.value = { name: '', position: '', phone: '', email: '', is_primary: false }
    showContactSheet.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.message || '添加失败')
  } finally {
    addingContact.value = false
  }
}

function callPhone(phone) { if (phone) window.open(`tel:${phone}`) }
function newProject() {
  router.push({ path: '/projects/new', query: { company_id: route.params.id } })
}
function openProject(id) {
  router.push(`/projects/${id}`)
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-bg);">

    <!-- Nav -->
    <NavBar back-label="客户" @back="router.back()"
      @more="router.push(`/customers/${route.params.id}/edit`)" />

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <div v-else-if="company" class="flex-1 overflow-y-auto pb-24">

      <!-- ─── Hero ─────────────────────────────────────── -->
      <div class="px-7 pt-5 pb-6">
        <div class="flex items-center gap-2.5 mb-3.5 flex-wrap">
          <span class="inline-flex items-center gap-1.5 text-[11px] font-semibold"
            :style="{ color: statusColor, letterSpacing: '0.4px' }">
            <span class="w-[5px] h-[5px] rounded-[3px]" :style="{ background: statusColor }" />
            {{ company.status || '活跃' }}
          </span>
          <span v-if="company.industry" class="text-[11px]" style="color: var(--color-ink-3);">
            · {{ company.industry }}
          </span>
        </div>

        <h1 class="font-serif font-medium leading-tight m-0"
          style="font-size: 28px; letter-spacing: -0.3px; color: var(--color-ink);">
          {{ company.name }}
        </h1>

        <div class="mt-3 text-[13px]" style="color: var(--color-ink-3);">
          <template v-if="company.tier">{{ company.tier }} 类客户 · </template>
          {{ [company.region, company.company_size].filter(Boolean).join(' · ') || '—' }}
        </div>

        <!-- 累计客户价值 -->
        <div class="mt-6 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular"
            style="font-size: 44px; color: var(--color-ink);">
            ¥{{ (company.value ?? 0).toFixed(2) }}
          </span>
          <span class="text-[14px]" style="color: var(--color-ink-3);">万 · 累计客户价值</span>
        </div>
      </div>

      <!-- ─── CTA row ──────────────────────────────────── -->
      <div class="px-5 pb-2 flex gap-2.5">
        <button @click="newProject" type="button"
          class="flex-1 h-12 rounded-2xl text-white text-[15px] font-semibold active:opacity-90"
          style="background: var(--color-accent); border: none;">
          新建项目 →
        </button>
        <button @click="showNoteBox = true" type="button"
          class="h-12 px-3.5 rounded-2xl flex items-center gap-1.5 active:opacity-70 shrink-0"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <svg width="14" height="14" viewBox="0 0 18 18" fill="none" style="pointer-events: none;">
            <path d="M9 2v14M2 9h14" stroke="var(--color-ink-2)" stroke-width="2" stroke-linecap="round" />
          </svg>
          <span class="text-[12px]" style="color: var(--color-ink-2); pointer-events: none;">跟进</span>
        </button>
      </div>

      <!-- ─── 项目概览 4 数 ──────────────────────────── -->
      <Section title="项目概览">
        <div class="grid grid-cols-4 rounded-2xl p-4"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink);">
              {{ company.total_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">总数</div>
          </div>
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-accent);">
              {{ company.open_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">进行中</div>
          </div>
          <div class="text-center" style="border-right: 1px solid var(--color-divider);">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink);">
              {{ company.won_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">已签约</div>
          </div>
          <div class="text-center">
            <div class="font-serif font-medium tabular" style="font-size: 24px; color: var(--color-ink-4);">
              {{ company.lost_count ?? 0 }}
            </div>
            <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">丢单</div>
          </div>
        </div>
      </Section>

      <!-- ─── 名下项目 ─────────────────────────────────── -->
      <Section title="名下项目">
        <template #action>
          <span class="text-[12px]" style="color: var(--color-ink-3);">
            共 {{ company.total_count ?? 0 }} 个 ›
          </span>
        </template>
        <div v-if="visibleProjects.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(p, i) in visibleProjects" :key="p.id"
            @click="openProject(p.id)"
            class="px-4 py-3 flex items-baseline justify-between gap-3 active:bg-bg cursor-pointer"
            :style="i < visibleProjects.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="flex-1 min-w-0">
              <div class="font-serif font-medium leading-tight truncate"
                style="font-size: 15px; color: var(--color-ink);">{{ p.name }}</div>
              <div class="mt-1"><StageDot :tone="p.tone" :label="p.stage_label" /></div>
            </div>
            <div class="text-[14px] font-semibold tabular whitespace-nowrap">
              <template v-if="p.amount > 0">
                ¥{{ p.amount.toFixed(2) }}<span class="text-[10px] ml-0.5" style="color: var(--color-ink-3);">万</span>
              </template>
              <span v-else class="text-[13px]" style="color: var(--color-ink-3);">—</span>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">暂无项目</div>
      </Section>

      <!-- ─── 详情 definition list ─────────────────────── -->
      <Section title="详情">
        <div class="grid text-[14px]" style="grid-template-columns: 90px 1fr; row-gap: 12px; column-gap: 16px;">
          <span style="color: var(--color-ink-3);">负责人</span>
          <span>{{ company.owner_name || '—' }}</span>
          <span style="color: var(--color-ink-3);">客户层级</span>
          <span><b class="font-semibold">{{ company.tier || '—' }}</b><template v-if="company.tier"> 类</template></span>
          <span style="color: var(--color-ink-3);">地址</span>
          <span>{{ company.address || '—' }}</span>
          <template v-if="company.established">
            <span style="color: var(--color-ink-3);">成立</span>
            <span class="tabular">{{ company.established }}</span>
          </template>
          <span style="color: var(--color-ink-3);">来源</span>
          <span>{{ company.source || '—' }}</span>
        </div>
      </Section>

      <!-- ─── 联系人 ───────────────────────────────────── -->
      <Section title="联系人">
        <template #action>
          <button @click="showContactSheet = true"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">+ 添加</button>
        </template>
        <div v-if="company.contacts?.length" class="rounded-2xl overflow-hidden"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(p, i) in company.contacts" :key="p.id"
            class="p-3.5 flex items-center gap-3.5"
            :style="i < company.contacts.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <Avatar :text="p.name" :size="40" :primary="p.is_primary" />
            <div class="flex-1 min-w-0">
              <div class="text-[15px] font-semibold truncate">{{ p.name }}</div>
              <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">
                {{ [p.position, p.department].filter(Boolean).join(' · ') || '—' }}
              </div>
            </div>
            <button v-if="p.phone" @click="callPhone(p.phone)"
              class="w-9 h-9 rounded-full flex items-center justify-center active:opacity-70"
              style="background: transparent; border: 1px solid var(--color-divider);">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z"
                  fill="var(--color-ink-2)" />
              </svg>
            </button>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">暂无联系人</div>
      </Section>

      <!-- ─── 跟进时间轴 ─────────────────────────────── -->
      <div class="px-7 pt-5 pb-24">
        <div class="flex items-center justify-between mb-3">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 1px;">跟进记录</div>
          <button @click="showNoteBox = true"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">+ 添加</button>
        </div>
        <div v-if="company.actions?.length">
          <div v-for="(a, i) in company.actions" :key="a.id"
            class="pl-3.5"
            :style="{
              borderLeft: '2px solid ' + (i === 0 ? 'var(--color-accent)' : 'var(--color-divider)'),
              marginTop: i ? '16px' : '0',
            }">
            <div class="text-[11px] tabular mb-1" style="color: var(--color-ink-3);">
              {{ a.date }} — {{ a.owner_name }}
            </div>
            <div class="font-serif"
              :style="{
                fontSize: '16px',
                lineHeight: '1.55',
                color: i === 0 ? 'var(--color-ink)' : 'var(--color-ink-2)',
              }">
              {{ a.communication }}
            </div>
          </div>
        </div>
        <div v-else class="text-center text-[13px] py-4" style="color: var(--color-ink-3);">暂无跟进记录</div>
      </div>
    </div>

    <!-- ─── 跟进输入弹层 ────────────────────────────── -->
    <Transition name="sheet">
      <div v-if="showNoteBox" class="absolute inset-0 z-40">
        <div class="absolute inset-0 bg-black/30" @click="showNoteBox = false" />
        <div class="absolute left-0 right-0 bottom-0 px-5 pt-3 pb-8 rounded-t-3xl"
          style="background: var(--color-card);">
          <div class="mx-auto mb-3 w-9 h-1 rounded-full" style="background: rgba(0,0,0,0.15);" />
          <div class="text-[11px] font-semibold uppercase mb-2"
            style="color: var(--color-ink-3); letter-spacing: 1px;">添加跟进记录</div>
          <textarea v-model="noteText" rows="4" placeholder="输入跟进内容..."
            class="w-full rounded-xl px-3 py-2.5 text-[14px] outline-none resize-none"
            style="border: 1px solid var(--color-divider); background: var(--color-bg); color: var(--color-ink);" />
          <div class="flex gap-2 mt-3">
            <button @click="showNoteBox = false"
              class="flex-1 rounded-2xl py-3 text-[15px]"
              style="border: 1px solid var(--color-divider); color: var(--color-ink-2);">取消</button>
            <button @click="submitNote" :disabled="addingNote || !noteText.trim()"
              class="flex-1 rounded-2xl py-3 text-[15px] font-semibold text-white disabled:opacity-50"
              style="background: var(--color-accent);">
              {{ addingNote ? '提交中…' : '提交' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ─── 新增联系人 sheet（对标 AddContactSheet） ───── -->
    <Transition name="sheet">
      <div v-if="showContactSheet" class="absolute inset-0 z-40">
        <div class="absolute inset-0" style="background: rgba(20,20,20,0.32);"
          @click="showContactSheet = false" />
        <div class="absolute left-0 right-0 bottom-0 rounded-t-3xl overflow-hidden"
          style="background: var(--color-bg); box-shadow: 0 -10px 40px rgba(0,0,0,0.18);">
          <div class="flex justify-center pt-3 pb-2">
            <div class="w-9 h-1 rounded-full" style="background: rgba(0,0,0,0.15);" />
          </div>
          <div class="flex justify-between items-center px-6 pt-1 pb-4">
            <button @click="showContactSheet = false" class="text-[14px] active:opacity-60"
              style="color: var(--color-accent);">取消</button>
            <span class="font-serif text-[18px] font-medium">新增联系人</span>
            <button @click="submitContact"
              :disabled="addingContact || !newContact.name.trim()"
              class="text-[14px] font-bold active:opacity-60 disabled:opacity-40"
              :style="{ color: newContact.name.trim() ? 'var(--color-accent)' : 'var(--color-ink-4)' }">
              {{ addingContact ? '添加中…' : '添加' }}
            </button>
          </div>
          <div class="px-5 pb-6">
            <div class="rounded-2xl py-1"
              style="background: var(--color-card); border: 1px solid var(--color-divider);">
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">姓名 *</div>
                <input v-model="newContact.name" type="text"
                  class="w-full font-serif text-[17px] font-medium outline-none bg-transparent"
                  placeholder="—" />
              </div>
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">职务</div>
                <input v-model="newContact.position" type="text"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
              <div class="px-4 py-3" style="border-bottom: 1px solid var(--color-divider);">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">手机</div>
                <input v-model="newContact.phone" type="tel"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
              <div class="px-4 py-3">
                <div class="text-[11px] mb-1" style="color: var(--color-ink-3);">邮箱</div>
                <input v-model="newContact.email" type="email"
                  class="w-full text-[15px] outline-none bg-transparent" placeholder="—" />
              </div>
            </div>

            <div class="mt-4 rounded-xl px-4 py-3.5 flex items-center justify-between"
              style="background: var(--color-accent-bg);">
              <div>
                <div class="text-[13px] font-semibold" style="color: var(--color-ink);">设为主要联系人</div>
                <div class="text-[11px] mt-0.5" style="color: var(--color-ink-3);">
                  当前主要联系人：{{ company.contacts?.find(c => c.is_primary)?.name || '无' }}
                </div>
              </div>
              <button @click="newContact.is_primary = !newContact.is_primary"
                class="w-11 h-[26px] rounded-full relative transition-colors"
                :style="{ background: newContact.is_primary ? 'var(--color-accent)' : 'var(--color-divider)' }">
                <div class="absolute top-0.5 w-[22px] h-[22px] rounded-full transition-all"
                  :style="{
                    left: newContact.is_primary ? '20px' : '2px',
                    background: 'var(--color-card)',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.18)',
                  }" />
              </button>
            </div>

            <div class="mt-5 text-center text-[12px] font-serif italic"
              style="color: var(--color-ink-3);">
              添加后会出现在客户详情的联系人列表中
            </div>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>
