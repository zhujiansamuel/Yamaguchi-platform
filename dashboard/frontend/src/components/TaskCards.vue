<template>
  <div>
    <a-empty v-if="sortedTasks.length === 0" description="暂无任务数据" />

    <div
      v-for="task in sortedTasks"
      :key="task.id"
      :style="{
        borderLeft: `4px solid ${STATUS_COLORS[task.status] || '#d9d9d9'}`,
        background: '#fafafa',
        borderRadius: '6px',
        padding: '12px 14px',
        marginBottom: '10px',
        cursor: 'pointer',
        transition: 'box-shadow 0.2s',
      }"
      @click="openDetail(task)"
      @mouseenter="(e) => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)')"
      @mouseleave="(e) => (e.currentTarget.style.boxShadow = 'none')"
    >
      <!-- Header row: source tag + status badge -->
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px">
        <a-tag :color="sourceColor(task.source)" style="margin: 0; font-size: 11px">
          {{ task.source }}
        </a-tag>
        <a-badge :status="badgeStatus(task.status)" :text="statusLabel(task.status)" />
      </div>

      <!-- Task title -->
      <div style="font-weight: 500; font-size: 14px; margin-bottom: 4px; line-height: 1.4">
        {{ task.title }}
      </div>

      <!-- Time range -->
      <div style="font-size: 12px; color: #8c8c8c; margin-bottom: 4px">
        <template v-if="task.started_at">
          {{ formatTime(task.started_at) }} → {{ formatTime(task.updated_at) }}
        </template>
        <template v-else>
          {{ formatTime(task.updated_at) }}
        </template>
      </div>

      <!-- Detail (truncated) -->
      <div style="font-size: 13px; color: #595959; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
        {{ task.detail }}
      </div>
    </div>

    <!-- Task detail modal -->
    <a-modal
      v-model:open="modalOpen"
      :title="selectedTask?.title"
      :footer="null"
      :centered="true"
    >
      <div v-if="selectedTask">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap">
          <a-tag :color="sourceColor(selectedTask.source)">{{ selectedTask.source }}</a-tag>
          <a-badge :status="badgeStatus(selectedTask.status)" :text="statusLabel(selectedTask.status)" />
        </div>
        <div style="color: #8c8c8c; font-size: 13px; margin-bottom: 10px">
          <template v-if="selectedTask.started_at">
            {{ formatTime(selectedTask.started_at) }} → {{ formatTime(selectedTask.updated_at) }}
          </template>
          <template v-else>
            {{ formatTime(selectedTask.updated_at) }}
          </template>
        </div>
        <div style="color: #333; font-size: 14px; line-height: 1.6">{{ selectedTask.detail }}</div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
})

const modalOpen = ref(false)
const selectedTask = ref(null)

function openDetail(task) {
  selectedTask.value = task
  modalOpen.value = true
}

const sortedTasks = computed(() =>
  [...props.tasks].sort((a, b) => {
    const ta = a.started_at ? new Date(a.started_at).getTime() : new Date(a.updated_at || 0).getTime()
    const tb = b.started_at ? new Date(b.started_at).getTime() : new Date(b.updated_at || 0).getTime()
    return ta - tb
  })
)

const STATUS_COLORS = {
  running: '#1677ff',
  success: '#52c41a',
  error: '#ff4d4f',
  pending: '#bfbfbf',
}

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
  const map = { running: 'processing', success: 'success', error: 'error', pending: 'default' }
  return map[status] || 'default'
}

function statusLabel(status) {
  const map = { running: '运行中', success: '成功', error: '异常', pending: '等待中' }
  return map[status] || status
}
</script>
