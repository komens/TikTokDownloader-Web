<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { ElIcon, ElButton, ElInput } from 'element-plus'
import {
  Grid,
  List,
  Search,
  ArrowDown,
  RefreshLeft,
} from '@element-plus/icons-vue'

const settingsStore = useSettingsStore()

interface SearchParams {
  author_nickname: string
  author_id: string
  work_title: string
  work_desc: string
}

const props = defineProps<{
  total: number
  searchParams: SearchParams
}>()

const emit = defineEmits<{
  'update:searchParams': [value: SearchParams]
  'search': []
  'reset': []
}>()

const isMobile = ref(window.innerWidth < 768)
const showAllFilters = ref(false)

const localSearchParams = ref<SearchParams>({
  author_nickname: props.searchParams.author_nickname,
  author_id: props.searchParams.author_id,
  work_title: props.searchParams.work_title,
  work_desc: props.searchParams.work_desc,
})

const hasFilters = computed(() => {
  return Object.values(localSearchParams.value).some(v => v.trim() !== '')
})

const activeFieldCount = computed(() => {
  return Object.values(localSearchParams.value).filter(v => v.trim() !== '').length
})

function handleSearch() {
  emit('update:searchParams', { ...localSearchParams.value })
  emit('search')
}

function handleReset() {
  localSearchParams.value = {
    author_nickname: '',
    author_id: '',
    work_title: '',
    work_desc: '',
  }
  emit('update:searchParams', { ...localSearchParams.value })
  emit('reset')
}

function toggleFilters() {
  showAllFilters.value = !showAllFilters.value
}

// 监听窗口大小变化
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 768
})
</script>

<template>
  <div class="search-container">
    <!-- 搜索主体 -->
    <div class="search-card">
      <!-- 搜索表单区域 -->
      <div class="search-form">
        <!-- 桌面端布局 -->
        <div v-if="!isMobile" class="desktop-layout">
          <div class="search-fields-grid">
            <div class="search-field-item">
              <ElInput
                v-model="localSearchParams.author_nickname"
                placeholder="作者昵称"
                clearable
                class="custom-input"
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <ElIcon class="input-icon"><Search /></ElIcon>
                </template>
              </ElInput>
            </div>
            
            <div class="search-field-item">
              <ElInput
                v-model="localSearchParams.author_id"
                placeholder="作者ID"
                clearable
                class="custom-input"
                @keyup.enter="handleSearch"
              />
            </div>
            
            <div class="search-field-item">
              <ElInput
                v-model="localSearchParams.work_title"
                placeholder="作品标题"
                clearable
                class="custom-input"
                @keyup.enter="handleSearch"
              />
            </div>
            
            <div class="search-field-item">
              <ElInput
                v-model="localSearchParams.work_desc"
                placeholder="作品描述"
                clearable
                class="custom-input"
                @keyup.enter="handleSearch"
              />
            </div>
          </div>
          
          <div class="action-buttons">
            <ElButton
              type="primary"
              class="search-button"
              @click="handleSearch"
            >
              <ElIcon class="button-icon"><Search /></ElIcon>
              <span>搜索</span>
            </ElButton>
            
            <ElButton
              v-if="hasFilters"
              class="reset-button"
              @click="handleReset"
            >
              <ElIcon class="button-icon"><RefreshLeft /></ElIcon>
              <span>重置</span>
            </ElButton>
          </div>
        </div>
        
        <!-- 移动端布局 -->
        <div v-else class="mobile-layout">
          <div class="mobile-search-main">
            <ElInput
              v-model="localSearchParams.author_nickname"
              placeholder="搜索作者昵称..."
              clearable
              class="custom-input mobile-input"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <ElIcon class="input-icon"><Search /></ElIcon>
              </template>
            </ElInput>
            
            <ElButton
              type="primary"
              class="search-button mobile-search-btn"
              @click="handleSearch"
            >
              <ElIcon><Search /></ElIcon>
            </ElButton>
          </div>
          
          <!-- 移动端展开的搜索条件 -->
          <transition name="expand">
            <div v-show="showAllFilters" class="mobile-filters-expand">
              <div class="mobile-filter-item">
                <ElInput
                  v-model="localSearchParams.author_id"
                  placeholder="作者ID"
                  clearable
                  class="custom-input"
                  @keyup.enter="handleSearch"
                />
              </div>
              <div class="mobile-filter-item">
                <ElInput
                  v-model="localSearchParams.work_title"
                  placeholder="作品标题"
                  clearable
                  class="custom-input"
                  @keyup.enter="handleSearch"
                />
              </div>
              <div class="mobile-filter-item">
                <ElInput
                  v-model="localSearchParams.work_desc"
                  placeholder="作品描述"
                  clearable
                  class="custom-input"
                  @keyup.enter="handleSearch"
                />
              </div>
              
              <div class="mobile-actions">
                <ElButton
                  v-if="hasFilters"
                  size="small"
                  class="reset-button"
                  @click="handleReset"
                >
                  <ElIcon class="button-icon"><RefreshLeft /></ElIcon>
                  重置
                </ElButton>
              </div>
            </div>
          </transition>
          
          <!-- 移动端展开/折叠按钮 -->
          <div class="mobile-toggle-wrapper">
            <button
              class="mobile-toggle-btn"
              @click="toggleFilters"
            >
              <span>{{ showAllFilters ? '收起筛选' : '更多筛选' }}</span>
              <ElIcon class="toggle-icon" :class="{ rotated: showAllFilters }">
                <ArrowDown />
              </ElIcon>
              <span v-if="activeFieldCount > 0" class="active-count">{{ activeFieldCount }}</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 分隔线 -->
      <div class="divider-line"></div>
      
      <!-- 底部工具栏 -->
      <div class="toolbar">
        <div class="view-switcher">
          <button
            @click="settingsStore.setViewMode('table')"
            class="view-btn"
            :class="{ active: settingsStore.viewMode === 'table' }"
          >
            <ElIcon class="view-icon"><List /></ElIcon>
            <span>表格</span>
          </button>
          <button
            @click="settingsStore.setViewMode('waterfall')"
            class="view-btn"
            :class="{ active: settingsStore.viewMode === 'waterfall' }"
          >
            <ElIcon class="view-icon"><Grid /></ElIcon>
            <span>瀑布流</span>
          </button>
        </div>
        
        <div class="total-count">
          <span class="count-number">{{ total }}</span>
          <span class="count-label">条结果</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-container {
  animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.03),
    0 1px 3px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.search-card:hover {
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.06),
    0 2px 6px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.search-form {
  margin-bottom: 0;
}

/* 桌面端布局 */
.desktop-layout {
  display: flex;
  gap: 16px;
  align-items: flex-end;
}

.search-fields-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.search-field-item {
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  animation-fill-mode: both;
}

.search-field-item:nth-child(1) { animation-delay: 0.1s; }
.search-field-item:nth-child(2) { animation-delay: 0.15s; }
.search-field-item:nth-child(3) { animation-delay: 0.2s; }
.search-field-item:nth-child(4) { animation-delay: 0.25s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 自定义输入框样式 */
.custom-input {
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  padding: 8px 12px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.custom-input :deep(.el-input__wrapper):hover {
  border-color: rgba(22, 24, 35, 0.3);
  box-shadow: 0 2px 8px rgba(22, 24, 35, 0.08);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #161823;
  background: rgba(255, 255, 255, 1);
  box-shadow: 
    0 0 0 3px rgba(22, 24, 35, 0.1),
    0 4px 12px rgba(22, 24, 35, 0.15);
  transform: translateY(-1px);
}

.custom-input :deep(.el-input__inner) {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 500;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: #999;
  font-weight: 400;
}

.input-icon {
  color: #161823;
  font-size: 16px;
}

/* 按钮样式 */
.action-buttons {
  display: flex;
  gap: 10px;
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
}

.search-button {
  background: linear-gradient(135deg, #161823 0%, #2d2f3e 100%);
  border: none;
  border-radius: 12px;
  padding: 9px 20px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 8px rgba(22, 24, 35, 0.25);
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
}

.search-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 24, 35, 0.35);
}

.search-button:active {
  transform: translateY(0);
}

.search-button :deep(.el-icon) {
  font-size: 16px;
}

.reset-button {
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 9px 16px;
  font-weight: 500;
  font-size: 14px;
  color: #666;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
}

.reset-button:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(0, 0, 0, 0.15);
  color: #333;
  transform: translateY(-1px);
}

.button-icon {
  font-size: 16px;
}

/* 移动端布局 */
.mobile-layout {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-search-main {
  display: flex;
  gap: 10px;
}

.mobile-input {
  flex: 1;
}

.mobile-search-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 12px;
}

.mobile-filters-expand {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  margin-top: 8px;
}

.mobile-filter-item {
  animation: fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.mobile-filter-item:nth-child(1) { animation-delay: 0.05s; }
.mobile-filter-item:nth-child(2) { animation-delay: 0.1s; }
.mobile-filter-item:nth-child(3) { animation-delay: 0.15s; }

.mobile-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.mobile-toggle-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 4px;
}

.mobile-toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(22, 24, 35, 0.05);
  border: 1px solid rgba(22, 24, 35, 0.1);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #161823;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mobile-toggle-btn:hover {
  background: rgba(22, 24, 35, 0.08);
  border-color: rgba(22, 24, 35, 0.2);
}

.toggle-icon {
  font-size: 14px;
  transition: transform 0.3s ease;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.active-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #2d2f3e;
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: scaleY(0.8) translateY(-10px);
}

/* 分隔线 */
.divider-line {
  height: 1px;
  background: linear-gradient(
    to right,
    transparent 0%,
    rgba(0, 0, 0, 0.06) 20%,
    rgba(0, 0, 0, 0.06) 80%,
    transparent 100%
  );
  margin: 20px 0;
}

/* 底部工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.35s both;
}

.view-switcher {
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.03);
  padding: 4px;
  border-radius: 12px;
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.view-btn:hover {
  color: #161823;
  background: rgba(22, 24, 35, 0.05);
}

.view-btn.active {
  background: linear-gradient(135deg, #161823 0%, #2d2f3e 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(22, 24, 35, 0.25);
}

.view-icon {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.view-btn:hover .view-icon {
  transform: scale(1.1);
}

.total-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.count-number {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #161823 0%, #2d2f3e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.count-label {
  font-size: 14px;
  color: #999;
  font-weight: 500;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .search-fields-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .search-card {
    padding: 16px;
    border-radius: 12px;
  }
  
  /* 移动端：布局切换和总数在一排 */
  .toolbar {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  
  .view-switcher {
    width: auto;
    justify-content: flex-start;
  }
  
  .total-count {
    justify-content: flex-end;
  }
}
</style>