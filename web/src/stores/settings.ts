import { defineStore } from 'pinia'
import { ref } from 'vue'

const VIEW_MODE_KEY = 'douyin-view-mode'
const DELETE_FILES_OPTION_KEY = 'douyin-delete-files-option'

export type ViewMode = 'table' | 'waterfall'
export type DeleteFilesOption = 'ask' | 'always' | 'never'

export const useSettingsStore = defineStore('settings', () => {
  const viewMode = ref<ViewMode>((localStorage.getItem(VIEW_MODE_KEY) as ViewMode) || 'table')

  // 删除文件选项(localStorage存储)
  const deleteFilesOption = ref<DeleteFilesOption>(
    (localStorage.getItem(DELETE_FILES_OPTION_KEY) as DeleteFilesOption) || 'ask'
  )

  function setViewMode(mode: ViewMode): void {
    viewMode.value = mode
    localStorage.setItem(VIEW_MODE_KEY, mode)
  }

  function setDeleteFilesOption(option: DeleteFilesOption): void {
    deleteFilesOption.value = option
    localStorage.setItem(DELETE_FILES_OPTION_KEY, option)
  }

  return {
    viewMode,
    deleteFilesOption,
    setViewMode,
    setDeleteFilesOption,
  }
})
