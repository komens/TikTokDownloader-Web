<script setup lang="ts">
import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { douyinApi } from '@/api'
import { ElMessage, ElIcon } from 'element-plus'
import {
  Download,
  Upload,
  FolderOpened,
  Loading,
} from '@element-plus/icons-vue'

const settingsStore = useSettingsStore()
const exportLoading = ref(false)
const importLoading = ref(false)
const importFileInput = ref<HTMLInputElement | null>(null)

async function handleExport(): Promise<void> {
  exportLoading.value = true
  try {
    const blob = await douyinApi.export()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `douyin-web-backup-${new Date().toISOString().slice(0, 10)}.zip`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

function handleImportClick(): void {
  importFileInput.value?.click()
}

async function handleImport(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importLoading.value = true
  try {
    await douyinApi.import(file)
    ElMessage.success('导入成功')
    target.value = ''
  } catch (error) {
    ElMessage.error('导入失败')
    target.value = ''
  } finally {
    importLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="bg-surface rounded-xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-text mb-4 flex items-center gap-2">
        <ElIcon class="w-5 h-5 text-primary"><Download /></ElIcon>
        删除设置
      </h2>
      <p class="text-text-secondary text-sm mb-4">配置删除作品时的文件处理方式。</p>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <input
            type="radio"
            id="delete-ask"
            name="delete-option"
            :checked="settingsStore.deleteFilesOption === 'ask'"
            @change="settingsStore.setDeleteFilesOption('ask')"
            class="w-4 h-4 text-primary"
          />
          <label for="delete-ask" class="text-sm text-text cursor-pointer">
            每次询问是否删除文件
          </label>
        </div>
        <div class="flex items-center gap-3">
          <input
            type="radio"
            id="delete-always"
            name="delete-option"
            :checked="settingsStore.deleteFilesOption === 'always'"
            @change="settingsStore.setDeleteFilesOption('always')"
            class="w-4 h-4 text-primary"
          />
          <label for="delete-always" class="text-sm text-text cursor-pointer">
            总是删除文件
          </label>
        </div>
        <div class="flex items-center gap-3">
          <input
            type="radio"
            id="delete-never"
            name="delete-option"
            :checked="settingsStore.deleteFilesOption === 'never'"
            @change="settingsStore.setDeleteFilesOption('never')"
            class="w-4 h-4 text-primary"
          />
          <label for="delete-never" class="text-sm text-text cursor-pointer">
            从不删除文件
          </label>
        </div>
      </div>
      <p class="text-text-muted text-xs mt-3">提示：此设置会保存到浏览器本地存储，刷新页面后仍然有效</p>
    </div>

    <div class="bg-surface rounded-xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-text mb-4 flex items-center gap-2">
        <ElIcon class="w-5 h-5 text-success"><Download /></ElIcon>
        数据导出
      </h2>
      <p class="text-text-secondary text-sm mb-4">将配置文件和数据库导出为 ZIP 文件，方便备份和迁移。</p>
      <button
        @click="handleExport"
        :disabled="exportLoading"
        class="px-4 py-2.5 bg-success/10 text-success font-medium rounded-lg hover:bg-success/20 transition-colors disabled:opacity-50 flex items-center gap-2"
      >
        <ElIcon :class="{ 'animate-spin': exportLoading }"><Loading v-if="exportLoading" /><Download v-else /></ElIcon>
        {{ exportLoading ? '导出中...' : '导出数据' }}
      </button>
    </div>

    <div class="bg-surface rounded-xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-text mb-4 flex items-center gap-2">
        <ElIcon class="w-5 h-5 text-info"><Upload /></ElIcon>
        数据导入
      </h2>
      <p class="text-text-secondary text-sm mb-4">导入之前导出的 ZIP 文件，恢复配置和数据。</p>
      <input
        ref="importFileInput"
        type="file"
        accept=".zip"
        class="hidden"
        @change="handleImport"
      />
      <button
        @click="handleImportClick"
        :disabled="importLoading"
        class="px-4 py-2.5 bg-info/10 text-info font-medium rounded-lg hover:bg-info/20 transition-colors disabled:opacity-50 flex items-center gap-2"
      >
        <ElIcon :class="{ 'animate-spin': importLoading }"><Loading v-if="importLoading" /><FolderOpened v-else /></ElIcon>
        {{ importLoading ? '导入中...' : '选择文件' }}
      </button>
    </div>
  </div>
</template>
