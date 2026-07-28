<script setup lang="ts">
import { ref } from 'vue'
import type { WorkData } from '@/types'
import { getThumbnailUrl, isVideoType, formatShortDate } from '@/utils'
import { ElIcon } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import TaskMobileCard from './TaskMobileCard.vue'

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
</script>

<template>
  <div class="bg-surface rounded-xl shadow-sm overflow-hidden">
    <div class="hidden sm:block overflow-x-auto">
      <table class="w-full min-w-[640px]">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">缩略图</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">作品标题</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">作者</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">类型</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">时间</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-text-secondary">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="work in works" :key="work.作品ID" class="border-t border-border hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3">
              <div class="relative w-12 h-12 rounded-lg overflow-hidden bg-gray-200">
                <!-- 缩略图 -->
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
                  <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </td>
            <td class="px-4 py-3">
              <span class="text-text truncate inline-block max-w-xs">{{ work.作品标题 || '未知标题' }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="text-text-secondary">{{ work.作者昵称 || '未知作者' }}</span>
            </td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 text-xs rounded-full"
                :class="isVideoType(work) ? 'bg-info/10 text-info' : 'bg-success/10 text-success'"
              >
                {{ work.作品类型 || '未知' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span class="text-text-muted text-sm">{{ formatShortDate(work.发布时间) }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <button
                  @click="emit('viewDetail', work.作品ID)"
                  class="px-3 py-1 text-primary text-sm hover:bg-primary/10 rounded-lg transition-colors"
                >
                  详情
                </button>
                <button
                  @click="emit('deleteWork', work.作品ID)"
                  class="px-3 py-1 text-error text-sm hover:bg-error/10 rounded-lg transition-colors"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <TaskMobileCard
      :works="works"
      @viewDetail="emit('viewDetail', $event)"
      @deleteWork="emit('deleteWork', $event)"
    />

    <div v-if="works.length === 0" class="text-center py-12">
      <ElIcon class="w-12 h-12 text-text-muted mx-auto mb-4"><Picture /></ElIcon>
      <p class="text-text-secondary">暂无作品数据</p>
    </div>
  </div>
</template>