<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDownloadStore } from '@/stores/download'
import { ElIcon } from 'element-plus'
import {
  Download,
  HomeFilled,
  List,
  Setting,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const downloadStore = useDownloadStore()

const isMobile = ref(false)

const navItems = [
  { path: '/', name: '首页', icon: HomeFilled },
  { path: '/tasks', name: '任务列表', icon: List },
  { path: '/settings', name: '设置', icon: Setting },
]

const currentPath = computed(() => route.path)
const isDetailPage = computed(() => route.name === 'Detail')

function checkMobile(): void {
  isMobile.value = window.innerWidth < 768
}

function navigate(path: string): void {
  router.push(path)
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
</script>

<template>
  <div class="min-h-screen bg-background">
    <header
      v-if="!isMobile"
      class="fixed top-0 left-0 right-0 z-50 bg-surface shadow-sm"
    >
      <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2 cursor-pointer" @click="navigate('/')">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white">
            <ElIcon><Download /></ElIcon>
          </div>
          <span class="font-semibold text-lg text-text">TikTokDownloader Web</span>
        </div>

        <nav class="flex items-center gap-1">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="navigate(item.path)"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="currentPath === item.path ? 'bg-primary/10 text-primary' : 'text-text-secondary hover:text-text hover:bg-gray-100'"
          >
            {{ item.name }}
          </button>
        </nav>

        <div class="flex items-center gap-3">
          <button
            v-if="downloadStore.pendingCount > 0"
            @click="navigate('/')"
            class="px-3 py-1.5 bg-primary text-white text-sm rounded-full flex items-center gap-1 hover:bg-primary-dark transition-colors"
          >
            <ElIcon><Download /></ElIcon>
            <span>{{ downloadStore.pendingCount }}</span>
          </button>
        </div>
      </div>
    </header>

    <main class="transition-all duration-300" :class="isMobile ? (isDetailPage ? '' : 'pb-16') : 'pt-14'">
      <div :class="isMobile && isDetailPage ? '' : 'max-w-5xl mx-auto px-4 py-6'">
        <slot />
      </div>
    </main>

    <nav
      v-if="isMobile && !isDetailPage"
      class="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border"
    >
      <div class="flex items-center justify-around h-14">
        <button
          v-for="item in navItems"
          :key="item.path"
          @click="navigate(item.path)"
          class="flex flex-col items-center justify-center w-full h-full gap-0.5 transition-colors"
          :class="currentPath === item.path ? 'text-primary' : 'text-text-muted'"
        >
          <ElIcon><component :is="item.icon" /></ElIcon>
          <span class="text-xs">{{ item.name }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>
