<script setup lang="ts">
import { ref } from 'vue'
import type { WorkData } from '@/types'
import { getThumbnailUrl, isVideoType, formatShortDate } from '@/utils'
import { ElIcon } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

defineProps<{
  works: WorkData[]
}>()

const emit = defineEmits<{
  viewDetail: [id: string]
  deleteWork: [id: string]
}>()

const imageErrors = ref<Set<string>>(new Set())

function handleImageError(workId: string) {
  imageErrors.value.add(workId)
}

function handleCardClick(workId: string, event: MouseEvent) {
  // 如果点击的是删除按钮，不触发卡片点击
  if ((event.target as HTMLElement).closest('.delete-btn')) {
    return
  }
  emit('viewDetail', workId)
}

function handleDeleteClick(workId: string, event: MouseEvent) {
  event.stopPropagation()
  emit('deleteWork', workId)
}
</script>

<template>
  <div class="sm:hidden space-y-3 p-3">
    <div
      v-for="work in works"
      :key="work.作品ID"
      class="relative flex gap-3 p-3 bg-gray-50 rounded-lg active:bg-gray-100 transition-colors cursor-pointer"
      @click="handleCardClick(work.作品ID, $event)"
    >
      <!-- 缩略图 -->
      <div class="relative w-20 h-20 rounded-lg overflow-hidden bg-gray-200 shrink-0">
        <img
          v-if="!imageErrors.has(work.作品ID)"
          :src="getThumbnailUrl(work)"
          :alt="work.作品标题 || '缩略图'"
          class="w-full h-full object-cover"
          @error="handleImageError(work.作品ID)"
        />
        <!-- 占位图 -->
        <div
          v-else
          class="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-200 to-gray-300"
        >
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
      
      <!-- 内容信息 -->
      <div class="flex-1 min-w-0 flex flex-col justify-between py-1">
        <div>
          <h4 class="font-medium text-text text-base line-clamp-2 mb-1">{{ work.作品标题 || '未知标题' }}</h4>
          <div class="flex items-center gap-2 text-text-secondary text-sm">
            <span>{{ work.作者昵称 || '未知作者' }}</span>
            <span
              class="px-2 py-0.5 text-xs rounded-full"
              :class="isVideoType(work) ? 'bg-info/10 text-info' : 'bg-success/10 text-success'"
            >
              {{ work.作品类型 || '未知' }}
            </span>
          </div>
          <div class="text-text-muted text-xs mt-1">{{ formatShortDate(work.发布时间) }}</div>
        </div>
      </div>
      
      <!-- 删除按钮（悬浮右上角） -->
      <button
        class="delete-btn absolute top-1 right-1 w-8 h-8 flex items-center justify-center bg-white/90 backdrop-blur-sm text-error hover:bg-error hover:text-white rounded-full shadow-md transition-all"
        @click="handleDeleteClick(work.作品ID, $event)"
      >
        <ElIcon class="w-4 h-4"><Delete /></ElIcon>
      </button>
    </div>
  </div>
</template>

<style scoped>
.delete-btn {
  opacity: 0;
  transition: all 0.3s ease;
}

/* 悬停显示删除按钮，但在移动端使用触摸更好 */
@media (hover: hover) {
  .delete-btn {
    opacity: 0;
  }
  
  button:hover .delete-btn {
    opacity: 1;
  }
}

/* 移动端默认显示 */
@media (max-width: 640px) {
  .delete-btn {
    opacity: 0.7;
  }
  
  .delete-btn:active {
    opacity: 1;
  }
}
</style>