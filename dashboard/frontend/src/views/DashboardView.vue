<template>
  <div>
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-statistic title="全部任务" :value="tasks.length" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="运行中" :value="countByStatus('running')" :value-style="{ color: '#1677ff' }" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="成功" :value="countByStatus('success')" :value-style="{ color: '#52c41a' }" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="异常" :value="countByStatus('error')" :value-style="{ color: '#ff4d4f' }" />
      </a-col>
    </a-row>

    <a-card title="任务时间线">
      <template #extra>
        <a-typography-text type="secondary" style="font-size: 12px">
          最后更新：{{ lastUpdated ? new Date(lastUpdated).toLocaleTimeString('ja-JP') : '—' }}
        </a-typography-text>
      </template>

      <TaskTimeline :tasks="tasks" />
    </a-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTaskStore } from '../stores/tasks'
import TaskTimeline from '../components/TaskTimeline.vue'

const store = useTaskStore()
const tasks = computed(() => store.tasks)
const lastUpdated = computed(() => store.lastUpdated)

function countByStatus(status) {
  return tasks.value.filter((t) => t.status === status).length
}
</script>
