import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { QueueItem } from '@/types'
import { douyinApi } from '@/api'

export const useDownloadStore = defineStore('download', () => {
  const queue = ref<QueueItem[]>([])
  const isPolling = ref(false)
  let pollTimer: number | undefined

  const pendingCount = computed(() => queue.value.filter(item => item.status === 'pending').length)
  const downloadingCount = computed(() => queue.value.filter(item => item.status === 'downloading').length)
  const completedCount = computed(() => queue.value.filter(item => item.status === 'completed').length)
  const failedCount = computed(() => queue.value.filter(item => item.status === 'failed').length)

  async function fetchQueue(): Promise<void> {
    try {
      const response = await douyinApi.getQueue()
      queue.value = response.data || []
    } catch (error) {
      console.error('Failed to fetch queue:', error)
    }
  }

  function startPolling(): void {
    if (isPolling.value) return
    isPolling.value = true
    void fetchQueue()
    pollTimer = window.setInterval(() => {
      void fetchQueue()
    }, 3000)
  }

  function stopPolling(): void {
    isPolling.value = false
    if (pollTimer !== undefined) {
      clearInterval(pollTimer)
      pollTimer = undefined
    }
  }

  async function addItem(url: string): Promise<boolean> {
    if (!url.trim()) return false
    try {
      await douyinApi.download({ url: url.trim() })
      await fetchQueue()
      return true
    } catch (error) {
      console.error('Failed to start download:', error)
      return false
    }
  }

  async function removeItem(workId: string): Promise<void> {
    try {
      await douyinApi.deleteFromQueue(workId)
      await fetchQueue()
    } catch (error) {
      console.error('Failed to remove item from queue:', error)
    }
  }

  return {
    queue,
    isPolling,
    pendingCount,
    downloadingCount,
    completedCount,
    failedCount,
    fetchQueue,
    startPolling,
    stopPolling,
    addItem,
    removeItem,
  }
})