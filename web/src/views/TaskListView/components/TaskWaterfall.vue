<script setup lang="ts">
import type { WorkData } from '@/types'
import TaskCard from './TaskCard.vue'

defineProps<{
  works: WorkData[]
}>()

const emit = defineEmits<{
  viewDetail: [id: string]
}>()
</script>

<template>
  <div class="waterfall-container">
    <TaskCard
      v-for="work in works"
      :key="work.作品ID"
      :work="work"
      @click="emit('viewDetail', work.作品ID)"
    />
  </div>
</template>

<style scoped>
.waterfall-container {
  column-count: 2;
  column-gap: 12px;
  width: 100%;
}

/* 响应式列数 */
@media (min-width: 640px) {
  .waterfall-container {
    column-count: 2;
    column-gap: 16px;
  }
}

@media (min-width: 1024px) {
  .waterfall-container {
    column-count: 3;
    column-gap: 16px;
  }
}

@media (min-width: 1280px) {
  .waterfall-container {
    column-count: 4;
    column-gap: 16px;
  }
}

/* 确保卡片不会被截断 */
.waterfall-container > * {
  break-inside: avoid;
  margin-bottom: 12px;
}

@media (min-width: 640px) {
  .waterfall-container > * {
    margin-bottom: 16px;
  }
}

/* 平滑的动画效果 */
.waterfall-container {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>