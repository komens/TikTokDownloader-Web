<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon, ElSelect, ElOption } from 'element-plus'
import { ArrowLeft, ArrowRight, MoreFilled } from '@element-plus/icons-vue'

interface Props {
  currentPage: number
  pageSize: number
  total: number
  pageSizes?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  pageSizes: () => [20, 50, 100]
})

const emit = defineEmits<{
  'update:currentPage': [value: number]
  'update:pageSize': [value: number]
  'pageChange': [value: number]
  'sizeChange': [value: number]
}>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))
const showPages = computed(() => {
  const pages: (number | string)[] = []
  const current = props.currentPage
  const total = totalPages.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    }
  }

  return pages
})

const isFirstPage = computed(() => props.currentPage === 1)
const isLastPage = computed(() => props.currentPage === totalPages.value || totalPages.value === 0)

function handlePageChange(page: number) {
  if (page < 1 || page > totalPages.value || page === props.currentPage) {
    return
  }
  emit('update:currentPage', page)
  emit('pageChange', page)
}

function handleSizeChange(size: number) {
  emit('update:pageSize', size)
  emit('sizeChange', size)
}

function handlePrevPage() {
  if (!isFirstPage.value) {
    handlePageChange(props.currentPage - 1)
  }
}

function handleNextPage() {
  if (!isLastPage.value) {
    handlePageChange(props.currentPage + 1)
  }
}
</script>

<template>
  <div class="pagination-container">
    <!-- 信息统计 -->
    <div class="pagination-info">
      <span class="info-text">
        共 <span class="info-number">{{ total }}</span> 条
      </span>
    </div>

    <!-- 分页控制 -->
    <div class="pagination-controls">
      <!-- 上一页按钮 -->
      <button
        class="pagination-btn prev-btn"
        :class="{ disabled: isFirstPage }"
        :disabled="isFirstPage"
        @click="handlePrevPage"
      >
        <ElIcon class="btn-icon"><ArrowLeft /></ElIcon>
      </button>

      <!-- 页码列表 -->
      <div class="page-list">
        <template v-for="(page, index) in showPages" :key="index">
          <button
            v-if="typeof page === 'number'"
            class="page-btn"
            :class="{ active: page === currentPage }"
            @click="handlePageChange(page)"
          >
            {{ page }}
          </button>
          <span v-else class="page-ellipsis">
            <ElIcon><MoreFilled /></ElIcon>
          </span>
        </template>
      </div>

      <!-- 下一页按钮 -->
      <button
        class="pagination-btn next-btn"
        :class="{ disabled: isLastPage }"
        :disabled="isLastPage"
        @click="handleNextPage"
      >
        <ElIcon class="btn-icon"><ArrowRight /></ElIcon>
      </button>
    </div>

    <!-- 每页数量选择 -->
    <div class="page-size-selector">
      <span class="selector-label">每页</span>
      <ElSelect
        :model-value="pageSize"
        class="size-select"
        @update:model-value="handleSizeChange"
      >
        <ElOption
          v-for="size in pageSizes"
          :key="size"
          :label="size"
          :value="size"
        />
      </ElSelect>
      <span class="selector-label">条</span>
    </div>

    <!-- 快速跳转 -->
    <div class="quick-jump">
      <span class="jump-label">跳至</span>
      <input
        type="number"
        class="jump-input"
        :min="1"
        :max="totalPages"
        :value="currentPage"
        @keyup.enter="handlePageChange(Number(($event.target as HTMLInputElement).value))"
      />
      <span class="jump-label">页</span>
    </div>
  </div>
</template>

<style scoped>
.pagination-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  border-radius: 16px;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.03),
    0 1px 3px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 信息统计 */
.pagination-info {
  display: flex;
  align-items: center;
}

.info-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.info-number {
  font-weight: 600;
  color: #161823;
  margin: 0 2px;
}

/* 分页控制 */
.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.pagination-btn:hover:not(.disabled) {
  background: rgba(22, 24, 35, 0.05);
  border-color: rgba(22, 24, 35, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(22, 24, 35, 0.15);
}

.pagination-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 16px;
  color: #666;
  transition: color 0.3s ease;
}

.pagination-btn:hover:not(.disabled) .btn-icon {
  color: #161823;
}

/* 页码列表 */
.page-list {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.page-btn:hover:not(.active) {
  background: rgba(22, 24, 35, 0.05);
  border-color: rgba(22, 24, 35, 0.2);
  color: #161823;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(22, 24, 35, 0.15);
}

.page-btn.active {
  background: linear-gradient(135deg, #161823 0%, #2d2f3e 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 12px rgba(22, 24, 35, 0.25);
  transform: translateY(-2px);
}

.page-ellipsis {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 14px;
}

/* 每页数量选择 */
.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.size-select {
  width: 80px;
}

.size-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.size-select :deep(.el-input__wrapper):hover {
  border-color: rgba(22, 24, 35, 0.3);
  box-shadow: 0 2px 8px rgba(22, 24, 35, 0.08);
}

.size-select :deep(.el-input__wrapper.is-focus) {
  border-color: #161823;
  box-shadow: 
    0 0 0 3px rgba(22, 24, 35, 0.1),
    0 4px 12px rgba(22, 24, 35, 0.15);
}

/* 快速跳转 */
.quick-jump {
  display: flex;
  align-items: center;
  gap: 8px;
}

.jump-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.jump-input {
  width: 60px;
  height: 36px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.jump-input:hover {
  border-color: rgba(22, 24, 35, 0.3);
  box-shadow: 0 2px 8px rgba(22, 24, 35, 0.08);
}

.jump-input:focus {
  outline: none;
  border-color: #161823;
  background: rgba(255, 255, 255, 1);
  box-shadow: 
    0 0 0 3px rgba(22, 24, 35, 0.1),
    0 4px 12px rgba(22, 24, 35, 0.15);
}

.jump-input::-webkit-inner-spin-button,
.jump-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.jump-input[type=number] {
  -moz-appearance: textfield;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .pagination-container {
    flex-wrap: wrap;
    gap: 16px;
  }

  .pagination-info {
    order: 1;
    width: 100%;
    justify-content: center;
  }

  .pagination-controls {
    order: 2;
    width: 100%;
    justify-content: center;
  }

  .page-size-selector,
  .quick-jump {
    order: 3;
  }
}

@media (max-width: 768px) {
  .pagination-container {
    padding: 16px;
    gap: 12px;
  }

  .page-list {
    gap: 4px;
  }

  .page-btn {
    min-width: 32px;
    height: 32px;
    padding: 0 8px;
    font-size: 13px;
  }

  .pagination-btn {
    width: 32px;
    height: 32px;
  }

  /* 移动端保留 pageSize 选择，隐藏快速跳转 */
  .page-size-selector {
    order: 3;
    width: 100%;
    justify-content: center;
  }

  .quick-jump {
    display: none;
  }
}
</style>