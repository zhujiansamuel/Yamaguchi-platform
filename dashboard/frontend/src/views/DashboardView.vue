<template>
  <div>
    <!-- Stats: count over all batches across all groups -->
    <a-row :gutter="[16, 16]" style="margin-bottom: 16px">
      <a-col :xs="12" :sm="6">
        <a-statistic title="全部批次" :value="allBatches.length" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic
          title="运行中"
          :value="countStatus('running')"
          :value-style="{ color: '#1677ff' }"
        />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic
          title="成功"
          :value="countStatus('success')"
          :value-style="{ color: '#52c41a' }"
        />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic
          title="异常"
          :value="countStatus('error')"
          :value-style="{ color: '#ff4d4f' }"
        />
      </a-col>
    </a-row>

    <a-card title="追踪任务时间线">
      <template #extra>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end">
          <a-segmented v-model:value="viewMode" :options="viewOptions" size="small" />
          <a-typography-text v-if="!isMobile" type="secondary" style="font-size: 12px">
            最后更新：{{ lastUpdated ? new Date(lastUpdated).toLocaleTimeString('ja-JP') : '—' }}
          </a-typography-text>
        </div>
      </template>

      <TaskTimeline v-if="viewMode === 'gantt'" :task-groups="taskGroups" />
      <TaskCards v-else :task-groups="taskGroups" />
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
const taskGroups = computed(() => store.taskGroups)
const lastUpdated = computed(() => store.lastUpdated)
const isMobile = useIsMobile()

const viewMode = ref(isMobile.value ? 'card' : 'gantt')
watch(isMobile, (mobile) => { viewMode.value = mobile ? 'card' : 'gantt' })

const viewOptions = [
  { label: '甘特图', value: 'gantt' },
  { label: '卡片', value: 'card' },
]

const allBatches = computed(() => taskGroups.value.flatMap((g) => g.batches))
function countStatus(status) {
  return allBatches.value.filter((b) => b.status === status).length
}
</script>
