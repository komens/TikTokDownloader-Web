<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import Player from 'xgplayer'
import 'xgplayer/dist/index.min.css'

const props = withDefaults(defineProps<{
  url: string
  poster?: string
  autoplay?: boolean
  loop?: boolean
  muted?: boolean
  /** 视频填充模式：contain 居中自适应保持比例，cover 铺满裁切 */
  videoFillMode?: 'contain' | 'cover'
}>(), {
  autoplay: false,
  loop: false,
  muted: false,
  videoFillMode: 'contain',
})

const emit = defineEmits<{
  play: []
  pause: []
  ended: []
}>()

const containerRef = ref<HTMLElement>()
let player: Player | null = null
let resizeObserver: MutationObserver | null = null

/**
 * xgplayer 会通过 resizeObserver 持续在根元素上写入内联像素 width/height
 * 这里用 MutationObserver 监听并强制清除，确保容器始终铺满父元素
 */
function startStyleGuard() {
  const el = containerRef.value
  if (!el) return
  stopStyleGuard()
  const forceFullSize = () => {
    if (!containerRef.value) return
    const s = containerRef.value.style
    if (s.width !== '100%' || s.height !== '100%') {
      s.width = '100%'
      s.height = '100%'
    }
  }
  // 立即执行一次
  forceFullSize()
  resizeObserver = new MutationObserver(() => forceFullSize())
  resizeObserver.observe(el, { attributes: true, attributeFilter: ['style'] })
}

function stopStyleGuard() {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
}

function initPlayer() {
  if (!containerRef.value || !props.url) return

  destroyPlayer()

  nextTick(() => {
    if (!containerRef.value) return

    player = new Player({
      el: containerRef.value,
      url: props.url,
      poster: props.poster || '',
      autoplay: props.autoplay,
      loop: props.loop,
      muted: props.muted,
      // 显式指定容器尺寸为 100%，配合 fitVideoSize: 'fixed' 锁定尺寸
      width: '100%',
      height: '100%',
      fluid: false,
      fitVideoSize: 'fixed',
      videoFillMode: props.videoFillMode,
      playsinline: true,
      whitelist: [''],
      videoInit: true,
      lang: 'zh-cn',
      closeVideoClick: false,
      closeVideoDblclick: false,
      closeVideoTouch: false,
      ignores: [
        'playbackrate',
        'screenshot',
        'pip',
        'miniscreen',
        'replay',
        'volume',
        'definition',
        'download',
        'cssfullscreen',
        'enter',
      ],
      keyShortcut: false,
    })

    // 启动样式守卫，持续覆盖 xgplayer 写入的内联像素尺寸
    startStyleGuard()

    player.on('play', () => emit('play'))
    player.on('pause', () => emit('pause'))
    player.on('ended', () => emit('ended'))
  })
}

function destroyPlayer() {
  stopStyleGuard()
  if (player) {
    player.destroy()
    player = null
  }
}

watch(() => props.url, () => {
  initPlayer()
})

onMounted(() => {
  initPlayer()
})

onUnmounted(() => {
  destroyPlayer()
})
</script>

<template>
  <div class="video-player">
    <div ref="containerRef" class="video-player__el"></div>
  </div>
</template>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  background: #000;
}

/* containerRef 元素本身会被 xgplayer 加上 .xgplayer class，
   直接匹配该元素而非后代元素，用 !important 覆盖内联像素样式 */
.video-player__el {
  width: 100% !important;
  height: 100% !important;
  background: #000;
}

.video-player__el :deep(.xgplayer-video) {
  width: 100% !important;
  height: 100% !important;
}

.video-player__el :deep(.xgplayer-controls) {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.5), transparent) !important;
  height: 44px !important;
  padding: 0 8px !important;
}

.video-player__el :deep(.xgplayer-controls .xgplayer-time) {
  font-size: 12px !important;
  opacity: 0.85;
}

.video-player__el :deep(.xgplayer-progress) {
  margin: 0 8px !important;
}

.video-player__el :deep(.xgplayer-fullscreen) {
  order: 99 !important;
}

.video-player__el :deep(.xgplayer-poster) {
  background-size: cover !important;
  background-position: center !important;
}
</style>
