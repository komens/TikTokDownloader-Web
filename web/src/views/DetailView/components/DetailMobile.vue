<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { douyinApi } from '@/api'
import type { WorkData } from '@/types'
import { getMediaUrl, getMediaCount, isVideoType, formatDate, getTags, getFileAccessInfoList } from '@/utils'
import { ElMessage, ElIcon } from 'element-plus'
import {
  ArrowLeft,
  Star,
  StarFilled,
  Message,
  Share,
  PriceTag,
  Document,
  Download,
  CopyDocument,
  User,
  MoreFilled,
  Close,
  Loading,
} from '@element-plus/icons-vue'
import VideoPlayer from './VideoPlayer.vue'

const props = defineProps<{
  works: WorkData[]
  currentId: string
  initialPage: number
  pageSize: number
}>()

const emit = defineEmits<{
  goBack: []
}>()

const router = useRouter()

// 本地维护的作品列表（支持分页追加）
const localWorks = ref<WorkData[]>([...props.works])
// 当前作品索引
const currentIndex = ref(0)
// 当前作品的图片轮播索引
const mediaIndex = ref(0)
// 详情抽屉
const showDrawer = ref(false)
// 滚动容器
const scrollContainer = ref<HTMLElement | null>(null)

// 图片轮播：水平滑动偏移量（px）
const mediaOffset = ref(0)
// 图片轮播：是否正在拖动
const isMediaDragging = ref(false)
// 图片滑动手势起点
let mediaTouchStartX = 0
let mediaTouchStartY = 0

// 虚拟窗口：只渲染当前±2 共 5 项（边界不足时自动收缩）
const VISIBLE_RANGE = 2
const visibleStart = ref(0)
const visibleEnd = ref(0)
const visibleWorks = computed(() => {
  const total = localWorks.value.length
  if (total === 0) {
    visibleStart.value = 0
    visibleEnd.value = 0
    return []
  }
  const start = Math.max(0, currentIndex.value - VISIBLE_RANGE)
  const end = Math.min(total, currentIndex.value + VISIBLE_RANGE + 1)
  visibleStart.value = start
  visibleEnd.value = end
  return localWorks.value.slice(start, end).map((work, i) => ({
    work,
    // 在 localWorks 中的真实索引
    realIndex: start + i,
  }))
})

// 分页状态
const currentPage = ref(props.initialPage)
const pageSize = ref(props.pageSize)
const hasMore = ref(true)
const hasPrev = ref(props.initialPage > 1)
const loadingMore = ref(false)
const loadingPrev = ref(false)
// 防止 URL 更新触发重复定位
let isUrlUpdating = false

const currentWork = computed(() => localWorks.value[currentIndex.value] || null)

// 初始化当前索引：找到目标作品位置
function initCurrentIndex() {
  const idx = localWorks.value.findIndex(w => w.作品ID === props.currentId)
  currentIndex.value = idx >= 0 ? idx : 0
  mediaIndex.value = 0
}

// 图片轮播：手势开始
function onMediaTouchStart(e: TouchEvent) {
  if (!currentWork.value || getMediaCount(currentWork.value) <= 1) return
  const touch = e.touches[0]
  mediaTouchStartX = touch.clientX
  mediaTouchStartY = touch.clientY
  isMediaDragging.value = true
}

// 图片轮播：手势移动
function onMediaTouchMove(e: TouchEvent) {
  if (!isMediaDragging.value || !currentWork.value) return
  const touch = e.touches[0]
  const dx = touch.clientX - mediaTouchStartX
  const dy = touch.clientY - mediaTouchStartY
  // 水平滑动距离明显大于垂直时，认定为图片切换手势，阻止垂直滚动
  if (Math.abs(dx) > Math.abs(dy)) {
    // 到边界时增加阻尼
    const count = getMediaCount(currentWork.value)
    let realDx = dx
    if ((mediaIndex.value === 0 && dx > 0) || (mediaIndex.value === count - 1 && dx < 0)) {
      realDx = dx * 0.3
    }
    mediaOffset.value = realDx
  }
}

// 图片轮播：手势结束
function onMediaTouchEnd() {
  if (!isMediaDragging.value || !currentWork.value) {
    isMediaDragging.value = false
    return
  }
  isMediaDragging.value = false
  const count = getMediaCount(currentWork.value)
  const threshold = window.innerWidth * 0.2
  if (mediaOffset.value < -threshold && mediaIndex.value < count - 1) {
    mediaIndex.value++
  } else if (mediaOffset.value > threshold && mediaIndex.value > 0) {
    mediaIndex.value--
  }
  // 回弹：偏移量归零，CSS transition 负责动画
  mediaOffset.value = 0
}

// 图片轮播：点击指示点跳转
function goToMedia(idx: number) {
  mediaIndex.value = idx
}

/**
 * 瞬间定位到当前作品（无动画），避免刷新或进入时的滚动动画
 */
function jumpToCurrentSlide() {
  nextTick(() => {
    if (scrollContainer.value) {
      const slideHeight = window.innerHeight
      scrollContainer.value.scrollTo({
        top: currentIndex.value * slideHeight,
        behavior: 'auto',
      })
    }
  })
}

// 更新 URL 中的 id 和 page（replace 不产生历史记录）
function updateUrl() {
  if (isUrlUpdating) return
  const work = currentWork.value
  if (!work) return
  isUrlUpdating = true
  router.replace({
    path: `/detail/${work.作品ID}`,
    query: {
      page: currentPage.value,
      pageSize: pageSize.value,
    },
  })
  nextTick(() => { isUrlUpdating = false })
}

// 加载下一页
async function loadNextPage() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const response = await douyinApi.list(currentPage.value + 1, pageSize.value)
    const newWorks = response.data || []
    if (newWorks.length > 0) {
      localWorks.value.push(...newWorks)
      currentPage.value += 1
      hasMore.value = newWorks.length >= pageSize.value
    } else {
      hasMore.value = false
    }
  } catch {
    ElMessage.warning('加载更多失败')
  } finally {
    loadingMore.value = false
  }
}

// 加载上一页
async function loadPrevPage() {
  if (loadingPrev.value || !hasPrev.value) return
  loadingPrev.value = true
  const prevPage = currentPage.value - 1
  if (prevPage < 1) {
    hasPrev.value = false
    loadingPrev.value = false
    return
  }
  try {
    const response = await douyinApi.list(prevPage, pageSize.value)
    const newWorks = response.data || []
    if (newWorks.length > 0) {
      const prevCount = newWorks.length
      // 在顶部插入旧数据
      localWorks.value.unshift(...newWorks)
      // 修正索引：原本定位的项现在下移了 prevCount
      currentIndex.value += prevCount
      currentPage.value = prevPage
      hasPrev.value = prevPage > 1
      // 保持滚动位置：插入数据后立即把滚动位置下移 prevCount 屏
      nextTick(() => {
        if (scrollContainer.value) {
          const slideHeight = window.innerHeight
          scrollContainer.value.scrollTop += prevCount * slideHeight
        }
      })
    } else {
      hasPrev.value = false
    }
  } catch {
    ElMessage.warning('加载上一页失败')
  } finally {
    loadingPrev.value = false
  }
}

// 下载
async function downloadAll() {
  if (!currentWork.value) return
  const fileList = getFileAccessInfoList(currentWork.value)
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

async function copyLink() {
  if (!currentWork.value?.作品链接) {
    ElMessage.warning('没有作品链接')
    return
  }
  try {
    await navigator.clipboard.writeText(currentWork.value.作品链接)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 监听 props.works 变化（父组件初次加载完成）
watch(() => props.works, (newWorks) => {
  if (localWorks.value.length === 0 && newWorks.length > 0) {
    localWorks.value = [...newWorks]
    initCurrentIndex()
    jumpToCurrentSlide()
  }
}, { immediate: true })

// 监听 currentId 变化（外部路由跳转）
watch(() => props.currentId, () => {
  if (isUrlUpdating) return
  const idx = localWorks.value.findIndex(w => w.作品ID === props.currentId)
  if (idx >= 0 && idx !== currentIndex.value) {
    currentIndex.value = idx
    jumpToCurrentSlide()
  }
})

// 监听 currentIndex，重置 mediaIndex 并同步 URL
watch(currentIndex, () => {
  mediaIndex.value = 0
  updateUrl()
})

// 滚动处理：同步索引 + 触发分页加载
let scrollTimer: ReturnType<typeof setTimeout> | null = null
function onScroll() {
  if (scrollTimer) clearTimeout(scrollTimer)
  scrollTimer = setTimeout(() => {
    if (!scrollContainer.value) return
    const slideHeight = window.innerHeight
    const newIndex = Math.round(scrollContainer.value.scrollTop / slideHeight)
    if (newIndex !== currentIndex.value && newIndex >= 0 && newIndex < localWorks.value.length) {
      currentIndex.value = newIndex
      mediaIndex.value = 0
    }
    // 接近底部：加载下一页
    const distanceToBottom = scrollContainer.value.scrollHeight - scrollContainer.value.scrollTop - scrollContainer.value.clientHeight
    if (distanceToBottom < slideHeight * 2 && !loadingMore.value && hasMore.value) {
      loadNextPage()
    }
    // 接近顶部：加载上一页
    if (scrollContainer.value.scrollTop < slideHeight && !loadingPrev.value && hasPrev.value) {
      loadPrevPage()
    }
  }, 100)
}

onMounted(() => {
  initCurrentIndex()
  document.body.style.overflow = 'hidden'
  jumpToCurrentSlide()
})

onUnmounted(() => {
  document.body.style.overflow = ''
  if (scrollTimer) clearTimeout(scrollTimer)
})
</script>

<template>
  <div class="mobile-detail">
    <!-- 顶部导航栏 -->
    <div class="mobile-detail__header">
      <button @click="emit('goBack')" class="mobile-detail__back">
        <ElIcon :size="20"><ArrowLeft /></ElIcon>
      </button>
      <div class="mobile-detail__counter">
        {{ currentIndex + 1 }} / {{ localWorks.length }}
      </div>
    </div>

    <!-- 全屏滑动区域 -->
    <div
      ref="scrollContainer"
      class="mobile-detail__slides"
      @scroll="onScroll"
    >
      <!-- 上方占位：撑起 visibleStart 屏，保持 scrollTop 计算基于全局索引 -->
      <div
        v-if="visibleStart > 0"
        class="mobile-detail__placeholder"
        :style="{ height: visibleStart * 100 + 'dvh' }"
      >
        <div v-if="loadingPrev" class="mobile-detail__loading">
          <ElIcon class="animate-spin"><Loading /></ElIcon>
        </div>
      </div>

      <div
        v-for="item in visibleWorks"
        :key="item.work.作品ID"
        class="mobile-detail__slide"
      >
        <!-- 媒体内容 -->
        <div class="mobile-detail__media">
          <!-- 视频 -->
          <div v-if="isVideoType(item.work)" class="mobile-detail__video">
            <!-- 当前项：渲染播放器并自动播放 -->
            <VideoPlayer
              v-if="item.realIndex === currentIndex"
              :url="getMediaUrl(item.work, 0)"
              :poster="item.work.文件访问信息?.[0]?.thumbnail_url || ''"
              :loop="true"
              autoplay
              muted
            />
            <!-- 非当前项：封面图占位 -->
            <img
              v-else
              :src="item.work.文件访问信息?.[0]?.thumbnail_url || ''"
              :alt="item.work.作品标题 || '视频封面'"
              class="mobile-detail__poster"
            />
          </div>

          <!-- 图片：支持左右滑动手势切换 -->
          <div
            v-else
            class="mobile-detail__image-wrapper"
            @touchstart.passive="onMediaTouchStart"
            @touchmove.passive="onMediaTouchMove"
            @touchend="onMediaTouchEnd"
          >
            <div
              v-if="item.realIndex === currentIndex"
              class="mobile-detail__image-track"
              :class="{ 'mobile-detail__image-track--dragging': isMediaDragging }"
              :style="{ transform: `translateX(calc(${-mediaIndex * 100}% + ${mediaOffset}px))` }"
            >
              <img
                v-for="(_, mi) in getMediaCount(item.work)"
                :key="mi"
                :src="getMediaUrl(item.work, mi)"
                :alt="item.work.作品标题 || '作品图片'"
                class="mobile-detail__image"
              />
            </div>
            <img
              v-else
              :src="getMediaUrl(item.work, 0)"
              :alt="item.work.作品标题 || '作品图片'"
              class="mobile-detail__image"
            />

            <!-- 图片指示点（仅当前项显示） -->
            <template v-if="item.realIndex === currentIndex && getMediaCount(item.work) > 1">
              <div class="mobile-detail__dots">
                <span
                  v-for="(_, di) in getMediaCount(item.work)"
                  :key="di"
                  class="mobile-detail__dot"
                  :class="{ 'mobile-detail__dot--active': di === mediaIndex }"
                  @click.stop="goToMedia(di)"
                ></span>
              </div>

              <!-- 图片计数 -->
              <div class="mobile-detail__media-count">
                {{ mediaIndex + 1 }} / {{ getMediaCount(item.work) }}
              </div>
            </template>
          </div>
        </div>

        <!-- 底部信息叠加层（仅当前项显示） -->
        <div v-if="item.realIndex === currentIndex" class="mobile-detail__info-overlay">
          <div class="mobile-detail__gradient"></div>
          <div class="mobile-detail__info-content">
            <div class="mobile-detail__author">
              <div class="mobile-detail__avatar">
                <ElIcon :size="16"><User /></ElIcon>
              </div>
              <span class="mobile-detail__author-name">{{ item.work.作者昵称 || '未知作者' }}</span>
            </div>
            <h2 class="mobile-detail__title">{{ item.work.作品标题 || '未知标题' }}</h2>
            <div class="mobile-detail__stats">
              <div class="mobile-detail__stat">
                <ElIcon :size="14"><StarFilled /></ElIcon>
                <span>{{ item.work.点赞数量 || '0' }}</span>
              </div>
              <div class="mobile-detail__stat">
                <ElIcon :size="14"><Star /></ElIcon>
                <span>{{ item.work.收藏数量 || '0' }}</span>
              </div>
              <div class="mobile-detail__stat">
                <ElIcon :size="14"><Message /></ElIcon>
                <span>{{ item.work.评论数量 || '0' }}</span>
              </div>
              <div class="mobile-detail__stat">
                <ElIcon :size="14"><Share /></ElIcon>
                <span>{{ item.work.分享数量 || '0' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧操作栏（仅当前项显示） -->
        <div v-if="item.realIndex === currentIndex" class="mobile-detail__actions">
          <button class="mobile-detail__action-btn" @click="downloadAll">
            <div class="mobile-detail__action-icon">
              <ElIcon :size="20"><Download /></ElIcon>
            </div>
            <span>下载</span>
          </button>
          <button class="mobile-detail__action-btn" @click="copyLink">
            <div class="mobile-detail__action-icon">
              <ElIcon :size="20"><CopyDocument /></ElIcon>
            </div>
            <span>链接</span>
          </button>
          <button class="mobile-detail__action-btn" @click="showDrawer = true">
            <div class="mobile-detail__action-icon">
              <ElIcon :size="20"><MoreFilled /></ElIcon>
            </div>
            <span>更多</span>
          </button>
        </div>
      </div>

      <!-- 下方占位：撑起剩余屏数，保持 scrollTop 计算正确 -->
      <div
        v-if="visibleEnd < localWorks.length"
        class="mobile-detail__placeholder"
        :style="{ height: (localWorks.length - visibleEnd) * 100 + 'dvh' }"
      >
        <div v-if="loadingMore" class="mobile-detail__loading">
          <ElIcon class="animate-spin"><Loading /></ElIcon>
        </div>
      </div>
      <!-- 没有更多时的提示（仅当已加载全部且在最后一项） -->
      <div v-else-if="!hasMore && !loadingMore" class="mobile-detail__loading mobile-detail__loading--bottom">
        <span class="mobile-detail__loading-text">没有更多了</span>
      </div>
    </div>

    <!-- 详情抽屉 -->
    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="showDrawer" class="mobile-drawer" @click.self="showDrawer = false">
          <div class="mobile-drawer__content">
            <div class="mobile-drawer__header">
              <span class="mobile-drawer__title">作品详情</span>
              <button class="mobile-drawer__close" @click="showDrawer = false">
                <ElIcon :size="18"><Close /></ElIcon>
              </button>
            </div>

            <div v-if="currentWork" class="mobile-drawer__body">
              <h3 class="mobile-drawer__work-title">{{ currentWork.作品标题 || '未知标题' }}</h3>

              <div class="mobile-drawer__author">
                <div class="mobile-drawer__avatar">
                  <ElIcon :size="18"><User /></ElIcon>
                </div>
                <div>
                  <div class="mobile-drawer__author-name">{{ currentWork.作者昵称 || '未知作者' }}</div>
                  <div class="mobile-drawer__date">{{ formatDate(currentWork.发布时间) }}</div>
                </div>
              </div>

              <div class="mobile-drawer__stats">
                <div class="mobile-drawer__stat">
                  <ElIcon :size="16" class="text-error"><StarFilled /></ElIcon>
                  <span class="mobile-drawer__stat-label">点赞</span>
                  <span class="mobile-drawer__stat-value">{{ currentWork.点赞数量 || '0' }}</span>
                </div>
                <div class="mobile-drawer__stat">
                  <ElIcon :size="16" class="text-warning"><Star /></ElIcon>
                  <span class="mobile-drawer__stat-label">收藏</span>
                  <span class="mobile-drawer__stat-value">{{ currentWork.收藏数量 || '0' }}</span>
                </div>
                <div class="mobile-drawer__stat">
                  <ElIcon :size="16"><Message /></ElIcon>
                  <span class="mobile-drawer__stat-label">评论</span>
                  <span class="mobile-drawer__stat-value">{{ currentWork.评论数量 || '0' }}</span>
                </div>
                <div class="mobile-drawer__stat">
                  <ElIcon :size="16"><Share /></ElIcon>
                  <span class="mobile-drawer__stat-label">分享</span>
                  <span class="mobile-drawer__stat-value">{{ currentWork.分享数量 || '0' }}</span>
                </div>
              </div>

              <div v-if="getTags(currentWork).length > 0" class="mobile-drawer__section">
                <div class="mobile-drawer__section-title">
                  <ElIcon :size="14"><PriceTag /></ElIcon>
                  标签
                </div>
                <div class="mobile-drawer__tags">
                  <span v-for="tag in getTags(currentWork)" :key="tag" class="mobile-drawer__tag">
                    {{ tag }}
                  </span>
                </div>
              </div>

              <div v-if="currentWork.作品描述" class="mobile-drawer__section">
                <div class="mobile-drawer__section-title">
                  <ElIcon :size="14"><Document /></ElIcon>
                  作品描述
                </div>
                <p class="mobile-drawer__desc">{{ currentWork.作品描述 }}</p>
              </div>

              <div class="mobile-drawer__buttons">
                <button @click="downloadAll" class="mobile-drawer__btn mobile-drawer__btn--primary">
                  <ElIcon><Download /></ElIcon>
                  下载全部
                </button>
                <button @click="copyLink" class="mobile-drawer__btn mobile-drawer__btn--secondary">
                  <ElIcon><CopyDocument /></ElIcon>
                  复制链接
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.mobile-detail {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: #000;
}

/* 顶部导航 */
.mobile-detail__header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 12px) + 8px) 16px 12px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.5) 0%, transparent 100%);
  pointer-events: none;
}

.mobile-detail__header > * {
  pointer-events: auto;
}

.mobile-detail__back {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border: none;
  border-radius: 50%;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  cursor: pointer;
  transition: background 0.2s;
}

.mobile-detail__back:active {
  background: rgba(255, 255, 255, 0.25);
}

.mobile-detail__counter {
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 500;
  padding: 4px 14px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 20px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  letter-spacing: 0.5px;
}

/* 全屏滑动区域 */
.mobile-detail__slides {
  width: 100%;
  height: 100%;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.mobile-detail__slides::-webkit-scrollbar {
  display: none;
}

.mobile-detail__slide {
  position: relative;
  width: 100%;
  height: 100dvh;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #000;
}

/* 虚拟滚动占位：撑起未渲染 slide 的高度 */
.mobile-detail__placeholder {
  width: 100%;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 加载提示 */
.mobile-detail__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 60px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  background: #000;
}

.mobile-detail__loading--bottom {
  scroll-snap-align: none;
}

.mobile-detail__loading-text {
  font-size: 12px;
  opacity: 0.5;
}

/* 媒体 */
.mobile-detail__media {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-detail__video {
  width: 100%;
  height: 100%;
}

.mobile-detail__poster {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.mobile-detail__image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图片轮播轨道：水平排列所有图片，通过 translateX 切换 */
.mobile-detail__image-track {
  display: flex;
  width: 100%;
  height: 100%;
  /* 拖动时关闭过渡，松手时启用过渡实现回弹/切换动画 */
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
  will-change: transform;
}

.mobile-detail__image-track--dragging {
  transition: none;
}

.mobile-detail__image {
  flex-shrink: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: none;
}

/* 图片指示点 */
.mobile-detail__dots {
  position: absolute;
  bottom: 170px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 5px;
  z-index: 5;
}

.mobile-detail__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
  cursor: pointer;
}

.mobile-detail__dot--active {
  background: #fff;
  width: 14px;
  border-radius: 2.5px;
}

/* 图片计数 */
.mobile-detail__media-count {
  position: absolute;
  top: 56px;
  right: 12px;
  padding: 2px 10px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.9);
  font-size: 11px;
  border-radius: 10px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 5;
}

/* 底部信息叠加层 */
.mobile-detail__info-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 5;
  pointer-events: none;
}

.mobile-detail__gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 280px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.65) 0%, rgba(0, 0, 0, 0.2) 50%, transparent 100%);
  pointer-events: none;
}

.mobile-detail__info-content {
  position: relative;
  padding: 0 16px 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
}

.mobile-detail__author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  pointer-events: auto;
}

.mobile-detail__avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.mobile-detail__author-name {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.mobile-detail__title {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.mobile-detail__stats {
  display: flex;
  gap: 14px;
  pointer-events: auto;
}

.mobile-detail__stat {
  display: flex;
  align-items: center;
  gap: 3px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 右侧操作栏 */
.mobile-detail__actions {
  position: absolute;
  right: 6px;
  /* 视频时上移避开底部播放器控制栏（约 44px） */
  bottom: 140px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: center;
}

.mobile-detail__action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  color: #fff;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 10px;
  padding: 2px;
  transition: transform 0.15s;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.mobile-detail__action-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: background 0.2s;
  margin-bottom: 2px;
}

.mobile-detail__action-btn:active .mobile-detail__action-icon {
  background: rgba(255, 255, 255, 0.25);
}

/* ===== 抽屉 ===== */
.mobile-drawer {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.mobile-drawer__content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 80vh;
  background: #fff;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

/* 抽屉把手 */
.mobile-drawer__content::before {
  content: '';
  display: block;
  width: 36px;
  height: 4px;
  background: #ddd;
  border-radius: 2px;
  margin: 10px auto 0;
  flex-shrink: 0;
}

.mobile-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px 12px;
  flex-shrink: 0;
}

.mobile-drawer__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.mobile-drawer__close {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f2f2;
  border: none;
  border-radius: 50%;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.mobile-drawer__close:active {
  background: #e6e6e6;
}

.mobile-drawer__body {
  padding: 0 20px 20px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-drawer__work-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  line-height: 1.5;
}

.mobile-drawer__author {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.mobile-drawer__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.mobile-drawer__author-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
}

.mobile-drawer__date {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* 抽屉统计 */
.mobile-drawer__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.mobile-drawer__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 4px;
  background: #fafafa;
  border-radius: 12px;
}

.mobile-drawer__stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.mobile-drawer__stat-label {
  font-size: 11px;
  color: var(--color-text-muted);
}

/* 抽屉分区 */
.mobile-drawer__section {
  margin-bottom: 20px;
}

.mobile-drawer__section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

.mobile-drawer__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mobile-drawer__tag {
  padding: 5px 14px;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  border-radius: 14px;
  font-weight: 500;
}

.mobile-drawer__desc {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
}

/* 抽屉按钮 */
.mobile-drawer__buttons {
  display: flex;
  gap: 12px;
  padding-top: 12px;
}

.mobile-drawer__btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.mobile-drawer__btn:active {
  opacity: 0.8;
}

.mobile-drawer__btn--primary {
  background: var(--color-primary);
  color: #fff;
}

.mobile-drawer__btn--secondary {
  background: #f5f5f5;
  color: var(--color-text);
}

/* 抽屉过渡动画 */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease;
}

.drawer-enter-active .mobile-drawer__content,
.drawer-leave-active .mobile-drawer__content {
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .mobile-drawer__content,
.drawer-leave-to .mobile-drawer__content {
  transform: translateY(100%);
}
</style>
