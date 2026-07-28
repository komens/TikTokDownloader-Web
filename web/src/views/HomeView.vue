<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDownloadStore } from '@/stores/download'
import { ElMessage, ElIcon } from 'element-plus'
import {
  Plus,
  Link,
  Loading,
  Warning,
  Delete,
  Collection,
  CircleCheck,
} from '@element-plus/icons-vue'

const downloadStore = useDownloadStore()
const inputUrl = ref('')
const isAdding = ref(false)

function validateUrl(url: string): boolean {
  return /(v\.douyin\.com|douyin\.com|iesdouyin\.com)/i.test(url)
}

async function addToQueue(): Promise<void> {
  if (!inputUrl.value.trim()) {
    ElMessage.warning('请输入抖音链接')
    return
  }
  if (!validateUrl(inputUrl.value)) {
    ElMessage.warning('请输入有效的抖音链接')
    return
  }
  isAdding.value = true
  try {
    const success = await downloadStore.addItem(inputUrl.value)
    if (success) {
      ElMessage.success('已添加到下载队列')
      inputUrl.value = ''
    } else {
      ElMessage.error('添加失败，请稍后重试')
    }
  } catch (error) {
    ElMessage.error('添加失败，请稍后重试')
  } finally {
    isAdding.value = false
  }
}

async function removeItem(workId: string): Promise<void> {
  try {
    await downloadStore.removeItem(workId)
    ElMessage.info('已移除')
  } catch (error) {
    ElMessage.error('移除失败')
  }
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  downloadStore.startPolling()
})

onUnmounted(() => {
  downloadStore.stopPolling()
})
</script>

<template>
  <div class="space-y-4 sm:space-y-6">
    <div class="bg-surface rounded-xl shadow-sm p-4 sm:p-6">
      <div class="flex flex-col sm:flex-row gap-3 sm:gap-4">
        <div class="flex-1 flex items-center border border-border rounded-xl focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          <ElIcon class="w-5 h-5 text-text-muted ml-3 sm:ml-4 shrink-0"><Link /></ElIcon>
          <input
            v-model="inputUrl"
            type="text"
            placeholder="输入抖音作品或账号链接..."
            class="flex-1 px-3 sm:px-4 py-3 text-text text-sm sm:text-base placeholder:text-text-muted focus:outline-none bg-transparent"
            @keyup.enter="addToQueue"
            autocomplete="off"
          />
        </div>
        <button
          @click="addToQueue"
          :disabled="isAdding"
          class="px-5 sm:px-6 py-3 bg-primary text-white font-medium rounded-xl hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap"
        >
          <ElIcon><Plus /></ElIcon>
          <span class="text-sm sm:text-base">添加</span>
        </button>
      </div>
    </div>

    <div class="bg-surface rounded-xl shadow-sm p-4 sm:p-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div class="flex flex-wrap items-center gap-2 sm:gap-4">
          <div class="flex items-center gap-1.5 sm:gap-2">
            <span class="text-text-secondary text-xs sm:text-sm">待下载:</span>
            <span class="px-2 py-0.5 bg-warning/10 text-warning text-xs sm:text-sm rounded-full font-medium">{{ downloadStore.pendingCount }}</span>
          </div>
          <div class="flex items-center gap-1.5 sm:gap-2">
            <span class="text-text-secondary text-xs sm:text-sm">下载中:</span>
            <span class="px-2 py-0.5 bg-info/10 text-info text-xs sm:text-sm rounded-full font-medium">{{ downloadStore.downloadingCount }}</span>
          </div>
          <div class="flex items-center gap-1.5 sm:gap-2">
            <span class="text-text-secondary text-xs sm:text-sm">已完成:</span>
            <span class="px-2 py-0.5 bg-success/10 text-success text-xs sm:text-sm rounded-full font-medium">{{ downloadStore.completedCount }}</span>
          </div>
          <div class="flex items-center gap-1.5 sm:gap-2">
            <span class="text-text-secondary text-xs sm:text-sm">失败:</span>
            <span class="px-2 py-0.5 bg-error/10 text-error text-xs sm:text-sm rounded-full">{{ downloadStore.failedCount }}</span>
          </div>
        </div>
      </div>

      <div v-if="downloadStore.queue.length === 0" class="text-center py-10 sm:py-12">
        <div class="w-16 h-16 sm:w-20 sm:h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
          <ElIcon class="w-8 h-8 sm:w-10 sm:h-10 text-text-muted"><Collection /></ElIcon>
        </div>
        <p class="text-text-secondary text-sm sm:text-base">暂无下载任务</p>
        <p class="text-text-muted text-xs sm:text-sm mt-1">输入链接后自动开始下载</p>
      </div>

      <div v-else class="space-y-2 sm:space-y-3">
        <div
          v-for="(item, index) in downloadStore.queue"
          :key="item.work_id"
          class="p-3 sm:p-4 bg-gray-50 rounded-lg border border-border hover:border-primary/30 transition-colors"
        >
          <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2 sm:gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span class="px-1.5 py-0.5 bg-gray-200 text-text-muted text-xs rounded shrink-0">{{ index + 1 }}</span>
                <span
                  class="px-2 py-0.5 text-xs rounded-full flex items-center gap-1 shrink-0"
                  :class="{
                    'bg-warning/10 text-warning': item.status === 'pending',
                    'bg-info/10 text-info': item.status === 'downloading',
                    'bg-success/10 text-success': item.status === 'completed',
                    'bg-error/10 text-error': item.status === 'failed',
                  }"
                >
                  <ElIcon class="w-3 h-3" :class="{ 'animate-spin': item.status === 'downloading' }">
                    <Loading v-if="item.status === 'downloading'" />
                    <CircleCheck v-else-if="item.status === 'completed'" />
                    <Warning v-else-if="item.status === 'failed'" />
                    <Collection v-else />
                  </ElIcon>
                  {{ {
                    'pending': '待下载',
                    'downloading': '下载中',
                    'completed': '已完成',
                    'failed': '下载失败',
                  }[item.status] }}
                </span>
              </div>
              <div class="text-sm text-text line-clamp-1 sm:line-clamp-2 break-all mb-1 sm:mb-2">
                {{ item.title || '未知作品' }}
              </div>
              <div class="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-text-muted">
                <span>{{ item.author || '未知作者' }}</span>
                <span>·</span>
                <span>{{ formatTimestamp(item.added_at) }}</span>
              </div>
              <div v-if="item.error_message" class="text-xs sm:text-sm text-error mt-1 flex items-center gap-1">
                <ElIcon class="w-3 h-3"><Warning /></ElIcon>
                {{ item.error_message }}
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                @click="removeItem(item.work_id)"
                class="px-3 py-1.5 text-text-muted hover:text-error hover:bg-error/10 text-xs sm:text-sm rounded-lg transition-colors"
              >
                <ElIcon class="w-4 h-4"><Delete /></ElIcon>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>