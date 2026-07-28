<script setup lang="ts">
import type { WorkData } from '@/types'
import { getMediaUrl, getMediaCount, isVideoType, formatDate, getTags } from '@/utils'
import { ElIcon } from 'element-plus'
import {
  ArrowLeft,
  CaretLeft,
  CaretRight,
  Star,
  StarFilled,
  Message,
  Share,
  PriceTag,
  Document,
  Download,
  CopyDocument,
  User,
} from '@element-plus/icons-vue'
import VideoPlayer from './VideoPlayer.vue'

const props = defineProps<{
  work: WorkData
}>()

const emit = defineEmits<{
  goBack: []
  downloadAll: []
  copyLink: []
}>()

const activeIndex = defineModel<number>('activeIndex', { default: 0 })

function prevMedia(): void {
  if (activeIndex.value > 0) {
    activeIndex.value--
  }
}

function nextMedia(): void {
  const count = getMediaCount(props.work)
  if (activeIndex.value < count - 1) {
    activeIndex.value++
  }
}
</script>

<template>
  <div class="space-y-6">
    <button
      @click="emit('goBack')"
      class="flex items-center gap-2 text-text-secondary hover:text-text transition-colors"
    >
      <ElIcon><ArrowLeft /></ElIcon>
      返回列表
    </button>

    <div class="bg-surface rounded-xl shadow-sm overflow-hidden">
      <div class="flex flex-col lg:flex-row">
        <div class="lg:w-3/5 relative bg-gray-900">
          <div v-if="isVideoType(work)" class="relative aspect-video w-full h-full object-contain">
            <VideoPlayer
              :url="getMediaUrl(work, 0)"
              :poster="work.文件访问信息?.[0]?.thumbnail_url || ''"
              video-fill-mode="contain"
            />
          </div>
          <div v-else class="relative">
            <img
              :src="getMediaUrl(work, activeIndex)"
              :alt="work.作品标题 || '作品图片'"
              class="w-full max-h-[60vh] object-contain"
            />
            <button
              v-if="getMediaCount(work) > 1"
              @click="prevMedia"
              :disabled="activeIndex === 0"
              class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/50 text-white rounded-full flex items-center justify-center hover:bg-black/70 transition-colors disabled:opacity-30"
            >
              <ElIcon><CaretLeft /></ElIcon>
            </button>
            <button
              v-if="getMediaCount(work) > 1"
              @click="nextMedia"
              :disabled="activeIndex === getMediaCount(work) - 1"
              class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/50 text-white rounded-full flex items-center justify-center hover:bg-black/70 transition-colors disabled:opacity-30"
            >
              <ElIcon><CaretRight /></ElIcon>
            </button>
            <div
              v-if="getMediaCount(work) > 1"
              class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2"
            >
              <span
                v-for="(_, index) in getMediaCount(work)"
                :key="index"
                class="w-2 h-2 rounded-full transition-colors"
                :class="index === activeIndex ? 'bg-white' : 'bg-white/50'"
              ></span>
            </div>
            <div class="absolute bottom-4 right-4 px-3 py-1 bg-black/50 text-white text-sm rounded">
              {{ activeIndex + 1 }} / {{ getMediaCount(work) }}
            </div>
          </div>
        </div>

        <div class="lg:w-2/5 p-6">
          <h1 class="text-xl font-semibold text-text mb-4">{{ work.作品标题 || '未知标题' }}</h1>

          <div class="space-y-3 mb-6">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <ElIcon class="w-5 h-5 text-text-muted"><User /></ElIcon>
              </div>
              <div>
                <div class="font-medium text-text">{{ work.作者昵称 || '未知作者' }}</div>
                <div class="text-sm text-text-muted">{{ formatDate(work.发布时间) }}</div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-6 mb-6">
            <div class="flex items-center gap-1">
              <ElIcon class="w-5 h-5 text-error"><StarFilled /></ElIcon>
              <span class="text-text">{{ work.点赞数量 || '0' }}</span>
            </div>
            <div class="flex items-center gap-1">
              <ElIcon class="w-5 h-5 text-warning"><Star /></ElIcon>
              <span class="text-text">{{ work.收藏数量 || '0' }}</span>
            </div>
            <div class="flex items-center gap-1">
              <ElIcon class="w-5 h-5 text-text-secondary"><Message /></ElIcon>
              <span class="text-text">{{ work.评论数量 || '0' }}</span>
            </div>
            <div class="flex items-center gap-1">
              <ElIcon class="w-5 h-5 text-text-secondary"><Share /></ElIcon>
              <span class="text-text">{{ work.分享数量 || '0' }}</span>
            </div>
          </div>

          <div class="mb-6" v-if="getTags(work).length > 0">
            <div class="flex items-center gap-2 mb-2">
              <ElIcon class="w-4 h-4 text-text-muted"><PriceTag /></ElIcon>
              <span class="text-sm font-medium text-text-secondary">标签</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in getTags(work)"
                :key="tag"
                class="px-2 py-1 bg-gray-100 text-text-secondary text-sm rounded"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="mb-6" v-if="work.作品描述">
            <div class="flex items-center gap-2 mb-2">
              <ElIcon class="w-4 h-4 text-text-muted"><Document /></ElIcon>
              <span class="text-sm font-medium text-text-secondary">作品描述</span>
            </div>
            <p class="text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
              {{ work.作品描述 }}
            </p>
          </div>

          <div class="flex items-center gap-3">
            <button
              @click="emit('downloadAll')"
              class="flex-1 px-4 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors flex items-center justify-center gap-2"
            >
              <ElIcon><Download /></ElIcon>
              下载全部
            </button>
            <button
              @click="emit('copyLink')"
              class="px-4 py-2.5 bg-gray-100 text-text font-medium rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
            >
              <ElIcon><CopyDocument /></ElIcon>
              复制链接
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
