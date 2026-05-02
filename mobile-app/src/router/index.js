import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/splash', component: () => import('@/views/SplashView.vue'), meta: { public: true } },
  { path: '/login',  component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/AppShell.vue'),
    children: [
      { path: '', redirect: '/projects' },
      { path: 'projects', component: () => import('@/views/projects/ProjectListView.vue') },
      { path: 'projects/new', component: () => import('@/views/projects/ProjectCreateView.vue') },
      { path: 'projects/:id', component: () => import('@/views/projects/ProjectDetailView.vue') },
      { path: 'approval', component: () => import('@/views/approval/ApprovalView.vue') },
      { path: 'messages',           component: () => import('@/views/messages/ChatListView.vue') },
      { path: 'messages/ai',        component: () => import('@/views/messages/AiChatView.vue'),
        meta: { hideTabBar: true } },
      { path: 'messages/broadcast', component: () => import('@/views/messages/BroadcastView.vue'),
        meta: { hideTabBar: true } },
      { path: 'messages/group/:id', component: () => import('@/views/messages/GroupChatView.vue'),
        meta: { hideTabBar: true } },
      { path: 'messages/group/:id/settings', component: () => import('@/views/messages/ChatSettingsView.vue'),
        meta: { hideTabBar: true } },
      { path: 'messages/dm/:id',    component: () => import('@/views/messages/DmChatView.vue'),
        meta: { hideTabBar: true } },
      { path: 'customers', component: () => import('@/views/customers/CustomerListView.vue') },
      { path: 'customers/new', component: () => import('@/views/customers/CustomerCreateView.vue') },
      { path: 'customers/:id', component: () => import('@/views/customers/CustomerDetailView.vue') },
      { path: 'customers/:id/edit', component: () => import('@/views/customers/CustomerEditView.vue') },
      { path: 'quotations/:id', component: () => import('@/views/quotations/QuotationDetailView.vue') },
      { path: 'profile', component: () => import('@/views/profile/ProfileView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/splash' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 跟踪是否已经播过 splash —— App 启动后只播一次
let splashShown = false

router.beforeEach((to) => {
  const auth = useAuthStore()
  // 第一次进 App 任何页面，先走 splash
  if (!splashShown && to.path !== '/splash') {
    splashShown = true
    return '/splash'
  }
  if (to.path === '/splash') splashShown = true
  if (!to.meta.public && !auth.isLoggedIn) return '/login'
})

export default router
