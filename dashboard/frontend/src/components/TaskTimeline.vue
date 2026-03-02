<template>
  <a-timeline mode="left">
    <a-timeline-item
      v-for="task in sortedTasks"
      :key="task.id"
      :color="task.color"
    >
      <template #label>
        <a-typography-text type="secondary" style="font-size: 12px">
          {{ formatTime(task.updated_at) }}
        </a-typography-text>
      </template>

      <div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap">
        <a-tag :color="sourceColor(task.source)" style="font-size: 11px">
          {{ task.source }}
        </a-tag>
        <span style="font-weight: 500">{{ task.title }}</span>
        <a-badge :status="badgeStatus(task.status)" :text="statusLabel(task.status)" />
      </div>
      <div style="color: #666; font-size: 13px; margin-top: 4px">
        {{ task.detail }}
      </div>
    </a-timeline-item>

    <a-empty v-if="sortedTasks.length === 0" description="暂无任务数据" />
  </a-timeline>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
})

const sortedTasks = computed(() =>
  [...props.tasks].sort((a, b) => {
    const ta = a.updated_at ? new Date(a.updated_at) : new Date(0)
    const tb = b.updated_at ? new Date(b.updated_at) : new Date(0)
    return tb - ta
  })
)

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function sourceColor(source) {
  const map = { dataapp: 'blue', ecsite: 'purple', webapp: 'orange' }
  return map[source] || 'default'
}

function badgeStatus(status) {
  const map = {
    running: 'processing',
    success: 'success',
    error: 'error',
    pending: 'default',
  }
  return map[status] || 'default'
}

function statusLabel(status) {
  const map = {
    running: '运行中',
    success: '成功',
    error: '异常',
    pending: '等待中',
  }
  return map[status] || status
}
</script>
