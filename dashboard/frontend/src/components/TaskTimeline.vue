<template>
  <div style="overflow-x: auto">
    <div :style="{ minWidth: isMobile ? '280px' : '500px' }">

      <!-- Time axis header -->
      <div style="display: flex; margin-bottom: 4px">
        <div :style="{ width: labelWidth + 'px', flexShrink: 0 }"></div>
        <div style="flex: 1; position: relative; height: 20px">
          <span
            v-for="mark in timeMarks"
            :key="mark.pos"
            :style="{
              position: 'absolute',
              left: mark.pos + '%',
              transform: 'translateX(-50%)',
              fontSize: '11px',
              color: '#8c8c8c',
              whiteSpace: 'nowrap',
              userSelect: 'none',
            }"
          >{{ mark.label }}</span>
        </div>
      </div>

      <a-empty v-if="sortedTasks.length === 0" description="暂无任务数据" />

      <!-- Task rows -->
      <div
        v-for="(task, idx) in sortedTasks"
        :key="task.id"
        :style="{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '4px',
          borderRadius: '4px',
          background: idx % 2 === 0 ? '#fafafa' : 'transparent',
          padding: '3px 0',
          borderLeft: isMobile ? `3px solid ${SOURCE_COLORS[task.source] || '#d9d9d9'}` : 'none',
          paddingLeft: isMobile ? '6px' : '0',
        }"
      >
        <!-- Label column -->
        <div
          :style="{
            width: labelWidth + 'px',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            paddingRight: '10px',
            overflow: 'hidden',
          }"
        >
          <a-tag
            v-if="!isMobile"
            :color="sourceColor(task.source)"
            style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 18px"
          >{{ task.source }}</a-tag>
          <a-tooltip :title="task.title">
            <span
              :style="{
                fontSize: isMobile ? '11px' : '12px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                flex: 1,
              }"
            >{{ task.title }}</span>
          </a-tooltip>
        </div>

        <!-- Chart column -->
        <div style="flex: 1; position: relative; height: 30px">
          <!-- Vertical grid lines -->
          <div
            v-for="mark in timeMarks"
            :key="'grid-' + mark.pos"
            :style="{
              position: 'absolute',
              left: mark.pos + '%',
              top: 0,
              bottom: 0,
              width: '1px',
              background: '#e8e8e8',
              zIndex: 0,
            }"
          ></div>

          <!-- Task bar — tooltip only on desktop -->
          <a-tooltip v-if="task.started_at" placement="top" :disabled="isMobile">
            <template #title>
              <div>{{ task.title }}</div>
              <div style="color: #aaa; font-size: 11px">
                {{ formatTime(task.started_at) }} → {{ formatTime(task.updated_at) }}
              </div>
              <div style="margin-top: 4px">{{ task.detail }}</div>
            </template>
            <div
              :style="barStyle(task)"
              style="
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                height: 20px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                padding: 0 8px;
                font-size: 11px;
                color: white;
                cursor: pointer;
                overflow: hidden;
                white-space: nowrap;
                z-index: 1;
              "
              @click="openDetail(task)"
            >
              <span
                :style="{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'rgba(255,255,255,0.8)',
                  display: 'inline-block',
                  marginRight: '5px',
                  flexShrink: 0,
                  animation: task.status === 'running' ? 'pulse 1.5s infinite' : 'none',
                }"
              ></span>
              {{ statusLabel(task.status) }}
            </div>
          </a-tooltip>

          <!-- Pending marker — tooltip only on desktop -->
          <a-tooltip v-else placement="top" :disabled="isMobile">
            <template #title>
              <div>{{ task.title }}</div>
              <div style="color: #aaa; font-size: 11px">{{ formatTime(task.updated_at) }}</div>
              <div style="margin-top: 4px">{{ task.detail }}</div>
            </template>
            <div
              :style="pendingMarkerStyle(task)"
              style="
                position: absolute;
                top: 50%;
                width: 12px;
                height: 12px;
                border-radius: 2px;
                cursor: pointer;
                z-index: 1;
              "
              @click="openDetail(task)"
            ></div>
          </a-tooltip>
        </div>
      </div>
    </div>

    <!-- Task detail modal -->
    <a-modal
      v-model:open="modalOpen"
      :title="selectedTask?.title"
      :footer="null"
      :centered="true"
      :width="isMobile ? '92%' : 480"
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
import { useIsMobile } from '../composables/useIsMobile'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
})

const isMobile = useIsMobile()
const labelWidth = computed(() => (isMobile.value ? 100 : 220))
const markCount = computed(() => (isMobile.value ? 3 : 5))

// Task detail modal
const modalOpen = ref(false)
const selectedTask = ref(null)
function openDetail(task) {
  selectedTask.value = task
  modalOpen.value = true
}

// Sort tasks by start time ascending
const sortedTasks = computed(() =>
  [...props.tasks].sort((a, b) => {
    const ta = a.started_at ? new Date(a.started_at).getTime() : new Date(a.updated_at || 0).getTime()
    const tb = b.started_at ? new Date(b.started_at).getTime() : new Date(b.updated_at || 0).getTime()
    return ta - tb
  })
)

// Overall time range with padding
const timeRange = computed(() => {
  const times = []
  props.tasks.forEach((task) => {
    if (task.started_at) times.push(new Date(task.started_at).getTime())
    if (task.updated_at) times.push(new Date(task.updated_at).getTime())
  })
  if (times.length === 0) {
    const now = Date.now()
    return { min: now - 3_600_000, max: now }
  }
  const min = Math.min(...times)
  const max = Math.max(...times)
  const padding = Math.max((max - min) * 0.08, 300_000)
  return { min: min - padding, max: max + padding }
})

const totalMs = computed(() => timeRange.value.max - timeRange.value.min)

function toPercent(isoStr) {
  if (!isoStr) return 0
  return ((new Date(isoStr).getTime() - timeRange.value.min) / totalMs.value) * 100
}

const timeMarks = computed(() =>
  Array.from({ length: markCount.value + 1 }, (_, i) => {
    const t = new Date(timeRange.value.min + (totalMs.value * i) / markCount.value)
    return { pos: (i / markCount.value) * 100, label: formatTime(t.toISOString()) }
  })
)

const STATUS_COLORS = {
  running: '#1677ff',
  success: '#52c41a',
  error: '#ff4d4f',
  pending: '#bfbfbf',
}

const SOURCE_COLORS = {
  dataapp: '#1677ff',
  ecsite: '#722ed1',
  webapp: '#fa8c16',
}

function barStyle(task) {
  const left = toPercent(task.started_at)
  const right = toPercent(task.updated_at)
  const width = Math.max(right - left, 0.8)
  const bg = STATUS_COLORS[task.status] || '#bfbfbf'
  return {
    left: left + '%',
    width: width + '%',
    background: bg,
    opacity: 0.9,
    boxShadow: task.status === 'running' ? `0 0 0 2px ${bg}44` : 'none',
  }
}

function pendingMarkerStyle(task) {
  const pos = toPercent(task.updated_at)
  return {
    left: `calc(${pos}% - 6px)`,
    transform: 'translateY(-50%) rotate(45deg)',
    background: STATUS_COLORS.pending,
  }
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

<style scoped>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
