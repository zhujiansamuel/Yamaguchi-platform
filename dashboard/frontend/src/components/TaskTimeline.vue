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

      <a-empty v-if="sections.length === 0" description="暂无任务数据" />

      <!-- ── Sections ───────────────────────────────────────────────────── -->
      <div v-for="(section, sIdx) in sections" :key="section.id">

        <!-- Section divider -->
        <div
          :style="{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginTop: sIdx === 0 ? '4px' : '14px',
            marginBottom: '4px',
          }"
        >
          <span style="font-size: 11px; font-weight: 600; color: #595959; white-space: nowrap">
            {{ section.label }}
          </span>
          <div style="flex: 1; height: 1px; background: #d9d9d9"></div>
        </div>

        <!-- Task groups -->
        <div v-for="group in section.task_groups" :key="group.id">

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
                :color="pipelineColor(group.pipeline)"
                style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 18px"
              >{{ group.pipeline }}</a-tag>
              <span
                :title="group.label"
                style="font-size: 12px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1"
              >{{ group.label }}</span>
              <a-badge :status="groupBadgeStatus(group)" style="flex-shrink: 0" />
            </div>

            <!-- Chart area: event markers or mini blocks -->
            <div :style="{ ...chartColStyle, position: 'relative' }">
              <div v-for="mark in timeMarks" :key="'g1-' + group.id + mark.pos" :style="gridLineStyle(mark.pos)"></div>

              <!-- Event-based groups (nextcloud & webapp) -->
              <template v-if="isSyncGroup(group)">
                <span
                  v-if="group.events.length === 0"
                  style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 11px; color: #d9d9d9; white-space: nowrap; pointer-events: none"
                >暂无记录</span>
                <div
                  v-for="event in group.events"
                  :key="'mkr-' + event.id"
                  :style="markerStyle(event, group)"
                  @click.stop="openSyncDetail(event, group)"
                ></div>
              </template>

              <!-- Batch groups (excel / db / email) -->
              <template v-else>
                <span
                  v-if="group.batches.length === 0"
                  style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 11px; color: #d9d9d9; white-space: nowrap; pointer-events: none"
                >暂无记录</span>
                <div
                  v-for="batch in group.batches"
                  :key="'mini-' + batch.id"
                  :style="miniBlockStyle(batch)"
                ></div>
              </template>
            </div>
          </div>

          <!-- L2 rows (expandable) -->
          <Transition name="expand">
            <div v-if="isExpanded(group.id)">

              <!-- ── Event list (nextcloud / webapp) ── -->
              <template v-if="isSyncGroup(group)">
                <div v-if="group.events.length === 0" :style="rowStyle('l2')">
                  <div :style="{ ...labelColStyle, paddingLeft: '24px' }"></div>
                  <div :style="chartColStyle" style="display: flex; align-items: center">
                    <span style="font-size: 12px; color: #bfbfbf">暂无记录</span>
                  </div>
                </div>

                <div
                  v-for="(event, eIdx) in group.events"
                  :key="'l2e-' + event.id"
                  :style="{
                    ...rowStyle('l2'),
                    background: eIdx % 2 === 0 ? '#fafafa' : 'transparent',
                    cursor: 'pointer',
                  }"
                  @click="openSyncDetail(event, group)"
                >
                  <!-- Label col: nextcloud -->
                  <template v-if="group.pipeline === 'nextcloud'">
                    <div :style="{ ...labelColStyle, paddingLeft: '22px', display: 'flex', alignItems: 'center', gap: '5px', overflow: 'hidden', paddingRight: '8px' }">
                      <span :style="{ color: eventColor(event), fontSize: '12px', flexShrink: 0, fontWeight: 700, lineHeight: 1 }">
                        {{ event.direction === 'in' ? '▼' : '▲' }}
                      </span>
                      <a-tag
                        :color="event.trigger === 'webhook' ? 'blue' : 'default'"
                        style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 16px"
                      >{{ event.trigger === 'webhook' ? 'hook' : '定时' }}</a-tag>
                      <span style="font-size: 11px; color: #595959; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1">
                        {{ event.record_count }} 条 · {{ formatTime(event.timestamp) }}
                      </span>
                    </div>
                  </template>

                  <!-- Label col: webapp -->
                  <template v-else>
                    <div :style="{ ...labelColStyle, paddingLeft: '22px', display: 'flex', alignItems: 'center', gap: '5px', overflow: 'hidden', paddingRight: '8px' }">
                      <a-badge :status="badgeStatus(event.status)" style="flex-shrink: 0" />
                      <span style="font-size: 11px; color: #595959; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1">
                        {{ event.status === 'success'
                          ? `写入 ${event.rows_inserted + event.rows_updated}/${event.rows_received}`
                          : '失败' }}
                        · {{ formatTime(event.timestamp) }}
                      </span>
                    </div>
                  </template>

                  <!-- Chart col (shared) -->
                  <div :style="{ ...chartColStyle, position: 'relative' }">
                    <div v-for="mark in timeMarks" :key="'g2e-' + event.id + mark.pos" :style="gridLineStyle(mark.pos)"></div>
                    <div
                      :style="{
                        position: 'absolute',
                        left: toPercent(event.timestamp) + '%',
                        top: '15%',
                        bottom: '15%',
                        width: '2px',
                        background: eventColor(event),
                        transform: 'translateX(-50%)',
                        borderRadius: '1px',
                        zIndex: 1,
                      }"
                    ></div>
                  </div>
                </div>
              </template>

              <!-- ── Batch progress bars (excel / db / email) ── -->
              <template v-else>
                <div v-if="group.batches.length === 0" :style="rowStyle('l2')">
                  <div :style="{ ...labelColStyle, paddingLeft: '24px' }"></div>
                  <div :style="chartColStyle" style="display: flex; align-items: center">
                    <span style="font-size: 12px; color: #bfbfbf">该任务暂无批次记录</span>
                  </div>
                </div>

                <div
                  v-for="(batch, bIdx) in group.batches"
                  :key="'l2-' + batch.id"
                  :style="{
                    ...rowStyle('l2'),
                    background: bIdx % 2 === 0 ? '#fafafa' : 'transparent',
                  }"
                >
                  <div :style="{ ...labelColStyle, paddingLeft: '22px', display: 'flex', alignItems: 'center', gap: '5px', overflow: 'hidden', paddingRight: '8px' }">
                    <a-tag
                      :color="sourceColor(batch.source)"
                      style="font-size: 10px; flex-shrink: 0; margin: 0; padding: 0 4px; line-height: 16px"
                    >{{ sourceLabel(batch.source) }}</a-tag>
                    <span
                      :title="batch.detail"
                      style="font-size: 11px; color: #595959; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1"
                    >{{ batch.detail }}</span>
                  </div>

                  <div :style="{ ...chartColStyle, position: 'relative' }">
                    <div v-for="mark in timeMarks" :key="'g2-' + batch.id + mark.pos" :style="gridLineStyle(mark.pos)"></div>

                    <span
                      v-if="!batch.created_at"
                      style="position: absolute; top: 50%; left: 8px; transform: translateY(-50%); font-size: 11px; color: #bfbfbf"
                    >等待触发</span>

                    <a-tooltip v-else :disabled="isMobile" placement="top">
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
                        <div :style="batchUnfilledStyle(batch)" style="position: absolute; right: 0; top: 0; bottom: 0;"></div>
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
              </template>

            </div>
          </Transition>

        </div><!-- end group loop -->
      </div><!-- end section loop -->

    </div><!-- end min-width wrapper -->

    <!-- Batch detail modal -->
    <a-modal
      v-model:open="modalOpen"
      :title="selectedGroup?.label"
      :footer="null"
      :centered="true"
      :width="isMobile ? '92%' : 460"
    >
      <div v-if="selectedBatch">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap">
          <a-tag :color="sourceColor(selectedBatch.source)">{{ sourceLabel(selectedBatch.source) }}</a-tag>
          <a-tag :color="pipelineColor(selectedGroup?.pipeline)">{{ selectedGroup?.pipeline }}</a-tag>
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
          <a-progress :percent="progressPct(selectedBatch)" :status="progressAntStatus(selectedBatch)" />
          <div v-if="selectedBatch.failed_jobs > 0" style="color: #ff4d4f; font-size: 12px; margin-top: 4px">
            {{ selectedBatch.failed_jobs }} 个失败
          </div>
        </div>
        <div style="color: #595959; font-size: 13px; word-break: break-all">{{ selectedBatch.detail }}</div>
      </div>
    </a-modal>

    <!-- Event detail modal (nextcloud + webapp) -->
    <a-modal
      v-model:open="syncModalOpen"
      :title="selectedEventGroup?.label"
      :footer="null"
      :centered="true"
      :width="isMobile ? '92%' : 420"
    >
      <div v-if="selectedEvent">

        <!-- ── Nextcloud event ── -->
        <template v-if="selectedEventGroup?.pipeline === 'nextcloud'">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap">
            <span :style="{ color: eventColor(selectedEvent), fontSize: '20px', fontWeight: 700, lineHeight: 1 }">
              {{ selectedEvent.direction === 'in' ? '▼' : '▲' }}
            </span>
            <span style="font-size: 14px; font-weight: 500">
              {{ selectedEvent.direction === 'in' ? '写入（Nextcloud → DB）' : '写出（DB → Nextcloud）' }}
            </span>
            <a-tag :color="pipelineColor(selectedEventGroup?.pipeline)">{{ selectedEventGroup?.pipeline }}</a-tag>
            <a-badge :status="badgeStatus(selectedEvent.status)" :text="statusLabel(selectedEvent.status)" />
          </div>
          <div style="display: flex; gap: 24px; margin-bottom: 14px; flex-wrap: wrap">
            <div>
              <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 2px">时间</div>
              <div style="font-size: 13px">{{ formatTime(selectedEvent.timestamp) }}</div>
            </div>
            <div>
              <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 2px">记录数</div>
              <div style="font-size: 13px">{{ selectedEvent.record_count }} 条</div>
            </div>
            <div v-if="selectedEvent.conflict_count > 0">
              <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 2px">冲突</div>
              <div style="font-size: 13px; color: #fa8c16">{{ selectedEvent.conflict_count }} 处</div>
            </div>
            <div>
              <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 2px">触发方式</div>
              <div style="font-size: 13px">{{ selectedEvent.trigger === 'webhook' ? 'Webhook' : '定时任务' }}</div>
            </div>
          </div>
          <div style="color: #595959; font-size: 13px; word-break: break-all">{{ selectedEvent.detail }}</div>
        </template>

        <!-- ── Webapp scraper event ── -->
        <template v-else-if="selectedEventGroup?.pipeline === 'webapp'">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap">
            <a-tag :color="pipelineColor(selectedEventGroup?.pipeline)">webapp</a-tag>
            <a-tag color="default" style="font-size: 11px">{{ selectedEvent.task_type }}</a-tag>
            <a-badge :status="badgeStatus(selectedEvent.status)" :text="statusLabel(selectedEvent.status)" />
          </div>

          <!-- Stage timeline -->
          <div style="margin-bottom: 14px">
            <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 8px; font-weight: 500">阶段时间线</div>
            <div style="display: flex; flex-direction: column; gap: 5px">
              <div style="display: flex; gap: 8px; font-size: 12px; align-items: baseline">
                <span style="color: #8c8c8c; width: 56px; flex-shrink: 0">创建</span>
                <span>{{ formatTime(selectedEvent.created_at) }}</span>
              </div>
              <div style="display: flex; gap: 8px; font-size: 12px; align-items: baseline">
                <span style="color: #8c8c8c; width: 56px; flex-shrink: 0">下载完成</span>
                <span>{{ formatTime(selectedEvent.received_at) || '—' }}</span>
              </div>
              <div style="display: flex; gap: 8px; font-size: 12px; align-items: baseline">
                <span style="color: #8c8c8c; width: 56px; flex-shrink: 0">清洗开始</span>
                <span>{{ formatTime(selectedEvent.cleaning_started_at) || '—' }}</span>
              </div>
              <div style="display: flex; gap: 8px; font-size: 12px; align-items: baseline">
                <span style="color: #8c8c8c; width: 56px; flex-shrink: 0">完成</span>
                <span :style="{ color: selectedEvent.status === 'error' ? '#ff4d4f' : 'inherit' }">
                  {{ formatTime(selectedEvent.completed_at) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Row stats -->
          <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; padding: 10px 0; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0">
            <div v-for="stat in scrapeStats(selectedEvent)" :key="stat.label">
              <div style="font-size: 11px; color: #8c8c8c; margin-bottom: 2px">{{ stat.label }}</div>
              <div :style="{ fontSize: '15px', fontWeight: 600, color: stat.color || 'inherit' }">{{ stat.value }}</div>
            </div>
          </div>

          <!-- Error message -->
          <div
            v-if="selectedEvent.error_message"
            style="background: #fff2f0; border: 1px solid #ffccc7; border-radius: 4px; padding: 8px 12px; font-size: 12px; color: #ff4d4f; word-break: break-all"
          >{{ selectedEvent.error_message }}</div>
        </template>

      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RightOutlined } from '@ant-design/icons-vue'
import { useIsMobile } from '../composables/useIsMobile'

const props = defineProps({
  sections: { type: Array, default: () => [] },
})

const isMobile = useIsMobile()
const LABEL_WIDTH = computed(() => (isMobile.value ? 120 : 240))
const MARK_COUNT = computed(() => (isMobile.value ? 3 : 5))

// ── Expand state ─────────────────────────────────────────────────────────────
const expandedGroups = ref({})
function toggle(id) { expandedGroups.value[id] = !expandedGroups.value[id] }
function isExpanded(id) { return !!expandedGroups.value[id] }

// ── Batch detail modal ────────────────────────────────────────────────────────
const modalOpen = ref(false)
const selectedBatch = ref(null)
const selectedGroup = ref(null)
function openDetail(batch, group) {
  selectedBatch.value = batch
  selectedGroup.value = group
  modalOpen.value = true
}

// ── Event detail modal (nextcloud + webapp) ───────────────────────────────────
const syncModalOpen = ref(false)
const selectedEvent = ref(null)
const selectedEventGroup = ref(null)
function openSyncDetail(event, group) {
  selectedEvent.value = event
  selectedEventGroup.value = group
  syncModalOpen.value = true
}

// ── Reactive now ──────────────────────────────────────────────────────────────
const now = ref(Date.now())
let timer
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { clearInterval(timer) })

// ── Group type detection ──────────────────────────────────────────────────────
function isSyncGroup(group) { return Array.isArray(group.events) }

// ── All batches and events (flat, for time range) ─────────────────────────────
const allBatches = computed(() =>
  props.sections.flatMap((s) => s.task_groups.flatMap((g) => g.batches || []))
)
const allEvents = computed(() =>
  props.sections.flatMap((s) => s.task_groups.flatMap((g) => g.events || []))
)

// ── Time range ────────────────────────────────────────────────────────────────
const timeRange = computed(() => {
  const times = []
  allBatches.value.forEach((b) => {
    if (b.created_at) times.push(new Date(b.created_at).getTime())
    if (b.completed_at) times.push(new Date(b.completed_at).getTime())
  })
  allEvents.value.forEach((e) => {
    if (e.timestamp) times.push(new Date(e.timestamp).getTime())
  })
  const hasRunning = allBatches.value.some((b) => b.status === 'running')
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

function rightPct(batch) {
  if (batch.completed_at) return toPercent(batch.completed_at)
  const rightMs = Math.min(now.value, timeRange.value.max)
  return ((rightMs - timeRange.value.min) / totalMs.value) * 100
}

// ── Time marks ───────────────────────────────────────────────────────────────
const timeMarks = computed(() =>
  Array.from({ length: MARK_COUNT.value + 1 }, (_, i) => {
    const t = new Date(timeRange.value.min + (totalMs.value * i) / MARK_COUNT.value)
    return { pos: (i / MARK_COUNT.value) * 100, label: formatTime(t.toISOString()) }
  })
)

// ── Layout ───────────────────────────────────────────────────────────────────
const labelColStyle = computed(() => ({ width: LABEL_WIDTH.value + 'px', flexShrink: 0 }))
const chartColStyle = { flex: 1, overflow: 'hidden' }

function rowStyle(type) {
  return {
    display: 'flex',
    alignItems: 'stretch',
    height: type === 'l1' ? '36px' : type === 'l2' ? '30px' : '20px',
    marginBottom: type === 'l2' ? '2px' : '4px',
    padding: type === 'l1' ? '0 4px' : '0',
  }
}

function gridLineStyle(pos) {
  return {
    position: 'absolute',
    left: pos + '%',
    top: 0, bottom: 0,
    width: '1px',
    background: '#e8e8e8',
    zIndex: 0,
  }
}

// ── Colors ───────────────────────────────────────────────────────────────────
const STATUS_COLORS = {
  running: '#1677ff',
  success: '#52c41a',
  error: '#ff4d4f',
  pending: '#bfbfbf',
}

function pipelineColor(pipeline) {
  return { excel: 'green', db: 'geekblue', email: 'purple', nextcloud: 'cyan', webapp: 'orange' }[pipeline] ?? 'default'
}

function sourceColor(source) {
  return { excel: 'green', db: 'geekblue', email: 'purple', nextcloud: 'cyan', webapp: 'orange' }[source] ?? 'default'
}

function sourceLabel(source) {
  return { excel: 'Excel', db: 'DB', email: 'Email' }[source] ?? source
}

// eventColor: used for vertical indicator line + nextcloud triangle color
function eventColor(event) {
  if (event.status === 'error') return '#ff4d4f'
  // nextcloud has direction; webapp doesn't — both fall through to green for success
  return event.direction === 'in' ? '#1677ff' : '#52c41a'
}

// ── Markers ───────────────────────────────────────────────────────────────────
function markerStyle(event, group) {
  const pos = toPercent(event.timestamp)
  const color = eventColor(event)
  const base = {
    position: 'absolute',
    left: pos + '%',
    top: '50%',
    transform: 'translate(-50%, -50%)',
    cursor: 'pointer',
    zIndex: 2,
  }
  if (group.pipeline === 'nextcloud') {
    const isIn = event.direction === 'in'
    return {
      ...base,
      width: '10px',
      height: '9px',
      background: color,
      clipPath: isIn ? 'polygon(0% 0%, 100% 0%, 50% 100%)' : 'polygon(50% 0%, 100% 100%, 0% 100%)',
    }
  }
  // webapp: circle
  return {
    ...base,
    width: '9px',
    height: '9px',
    background: color,
    borderRadius: '50%',
  }
}

// ── Mini block (L1 for batch groups) ─────────────────────────────────────────
function miniBlockStyle(batch) {
  if (!batch.created_at) return { display: 'none' }
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

function batchUnfilledStyle(batch) {
  return {
    width: (100 - progressPct(batch)) + '%',
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

// ── Group badge ──────────────────────────────────────────────────────────────
function groupBadgeStatus(group) {
  if (isSyncGroup(group)) {
    if (!group.events.length) return 'default'
    return group.events.some((e) => e.status === 'error') ? 'error' : 'success'
  }
  if (group.batches.some((b) => b.status === 'running')) return 'processing'
  if (!group.batches.length) return 'default'
  const last = group.batches.reduce((a, b) =>
    new Date(a.created_at || 0) > new Date(b.created_at || 0) ? a : b
  )
  return badgeStatus(last.status)
}

// ── Webapp modal stats helper ─────────────────────────────────────────────────
function scrapeStats(event) {
  return [
    { label: '接收', value: event.rows_received },
    { label: '写入', value: event.rows_inserted, color: '#52c41a' },
    { label: '更新', value: event.rows_updated, color: '#1677ff' },
    { label: '跳过', value: event.rows_skipped },
    { label: '未匹配', value: event.rows_unmatched, color: event.rows_unmatched > 0 ? '#fa8c16' : undefined },
  ]
}

// ── Formatters ───────────────────────────────────────────────────────────────
function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ja-JP', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
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
.expand-enter-active { animation: expandDown 0.2s ease; }
.expand-leave-active { animation: expandDown 0.15s ease reverse; }
@keyframes expandDown {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
