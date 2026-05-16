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
      { path: 'projects/:id/edit', component: () => import('@/views/projects/ProjectEditView.vue') },
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
      { path: 'customers/scan', component: () => import('@/views/customers/CardScanCaptureView.vue'),
        meta: { hideTabBar: true } },
      { path: 'customers/scan/confirm', component: () => import('@/views/customers/CardScanConfirmView.vue'),
        meta: { hideTabBar: true } },
      { path: 'customers/scan/success', component: () => import('@/views/customers/CardScanSuccessView.vue'),
        meta: { hideTabBar: true } },
      { path: 'customers/:id', component: () => import('@/views/customers/CustomerDetailView.vue') },
      { path: 'customers/:id/edit', component: () => import('@/views/customers/CustomerEditView.vue') },
      { path: 'customers/:cid/contacts/:contactId', component: () => import('@/views/customers/ContactDetailView.vue'),
        meta: { hideTabBar: true } },
      { path: 'quotations/:id', component: () => import('@/views/quotations/QuotationDetailView.vue') },
      // 报销模块
      { path: 'expense', component: () => import('@/views/expense/ExpenseListView.vue') },
      { path: 'expense/new', component: () => import('@/views/expense/ExpenseEditView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id', component: () => import('@/views/expense/ExpenseDetailView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id/edit', component: () => import('@/views/expense/ExpenseEditView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id/capture', component: () => import('@/views/expense/ReceiptCaptureView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id/processing', component: () => import('@/views/expense/ReceiptProcessingView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id/confirm', component: () => import('@/views/expense/ReceiptConfirmView.vue'),
        meta: { hideTabBar: true } },
      { path: 'expense/:id/merge', component: () => import('@/views/expense/ReceiptMergeView.vue'),
        meta: { hideTabBar: true } },
      // 审批模块详情(列表已存在)
      { path: 'approval/:instanceId', component: () => import('@/views/approval/ApprovalDetailView.vue'),
        meta: { hideTabBar: true } },
      { path: 'profile', component: () => import('@/views/profile/ProfileView.vue') },
      { path: 'tasks', component: () => import('@/views/tasks/TaskListView.vue'),
        meta: { hideTabBar: true } },
      { path: 'tasks/new', component: () => import('@/views/tasks/TaskCreateView.vue'),
        meta: { hideTabBar: true } },
      { path: 'tasks/:id', component: () => import('@/views/tasks/TaskDetailView.vue'),
        meta: { hideTabBar: true } },
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
