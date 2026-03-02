<template>
  <div style="overflow-x: auto">
    <div :style="{ minWidth: isMobile ? '320px' : '580px' }">

      <!-- ── Time axis header ───────────────────────────────────────────── -->
      <div :style="rowStyle('header')">
        <div :style="labelColStyle"></div>
        <div :style="{ ...chartColStyle, position: 'relative', height: '20px' }">
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

      <a-empty v-if="taskGroups.length === 0" description="暂无任务数据" />

      <!-- ── Task group rows ────────────────────────────────────────────── -->
      <div v-for="group in taskGroups" :key="group.id">

        <!-- L1 row -->
        <div
          :style="{
            ...rowStyle('l1'),
            background: '#f0f5ff',
            borderRadius: '4px',
            cursor: 'pointer',
          }"
          @click="toggle(group.id)"
        >
          <!-- Label col -->
          <div :style="{ ...labelColStyle, display: 'flex', alignItems: 'center', gap: '5px', paddingRight: '8px', overflow: 'hidden' }">
            <right-outlined
              :style="{
                fontSize: '10px',
                color: '#8c8c8c',
                flexShrink: 0,
                transition: 'transform 0.2s',
                transform: isExpanded(group.id) ? 'rotate(90deg)' : 'none',
              }"
            />
            <a-tag
              :color="group.pipeline === 'excel' ? 'green' : 'geekblue'"
              style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 18px"
            >{{ group.pipeline }}</a-tag>
            <span
              :title="group.label"
              style="font-size: 12px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1"
            >{{ group.label }}</span>
            <a-badge :status="groupBadgeStatus(group)" style="flex-shrink: 0" />
          </div>

          <!-- Chart col: mini block track -->
          <div :style="{ ...chartColStyle, position: 'relative' }">
            <div v-for="mark in timeMarks" :key="'g1-' + group.id + mark.pos" :style="gridLineStyle(mark.pos)"></div>
            <span
              v-if="group.batches.length === 0"
              style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 11px; color: #d9d9d9; white-space: nowrap; pointer-events: none"
            >暂无记录</span>
            <div
              v-for="batch in group.batches"
              :key="'mini-' + batch.id"
              :style="miniBlockStyle(batch)"
            ></div>
          </div>
        </div>

        <!-- L2 rows (expandable) -->
        <Transition name="expand">
          <div v-if="isExpanded(group.id)">
            <!-- Empty state -->
            <div v-if="group.batches.length === 0" :style="rowStyle('l2')">
              <div :style="{ ...labelColStyle, paddingLeft: '24px' }"></div>
              <div :style="chartColStyle" style="display: flex; align-items: center">
                <span style="font-size: 12px; color: #bfbfbf">该任务暂无批次记录</span>
              </div>
            </div>

            <!-- Batch rows -->
            <div
              v-for="(batch, idx) in group.batches"
              :key="'l2-' + batch.id"
              :style="{
                ...rowStyle('l2'),
                background: idx % 2 === 0 ? '#fafafa' : 'transparent',
              }"
            >
              <!-- Label col -->
              <div :style="{ ...labelColStyle, paddingLeft: '22px', display: 'flex', alignItems: 'center', gap: '5px', overflow: 'hidden', paddingRight: '8px' }">
                <a-tag
                  :color="batch.source === 'excel' ? 'green' : 'geekblue'"
                  style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 16px"
                >{{ batch.source === 'excel' ? 'Excel' : 'DB' }}</a-tag>
                <span
                  :title="batch.detail"
                  style="font-size: 11px; color: #595959; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1"
                >{{ batch.detail }}</span>
              </div>

              <!-- Chart col: progress bar -->
              <div :style="{ ...chartColStyle, position: 'relative' }">
                <div v-for="mark in timeMarks" :key="'g2-' + batch.id + mark.pos" :style="gridLineStyle(mark.pos)"></div>
                <a-tooltip :disabled="isMobile" placement="top">
                  <template #title>
                    <div style="font-weight: 500">{{ group.label }}</div>
                    <div style="color: #aaa; font-size: 11px; margin-top: 2px">
                      {{ formatTime(batch.created_at) }} →
                      {{ batch.completed_at ? formatTime(batch.completed_at) : '进行中' }}
                    </div>
                    <div style="margin-top: 4px">{{ batch.completed_jobs }} / {{ batch.total_jobs }} 完成</div>
                    <div v-if="batch.failed_jobs > 0" style="color: #ff7875; font-size: 11px">
                      {{ batch.failed_jobs }} 失败
                    </div>
                  </template>
                  <!-- Progress bar container -->
                  <div
                    :style="batchBarContainerStyle(batch)"
                    style="
                      position: absolute;
                      top: 50%;
                      transform: translateY(-50%);
                      height: 22px;
                      border-radius: 4px;
                      overflow: hidden;
                      cursor: pointer;
                      display: flex;
                      align-items: center;
                      z-index: 1;
                      min-width: 6px;
                    "
                    @click="openDetail(batch, group)"
                  >
                    <!-- Unfilled overlay (right portion, lighter) -->
                    <div :style="batchUnfilledStyle(batch)" style="position: absolute; right: 0; top: 0; bottom: 0;"></div>
                    <!-- Label -->
                    <span style="position: relative; z-index: 2; font-size: 11px; color: white; padding: 0 8px; white-space: nowrap; overflow: hidden; text-shadow: 0 1px 2px rgba(0,0,0,0.25)">
                      <span
                        v-if="batch.status === 'running'"
                        style="display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: white; margin-right: 4px; vertical-align: middle; animation: pulse 1.5s infinite"
                      ></span>
                      {{ batch.completed_jobs }}/{{ batch.total_jobs }}
                    </span>
                  </div>
                </a-tooltip>
              </div>
            </div>
          </div>
        </Transition>

      </div><!-- end group loop -->

    </div><!-- end min-width wrapper -->

    <!-- Detail modal -->
    <a-modal
      v-model:open="modalOpen"
      :title="selectedGroup?.label"
      :footer="null"
      :centered="true"
      :width="isMobile ? '92%' : 460"
    >
      <div v-if="selectedBatch">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap">
          <a-tag :color="selectedBatch.source === 'excel' ? 'green' : 'geekblue'">
            {{ selectedBatch.source === 'excel' ? 'Excel' : 'DB' }}
          </a-tag>
          <a-tag :color="selectedGroup?.pipeline === 'excel' ? 'green' : 'geekblue'">
            {{ selectedGroup?.pipeline }}
          </a-tag>
          <a-badge :status="badgeStatus(selectedBatch.status)" :text="statusLabel(selectedBatch.status)" />
        </div>
        <div style="color: #8c8c8c; font-size: 13px; margin-bottom: 14px">
          {{ formatTime(selectedBatch.created_at) }} →
          {{ selectedBatch.completed_at ? formatTime(selectedBatch.completed_at) : '进行中' }}
        </div>
        <div style="margin-bottom: 14px">
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px">
            <span>完成进度</span>
            <span>{{ selectedBatch.completed_jobs }} / {{ selectedBatch.total_jobs }}</span>
          </div>
          <a-progress
            :percent="progressPct(selectedBatch)"
            :status="progressAntStatus(selectedBatch)"
          />
          <div v-if="selectedBatch.failed_jobs > 0" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
            {{ selectedBatch.failed_jobs }} 个失败
          </div>
        </div>
        <div style="color: #595959; font-size: 13px; word-break: break-all">{{ selectedBatch.detail }}</div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RightOutlined } from '@ant-design/icons-vue'
import { useIsMobile } from '../composables/useIsMobile'

const props = defineProps({
  taskGroups: { type: Array, default: () => [] },
})

const isMobile = useIsMobile()
const LABEL_WIDTH = computed(() => (isMobile.value ? 120 : 240))
const MARK_COUNT = computed(() => (isMobile.value ? 3 : 5))

// ── Expand state ────────────────────────────────────────────────────────────
const expandedGroups = ref({})
function toggle(id) {
  expandedGroups.value[id] = !expandedGroups.value[id]
}
function isExpanded(id) {
  return !!expandedGroups.value[id]
}

// ── Modal ───────────────────────────────────────────────────────────────────
const modalOpen = ref(false)
const selectedBatch = ref(null)
const selectedGroup = ref(null)
function openDetail(batch, group) {
  selectedBatch.value = batch
  selectedGroup.value = group
  modalOpen.value = true
}

// ── Reactive now (for running bar right edge only) ──────────────────────────
const now = ref(Date.now())
let timer
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { clearInterval(timer) })

// ── Time range (does NOT use reactive now — stable per SSE update) ──────────
const timeRange = computed(() => {
  const times = []
  props.taskGroups.forEach((g) => {
    g.batches.forEach((b) => {
      if (b.created_at) times.push(new Date(b.created_at).getTime())
      if (b.completed_at) times.push(new Date(b.completed_at).getTime())
    })
  })
  const hasRunning = props.taskGroups.some((g) => g.batches.some((b) => b.status === 'running'))
  // Extend right edge for running batches using non-reactive Date.now()
  if (hasRunning) times.push(Date.now() + 10 * 60 * 1000)

  if (times.length === 0) {
    const n = Date.now()
    return { min: n - 3_600_000, max: n + 600_000 }
  }
  const min = Math.min(...times)
  const max = Math.max(...times)
  const padding = Math.max((max - min) * 0.05, 300_000)
  return { min: min - padding, max: max + padding }
})

const totalMs = computed(() => timeRange.value.max - timeRange.value.min)

function toPercent(isoStr) {
  if (!isoStr) return 0
  return ((new Date(isoStr).getTime() - timeRange.value.min) / totalMs.value) * 100
}

// Right edge % for a batch (uses reactive now only for running batches)
function rightPct(batch) {
  if (batch.completed_at) return toPercent(batch.completed_at)
  const rightMs = Math.min(now.value, timeRange.value.max)
  return ((rightMs - timeRange.value.min) / totalMs.value) * 100
}

// ── Time axis marks ──────────────────────────────────────────────────────────
const timeMarks = computed(() =>
  Array.from({ length: MARK_COUNT.value + 1 }, (_, i) => {
    const t = new Date(timeRange.value.min + (totalMs.value * i) / MARK_COUNT.value)
    return { pos: (i / MARK_COUNT.value) * 100, label: formatTime(t.toISOString()) }
  })
)

// ── Layout helpers ───────────────────────────────────────────────────────────
const labelColStyle = computed(() => ({
  width: LABEL_WIDTH.value + 'px',
  flexShrink: 0,
}))

const chartColStyle = { flex: 1, overflow: 'hidden' }

function rowStyle(type) {
  const heights = { header: '20px', l1: '36px', l2: '30px' }
  return {
    display: 'flex',
    alignItems: 'stretch',
    height: heights[type],
    marginBottom: type === 'l2' ? '2px' : '4px',
    padding: type === 'l1' ? '0 4px' : '0',
  }
}

function gridLineStyle(pos) {
  return {
    position: 'absolute',
    left: pos + '%',
    top: 0,
    bottom: 0,
    width: '1px',
    background: '#e8e8e8',
    zIndex: 0,
  }
}

// ── Status colors ─────────────────────────────────────────────────────────────
const STATUS_COLORS = {
  running: '#1677ff',
  success: '#52c41a',
  error: '#ff4d4f',
  pending: '#bfbfbf',
}

// ── Mini block (L1) ─────────────────────────────────────────────────────────
function miniBlockStyle(batch) {
  const left = toPercent(batch.created_at)
  const right = rightPct(batch)
  const width = Math.max(right - left, 0.5)
  return {
    position: 'absolute',
    left: left + '%',
    width: width + '%',
    height: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    borderRadius: '2px',
    background: STATUS_COLORS[batch.status] || '#bfbfbf',
    opacity: batch.status === 'running' ? 1 : 0.65,
    zIndex: 1,
    transition: 'width 0.5s linear',
  }
}

// ── Batch progress bar (L2) ──────────────────────────────────────────────────
function batchBarContainerStyle(batch) {
  const left = toPercent(batch.created_at)
  const right = rightPct(batch)
  const width = Math.max(right - left, 0.8)
  return {
    left: left + '%',
    width: width + '%',
    background: STATUS_COLORS[batch.status] || '#bfbfbf',
    boxShadow: batch.status === 'running' ? `0 0 0 2px ${STATUS_COLORS.running}33` : 'none',
    transition: 'width 0.5s linear',
  }
}

// Semi-transparent overlay for the unfilled portion
function batchUnfilledStyle(batch) {
  const pct = progressPct(batch)
  return {
    width: (100 - pct) + '%',
    background: 'rgba(255,255,255,0.45)',
    transition: 'width 0.5s ease',
  }
}

function progressPct(batch) {
  if (batch.status === 'success') return 100
  if (!batch.total_jobs) return 0
  return Math.min(Math.round((batch.completed_jobs / batch.total_jobs) * 100), 100)
}

function progressAntStatus(batch) {
  if (batch.status === 'error') return 'exception'
  if (batch.status === 'running') return 'active'
  return 'normal'
}

// ── Group summary badge ──────────────────────────────────────────────────────
function groupBadgeStatus(group) {
  if (group.batches.some((b) => b.status === 'running')) return 'processing'
  if (!group.batches.length) return 'default'
  const last = group.batches.reduce((a, b) =>
    new Date(a.created_at) > new Date(b.created_at) ? a : b
  )
  return badgeStatus(last.status)
}

// ── Formatters ───────────────────────────────────────────────────────────────
function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function badgeStatus(status) {
  return { running: 'processing', success: 'success', error: 'error', pending: 'default' }[status] ?? 'default'
}

function statusLabel(status) {
  return { running: '运行中', success: '成功', error: '异常', pending: '等待中' }[status] ?? status
}
</script>

<style scoped>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.expand-enter-active {
  animation: expandDown 0.2s ease;
}
.expand-leave-active {
  animation: expandDown 0.15s ease reverse;
}
@keyframes expandDown {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
