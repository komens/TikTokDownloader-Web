<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { watch } from 'vue'
import AppLayout from '@/components/AppLayout.vue'

const route = useRoute()

// 监听路由变化，更新页面标题和描述
watch(
  () => route.meta,
  (meta) => {
    // 更新页面标题
    if (meta.title) {
      document.title = meta.title as string
    }
    
    // 更新页面描述
    if (meta.description) {
      let descriptionMeta = document.querySelector('meta[name="description"]')
      if (descriptionMeta) {
        descriptionMeta.setAttribute('content', meta.description as string)
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>
