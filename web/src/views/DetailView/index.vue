<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { douyinApi } from '@/api'
import type { WorkData } from '@/types'
import { getFileAccessInfoList } from '@/utils'
import { ElMessage, ElIcon } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import DetailDesktop from './components/DetailDesktop.vue'
import DetailMobile from './components/DetailMobile.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const work = ref<WorkData | null>(null)
const works = ref<WorkData[]>([])
const isMobile = ref(false)
const activeIndex = ref(0)

/** 从路由 query 解析分页参数（列表页跳转或刷新恢复） */
const initialPage = Number(route.query.page) || 1
const initialPageSize = Number(route.query.pageSize) || 20

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

async function loadWork(): Promise<void> {
  const id = route.params.id as string
  if (!id) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const response = await douyinApi.detail(id)
    work.value = response.data
    activeIndex.value = 0

    // 移动端：加载初始页数据（不滚到对应项，直接以当前页作为起点）
    if (isMobile.value) {
      await loadInitialWorks(id)
    }
  } catch (error) {
    ElMessage.error('加载作品详情失败')
    work.value = null
  } finally {
    loading.value = false
  }
}

/**
 * 加载移动端初始页数据
 * 使用路由 query 中的 page/pageSize 作为起点
 */
async function loadInitialWorks(currentId: string): Promise<void> {
  try {
    const response = await douyinApi.list(initialPage, initialPageSize)
    works.value = response.data || []
    // 兜底：若当前页未包含目标作品，补到首位
    const exists = works.value.some(w => w.作品ID === currentId)
    if (!exists && work.value) {
      works.value.unshift(work.value)
    }
  } catch {
    if (work.value) {
      works.value = [work.value]
    }
  }
}

function goBack(): void {
  // 带上分页信息回列表页，恢复到离开时所在的分页
  router.push({
    path: '/tasks',
    query: {
      page: initialPage,
      pageSize: initialPageSize,
    },
  })
}

async function downloadAll(): Promise<void> {
  if (!work.value) return

  const fileList = getFileAccessInfoList(work.value)
  if (fileList.length === 0) {
    ElMessage.warning('没有可下载的文件')
    return
  }

  for (const fileInfo of fileList) {
    const url = fileInfo.url
    if (!url) continue
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = fileInfo.filename || 'download'
      a.click()
      URL.revokeObjectURL(a.href)
    } catch {
      ElMessage.warning(`下载 ${fileInfo.filename || '文件'} 失败`)
    }
  }

  ElMessage.success('已开始下载所有文件')
}

async function copyLink(): Promise<void> {
  if (!work.value?.作品链接) {
    ElMessage.warning('没有作品链接')
    return
  }
  try {
    await navigator.clipboard.writeText(work.value.作品链接)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadWork()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center py-20">
    <div class="text-center">
      <ElIcon class="w-8 h-8 text-primary animate-spin mx-auto mb-4"><Loading /></ElIcon>
      <p class="text-text-secondary">加载中...</p>
    </div>
  </div>

  <div v-else-if="!work" class="text-center py-20">
    <ElIcon class="w-12 h-12 text-error mx-auto mb-4"><Warning /></ElIcon>
    <p class="text-text-secondary">作品不存在或已被删除</p>
    <button
      @click="goBack"
      class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
    >
      返回列表
    </button>
  </div>

  <template v-else>
    <!-- 移动端：全屏沉浸式 -->
    <DetailMobile
      v-if="isMobile"
      :works="works"
      :current-id="work.作品ID"
      :initial-page="initialPage"
      :page-size="initialPageSize"
      @go-back="goBack"
    />

    <!-- PC端：原有布局 -->
    <DetailDesktop
      v-else
      :work="work"
      v-model:active-index="activeIndex"
      @go-back="goBack"
      @download-all="downloadAll"
      @copy-link="copyLink"
    />
  </template>
</template>
