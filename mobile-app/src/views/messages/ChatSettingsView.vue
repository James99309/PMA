<script setup>
// 群聊设置 —— 真后端版本
// 加载会话详情（成员、关联项目、公告等）
// 支持：添加成员（用户搜索 sheet）、删除成员（owner）、退群（自己）
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NavBar from '@/components/common/NavBar.vue'
import Section from '@/components/common/Section.vue'
import ProjectRefCard from '@/components/common/refs/ProjectRefCard.vue'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()
import {
  getConversation, addParticipants, removeParticipant,
  deleteConversation, searchUsers,
} from '@/api/chat'

const route = useRoute()
const router = useRouter()

const convId = computed(() => Number(route.params.id))
const isNumericConv = computed(() => /^\d+$/.test(String(route.params.id)))

const loading = ref(true)
const detail = ref(null)  // { id, name, type, created_at, announcement, is_owner, participants, linked_project }

const muted = ref(false)
const pinned = ref(true)

// 添加成员 sheet
const showAddSheet = ref(false)
const addSearch = ref('')
const addResults = ref([])
const addLoading = ref(false)
const adding = ref(false)
let addSearchTimer = null

async function load() {
  if (!isNumericConv.value) {
    // proj-* 等虚拟会话：没有后端数据，展示降级 UI
    detail.value = {
      id: route.params.id,
      name: route.query.name || '群聊',
      type: 'group',
      created_at: null,
      announcement: '',
      is_owner: false,
      participants: [],
      linked_project: null,
    }
    loading.value = false
    return
  }
  loading.value = true
  try {
    const r = await getConversation(convId.value)
    if (r.data?.success) {
      detail.value = r.data.data
    } else {
      alert(r.data?.message || '加载会话详情失败')
      router.back()
    }
  } catch (e) {
    console.error('load conv detail failed', e)
    alert(`加载失败：${e.message || e}`)
  } finally {
    loading.value = false
  }
}

const initial = computed(() => (detail.value?.name || '群')[0])
const memberCount = computed(() => detail.value?.participants?.length || 0)
const formattedCreatedAt = computed(() => {
  if (!detail.value?.created_at) return ''
  try {
    const d = new Date(detail.value.created_at)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return ''
  }
})

function viewLinkedProject() {
  const pid = detail.value?.linked_project?.id
  if (pid) router.push(`/projects/${pid}`)
}

// ─── 添加成员 ─────────────────────────────────────────────────
function openAddSheet() {
  if (!isNumericConv.value) {
    alert('该会话暂不支持添加成员')
    return
  }
  showAddSheet.value = true
  addSearch.value = ''
  addResults.value = []
  // 默认拉一批活跃用户
  doAddSearch('')
}

function closeAddSheet() {
  showAddSheet.value = false
}

function onAddSearchInput() {
  clearTimeout(addSearchTimer)
  addSearchTimer = setTimeout(() => doAddSearch(addSearch.value.trim()), 250)
}

async function doAddSearch(q) {
  addLoading.value = true
  try {
    const r = await searchUsers(q)
    const all = r.data?.success ? (r.data.data || []) : []
    // 过滤掉已在群里的
    const existIds = new Set((detail.value?.participants || []).map(p => p.user_id))
    addResults.value = all.filter(u => !existIds.has(u.id))
  } catch (e) {
    console.error('search users failed', e)
    addResults.value = []
  } finally {
    addLoading.value = false
  }
}

async function pickToAdd(u) {
  if (adding.value) return
  adding.value = true
  try {
    const r = await addParticipants(convId.value, [u.id])
    if (r.data?.success) {
      // 重新拉详情，刷新成员
      await load()
      closeAddSheet()
    } else {
      alert(r.data?.message || '添加失败')
    }
  } catch (e) {
    console.error('add participant failed', e)
    alert(`添加失败：${e.message || e}`)
  } finally {
    adding.value = false
  }
}

// ─── 删除成员 / 退群 ──────────────────────────────────────────
async function removeMember(member) {
  if (!isNumericConv.value) return
  if (member.is_self) {
    return leaveGroup()
  }
  if (!detail.value.is_owner) {
    alert('只有群主可以移除其他成员')
    return
  }
  if (!confirm(`将「${member.name}」移出群聊？`)) return
  try {
    const r = await removeParticipant(convId.value, member.user_id)
    if (r.data?.success) {
      await load()
    } else {
      alert(r.data?.message || '移除失败')
    }
  } catch (e) {
    console.error('remove participant failed', e)
    alert(`移除失败：${e.message || e}`)
  }
}

onMounted(load)

async function leaveGroup() {
  if (!confirm(`退出「${detail.value?.name}」群聊？`)) return
  if (!isNumericConv.value) {
    router.back()
    return
  }
  try {
    // 先尝试用 remove_participant 把自己移出（也会同步项目共享）
    const me = (detail.value?.participants || []).find(p => p.is_self)
    if (me) {
      const r = await removeParticipant(convId.value, me.user_id)
      if (r.data?.success) {
        router.push('/messages')
        return
      }
      // 如果是最后一人，回退到删除会话
      if (r.data?.message?.includes('至少需保留')) {
        const dr = await deleteConversation(convId.value)
        if (dr.data?.success) {
          router.push('/messages')
          return
        }
        alert(dr.data?.message || '退出失败')
        return
      }
      alert(r.data?.message || '退出失败')
    }
  } catch (e) {
    console.error('leave group failed', e)
    alert(`退出失败：${e.message || e}`)
  }
}
</script>

<template>
  <div class="flex flex-col h-full overflow-y-auto" :style="[{ background: 'var(--color-bg)' }, kbStyle]">

    <NavBar back-label="返回" title="聊天设置" @back="router.back()" />

    <!-- 加载中 -->
    <div v-if="loading" class="flex justify-center items-center py-16">
      <div class="w-6 h-6 border-2 rounded-full animate-spin"
        style="border-color: var(--color-accent); border-top-color: transparent;" />
    </div>

    <template v-else-if="detail">
      <!-- Hero：群头像 + 名 + 元信息 -->
      <div class="px-6 pt-6 pb-5 flex flex-col items-center gap-3">
        <div class="w-16 h-16 rounded-2xl inline-flex items-center justify-center font-serif font-medium"
          style="background: var(--color-accent-soft); color: var(--color-accent); font-size: 28px;">
          {{ initial }}
        </div>
        <div class="font-serif text-center"
          style="font-size: 19px; font-weight: 500; line-height: 1.3; color: var(--color-ink);">
          {{ detail.name || '群聊' }}
        </div>
        <div class="text-[12px]" style="color: var(--color-ink-3);">
          {{ memberCount }} 人<span v-if="formattedCreatedAt"> · 创建于 {{ formattedCreatedAt }}</span>
        </div>
      </div>

      <!-- 关联项目（仅项目群有） -->
      <Section v-if="detail.linked_project" title="关联">
        <ProjectRefCard
          :name="detail.linked_project.name"
          :stage="detail.linked_project.stage"
          stage-tone="#D97757"
          :amount="(detail.linked_project.amount || 0).toFixed(2)"
          :owner="detail.linked_project.owner"
          :region="detail.linked_project.region"
          @click="viewLinkedProject" />
      </Section>

      <!-- 公告（仅当存在时） -->
      <Section v-if="detail.announcement" title="公告">
        <div class="rounded-2xl px-4 py-3.5 font-serif italic"
          style="background: var(--color-card); border: 1px solid var(--color-divider);
                 font-size: 14px; color: var(--color-ink-2); line-height: 1.55;">
          {{ detail.announcement }}
        </div>
      </Section>

      <!-- 成员 -->
      <Section :title="`成员 · ${memberCount}`">
        <template #action>
          <button @click="openAddSheet"
            class="text-[12px] font-medium active:opacity-60"
            style="color: var(--color-accent);">+ 添加</button>
        </template>
        <div v-if="memberCount === 0"
          class="rounded-2xl px-4 py-6 text-center text-[12px]"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: var(--color-ink-3);">
          暂无成员
        </div>
        <div v-else class="rounded-2xl"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div v-for="(m, i) in detail.participants" :key="m.user_id"
            class="px-4 py-3 flex items-center gap-3"
            :style="i < memberCount - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
            <div class="w-8 h-8 rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold"
              style="background: var(--color-accent-soft); color: var(--color-accent);">{{ m.avatar }}</div>
            <div class="flex-1 min-w-0">
              <div class="font-serif" style="font-size: 14px; font-weight: 500;">
                {{ m.name }}<span v-if="m.is_self" class="ml-1 text-[11px]" style="color: var(--color-ink-3);">（我）</span>
              </div>
              <div v-if="m.dept" class="text-[11px]" style="color: var(--color-ink-3);">{{ m.dept }}</div>
            </div>
            <span v-if="m.role === 'owner'" class="text-[10px] font-semibold px-1.5 py-px rounded"
              style="background: var(--color-bg); color: var(--color-ink-3); letter-spacing: 0.4px;">群主</span>
            <!-- 移除按钮：群主可移除非自己；自己不显示（自己用底部退群） -->
            <button v-if="detail.is_owner && !m.is_self"
              @click="removeMember(m)"
              class="ml-1 w-7 h-7 inline-flex items-center justify-center active:opacity-50"
              style="color: var(--color-ink-3); font-size: 16px;"
              title="移除成员">×</button>
          </div>
        </div>
      </Section>

      <!-- 选项 -->
      <Section title="选项">
        <div class="rounded-2xl"
          style="background: var(--color-card); border: 1px solid var(--color-divider);">
          <div class="px-4 py-3.5 flex justify-between items-center text-[14px]"
            style="border-bottom: 1px solid var(--color-divider);">
            <span style="color: var(--color-ink-2);">消息免打扰</span>
            <button @click="muted = !muted"
              class="w-11 h-[26px] rounded-full relative transition-colors"
              :style="{ background: muted ? 'var(--color-accent)' : 'var(--color-divider)' }">
              <div class="absolute top-0.5 w-[22px] h-[22px] rounded-full transition-all"
                :style="{ left: muted ? '20px' : '2px', background: 'var(--color-card)',
                         boxShadow: '0 1px 3px rgba(0,0,0,0.18)' }" />
            </button>
          </div>
          <div class="px-4 py-3.5 flex justify-between items-center text-[14px]">
            <span style="color: var(--color-ink-2);">置顶聊天</span>
            <button @click="pinned = !pinned"
              class="w-11 h-[26px] rounded-full relative transition-colors"
              :style="{ background: pinned ? 'var(--color-accent)' : 'var(--color-divider)' }">
              <div class="absolute top-0.5 w-[22px] h-[22px] rounded-full transition-all"
                :style="{ left: pinned ? '20px' : '2px', background: 'var(--color-card)',
                         boxShadow: '0 1px 3px rgba(0,0,0,0.18)' }" />
            </button>
          </div>
        </div>
      </Section>

      <!-- 退出群聊 -->
      <div class="px-7 pt-4 pb-8">
        <button @click="leaveGroup"
          class="w-full py-3.5 rounded-2xl text-[14px] font-medium active:opacity-70"
          style="background: var(--color-card); border: 1px solid var(--color-divider); color: #A04848;">
          退出群聊
        </button>
      </div>
    </template>

    <!-- 添加成员 sheet -->
    <transition name="sheet">
      <div v-if="showAddSheet" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(0,0,0,0.32);" @click.self="closeAddSheet">
        <div class="mt-auto rounded-t-3xl flex flex-col"
          style="background: var(--color-bg); max-height: 80vh; min-height: 50vh;">
          <!-- header -->
          <div class="px-5 pt-4 pb-2 flex items-center justify-between shrink-0">
            <button @click="closeAddSheet" class="text-[13px]"
              style="color: var(--color-ink-3);">取消</button>
            <span class="font-serif" style="font-size: 16px; font-weight: 500;">添加成员</span>
            <span class="w-8" />
          </div>
          <div class="px-5 pb-3 shrink-0">
            <input v-model="addSearch" @input="onAddSearchInput"
              type="text" placeholder="搜索姓名 / 部门"
              class="w-full px-4 py-2.5 rounded-xl text-[14px]"
              style="background: var(--color-card); border: 1px solid var(--color-divider); outline: none;" />
          </div>
          <!-- list -->
          <div class="flex-1 overflow-y-auto px-3 pb-6">
            <div v-if="addLoading" class="flex justify-center py-6">
              <div class="w-5 h-5 border-2 rounded-full animate-spin"
                style="border-color: var(--color-accent); border-top-color: transparent;" />
            </div>
            <div v-else-if="!addResults.length" class="text-center py-8 text-[13px]"
              style="color: var(--color-ink-3);">
              {{ addSearch ? '没有找到匹配的用户' : '暂无可添加的用户' }}
            </div>
            <button v-else v-for="u in addResults" :key="u.id"
              @click="pickToAdd(u)"
              class="w-full flex items-center gap-3 px-3 py-3 active:bg-bg text-left rounded-xl"
              :disabled="adding">
              <div class="w-9 h-9 rounded-full inline-flex items-center justify-center font-serif text-[13px] font-semibold"
                style="background: var(--color-accent-soft); color: var(--color-accent);">{{ u.avatar || u.name?.[0] || '?' }}</div>
              <div class="flex-1 min-w-0">
                <div class="font-serif truncate" style="font-size: 14px; font-weight: 500;">{{ u.name }}</div>
                <div v-if="u.dept" class="text-[11px] truncate" style="color: var(--color-ink-3);">{{ u.dept }}</div>
              </div>
              <span class="text-[12px] font-medium" style="color: var(--color-accent);">添加</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
</style>
