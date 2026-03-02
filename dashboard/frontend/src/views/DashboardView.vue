<template>
  <div>
    <!-- Stats: 2×2 on mobile, 4 columns on desktop -->
    <a-row :gutter="[16, 16]" style="margin-bottom: 16px">
      <a-col :xs="12" :sm="6">
        <a-statistic title="全部任务" :value="tasks.length" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="运行中" :value="countByStatus('running')" :value-style="{ color: '#1677ff' }" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="成功" :value="countByStatus('success')" :value-style="{ color: '#52c41a' }" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="异常" :value="countByStatus('error')" :value-style="{ color: '#ff4d4f' }" />
      </a-col>
    </a-row>

    <a-card title="任务时间线">
      <template #extra>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end">
          <a-segmented v-model:value="viewMode" :options="viewOptions" size="small" />
          <a-typography-text v-if="!isMobile" type="secondary" style="font-size: 12px">
            最后更新：{{ lastUpdated ? new Date(lastUpdated).toLocaleTimeString('ja-JP') : '—' }}
          </a-typography-text>
        </div>
      </template>

      <TaskTimeline v-if="viewMode === 'gantt'" :tasks="tasks" />
      <TaskCards v-else :tasks="tasks" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTaskStore } from '../stores/tasks'
import { useIsMobile } from '../composables/useIsMobile'
import TaskTimeline from '../components/TaskTimeline.vue'
import TaskCards from '../components/TaskCards.vue'

const store = useTaskStore()
const tasks = computed(() => store.tasks)
const lastUpdated = computed(() => store.lastUpdated)
const isMobile = useIsMobile()

// Default to card view on mobile, gantt on desktop
const viewMode = ref(isMobile.value ? 'card' : 'gantt')

// Follow screen size changes (e.g., rotating device)
watch(isMobile, (mobile) => {
  viewMode.value = mobile ? 'card' : 'gantt'
})

const viewOptions = [
  { label: '甘特图', value: 'gantt' },
  { label: '卡片', value: 'card' },
]

function countByStatus(status) {
  return tasks.value.filter((t) => t.status === status).length
}
</script>
