<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { douyinApi } from '@/api'
import type { WorkData } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import TaskListHeader from './components/TaskListHeader.vue'
import TaskTable from './components/TaskTable.vue'
import TaskWaterfall from './components/TaskWaterfall.vue'
import PaginationBar from './components/PaginationBar.vue'

const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()

const loading = ref(false)
const works = ref<WorkData[]>([])
const total = ref(0)
// 从 URL query 读取分页初始值，支持详情页回退/直接访问分页链接
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(Number(route.query.pageSize) || 20)
const searchParams = ref({
  author_nickname: '',
  author_id: '',
  work_title: '',
  work_desc: '',
})

async function loadWorks(): Promise<void> {
  if (loading.value) return

  loading.value = true

  try {
    const response = await douyinApi.list(page.value, pageSize.value, searchParams.value)
    works.value = response.data || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

/** 同步当前分页信息到 URL query（replace 避免历史记录堆积） */
function syncQueryToUrl(): void {
  router.replace({
    query: {
      ...route.query,
      page: page.value,
      pageSize: pageSize.value,
    },
  })
}

/** 切换分页后滚动到列表顶部 */
function scrollToTop(): void {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function deleteWork(id: string): Promise<void> {
  let deleteFiles = false

  // 根据设置决定删除行为
  if (settingsStore.deleteFilesOption === 'always') {
    deleteFiles = true
  } else if (settingsStore.deleteFilesOption === 'never') {
    deleteFiles = false
  } else {
    // ask 模式:询问用户
    try {
      // 先询问是否删除文件
      await ElMessageBox.confirm(
        '删除时是否同时删除下载的文件资源?',
        '删除选项',
        {
          confirmButtonText: '删除文件',
          cancelButtonText: '仅删除数据',
          distinguishCancelAndClose: true,
        }
      )

      deleteFiles = true
    } catch (action) {
      // 点击"仅删除数据"按钮
      if (action === 'cancel') {
        deleteFiles = false
      } else {
        // 点击关闭按钮,取消删除
        return
      }
    }
  }

  // 确认删除
  try {
    await ElMessageBox.confirm(
      `确定删除该作品吗?${deleteFiles ? ' (将同时删除文件)' : ''}`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      }
    )
  } catch {
    return
  }

  try {
    await douyinApi.delete(id, deleteFiles)
    works.value = works.value.filter(w => w.作品ID !== id)
    total.value--
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

function goToDetail(id: string): void {
  router.push({
    path: `/detail/${id}`,
    query: {
      page: page.value,
      pageSize: pageSize.value,
    },
  })
}

function handleSearch(): void {
  page.value = 1
  syncQueryToUrl()
  loadWorks()
  scrollToTop()
}

function handleReset(): void {
  page.value = 1
  syncQueryToUrl()
  loadWorks()
  scrollToTop()
}

function handlePageChange(newPage: number): void {
  page.value = newPage
  syncQueryToUrl()
  loadWorks()
  scrollToTop()
}

function handleSizeChange(newSize: number): void {
  pageSize.value = newSize
  page.value = 1
  syncQueryToUrl()
  loadWorks()
  scrollToTop()
}

onMounted(() => {
  loadWorks()
})
</script>

<template>
  <div class="space-y-6">
    <TaskListHeader
      :total="total"
      :searchParams="searchParams"
      @update:searchParams="searchParams = $event"
      @search="handleSearch"
      @reset="handleReset"
    />

    <TaskTable
      v-if="settingsStore.viewMode === 'table'"
      :works="works"
      @viewDetail="goToDetail"
      @deleteWork="deleteWork"
    />

    <TaskWaterfall
      v-else
      :works="works"
      @viewDetail="goToDetail"
    />

    <!-- 分页组件 -->
    <PaginationBar
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[20, 50, 100]"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>