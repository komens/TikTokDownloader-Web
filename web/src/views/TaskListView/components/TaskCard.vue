<script setup lang="ts">
import { ref } from 'vue'
import type { WorkData } from '@/types'
import { getThumbnailUrl } from '@/utils'
import { ElIcon } from 'element-plus'
import { Star } from '@element-plus/icons-vue'

defineProps<{
  work: WorkData
}>()

const emit = defineEmits<{
  click: []
}>()

const imageError = ref(false)

function handleImageError() {
  imageError.value = true
}
</script>

<template>
  <div
    class="break-inside-avoid bg-surface rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
    @click="emit('click')"
  >
    <div class="relative">
      <!-- 缩略图 -->
      <img
        v-if="!imageError"
        :src="getThumbnailUrl(work)"
        :alt="work.作品标题 || '缩略图'"
        class="w-full object-cover group-hover:opacity-90 transition-opacity"
        loading="lazy"
        @error="handleImageError"
      />
      <!-- 占位图 -->
      <div
        v-else
        class="w-full aspect-square flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200"
      >
        <svg class="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <div class="absolute top-2 right-2 px-2 py-0.5 bg-black/70 backdrop-blur-sm text-white text-xs rounded">
        {{ work.作品类型 || '未知' }}
      </div>
    </div>
    <div class="p-3 sm:p-4">
      <h3 class="font-medium text-text text-sm sm:text-base line-clamp-2 mb-2">{{ work.作品标题 || '未知标题' }}</h3>
      <div class="flex items-center justify-between">
        <span class="text-text-muted text-xs sm:text-sm">{{ work.作者昵称 || '未知作者' }}</span>
        <div class="flex items-center gap-1 text-text-muted text-xs sm:text-sm">
          <ElIcon class="w-3 sm:w-4 h-3 sm:h-4"><Star /></ElIcon>
          {{ work.点赞数量 || '0' }}
        </div>
      </div>
    </div>
  </div>
</template>