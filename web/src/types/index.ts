export interface FileAccessInfo {
  absolute_path: string
  relative_path: string
  url: string
  filename: string
  thumbnail_url?: string
}

export interface WorkData {
  收藏数量: string
  评论数量: string
  分享数量: string
  点赞数量: string
  作品标签: string
  作品ID: string
  作品链接: string
  作品标题: string
  作品描述: string
  作品类型: '图文' | '视频'
  发布时间: string
  最后更新时间: string
  作者昵称: string
  作者ID: string
  作者链接: string
  下载地址: (string | null)[]
  动图地址: (string | null)[]
  下载文件路径: string[]
  采集时间: string
  文件访问信息: FileAccessInfo[]
}

export interface ApiResponse<T> {
  message?: string
  data: T
  total?: number
  page?: number
  pageSize?: number
}

export type DownloadQueueStatus = 'pending' | 'downloading' | 'completed' | 'failed'

export interface DownloadQueueItem {
  id: string
  url: string
  status: DownloadQueueStatus
  addedAt: string
  result?: ApiResponse<WorkData>
  error?: string
}

export interface ListResponse extends ApiResponse<WorkData[]> {
  total: number
  page: number
  pageSize: number
}

export interface DownloadParams {
  url: string
}

export interface DownloadResponse extends ApiResponse<WorkData> {}

// 后端下载队列项类型
export interface QueueItem {
  work_id: string
  title: string
  author: string
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  added_at: number
  url: string
  error_message?: string
  real_work_id?: string
  completed_at?: number
}

// 队列响应类型
export interface QueueResponse {
  message: string
  count: number
  data: QueueItem[]
}
