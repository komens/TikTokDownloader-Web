import axios from 'axios'
import type { ApiResponse, WorkData, DownloadParams, DownloadResponse, ListResponse, QueueResponse } from '@/types'

const apiClient = axios.create({
  baseURL: '/',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

export const douyinApi = {
  download: async (params: DownloadParams): Promise<DownloadResponse> => {
    const response = await apiClient.post<DownloadResponse>('/douyin/download', params)
    return response.data
  },

  list: async (
    page: number = 1,
    pageSize: number = 20,
    searchParams?: {
      author_nickname?: string
      author_id?: string
      work_title?: string
      work_desc?: string
    }
  ): Promise<ListResponse> => {
    const response = await apiClient.get<ListResponse>('/douyin/list', {
      params: { page, pageSize, ...searchParams },
    })
    return response.data
  },

  detail: async (id: string): Promise<ApiResponse<WorkData>> => {
    const response = await apiClient.get<ApiResponse<WorkData>>(`/douyin/detail/${id}`)
    return response.data
  },

  delete: async (id: string, deleteFiles: boolean = false): Promise<ApiResponse<unknown>> => {
    const response = await apiClient.delete<ApiResponse<unknown>>(`/douyin/delete/${id}`, {
      params: { delete_files: deleteFiles }
    })
    return response.data
  },

  export: async (): Promise<Blob> => {
    const response = await apiClient.get('/douyin/export', {
      responseType: 'blob',
    })
    return response.data
  },

  import: async (file: File): Promise<ApiResponse<unknown>> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<ApiResponse<unknown>>('/douyin/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 下载队列相关接口
  getQueue: async (): Promise<QueueResponse> => {
    const response = await apiClient.get<QueueResponse>('/douyin/queue')
    return response.data
  },

  deleteFromQueue: async (workId: string): Promise<ApiResponse<{ success: boolean }>> => {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(`/douyin/queue/${workId}`)
    return response.data
  },
}

export default apiClient
