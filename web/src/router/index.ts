import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      title: 'TikTokDownloader Web - 作品下载',
      description: '下载抖音作品，支持图片、视频等多种格式'
    }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/TaskListView/index.vue'),
    meta: {
      title: 'TikTokDownloader Web - 作品列表',
      description: '查看所有下载的作品列表'
    }
  },
  {
    path: '/detail/:id',
    name: 'Detail',
    component: () => import('@/views/DetailView/index.vue'),
    meta: {
      title: 'TikTokDownloader Web - 作品详情',
      description: '查看作品详细信息'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: {
      title: 'TikTokDownloader Web - 系统设置',
      description: '配置下载参数和系统设置'
    }
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
