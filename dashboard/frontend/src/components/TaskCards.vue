<template>
  <div>
    <a-empty v-if="sections.length === 0" description="暂无任务数据" />

    <div v-for="(section, sIdx) in sections" :key="section.id">

      <!-- Section divider -->
      <div
        :style="{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginTop: sIdx === 0 ? '0' : '16px',
          marginBottom: '8px',
        }"
      >
        <span style="font-size: 12px; font-weight: 600; color: #595959; white-space: nowrap">
          {{ section.label }}
        </span>
        <div style="flex: 1; height: 1px; background: #e8e8e8"></div>
      </div>

      <!-- Task group cards -->
      <div
        v-for="group in section.task_groups"
        :key="group.id"
        style="border: 1px solid #e8e8e8; border-radius: 6px; margin-bottom: 8px; overflow: hidden"
      >
        <!-- L1: Group header -->
        <div
          style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            cursor: pointer;
            background: #fafafa;
            user-select: none;
          "
          @click="toggle(group.id)"
        >
          <div style="display: flex; align-items: center; gap: 8px; overflow: hidden; flex: 1; min-width: 0">
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
              style="flex-shrink: 0; margin: 0; font-size: 10px; padding: 0 5px; line-height: 18px"
            >{{ group.pipeline }}</a-tag>
            <span style="font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
              {{ group.label }}
            </span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0; margin-left: 8px">
            <span style="font-size: 11px; color: #8c8c8c">
              {{ isSyncGroup(group)
                ? (group.events.length ? group.events.length + ' 次记录' : '暂无记录')
                : (group.batches.length ? group.batches.length + ' 批次' : '暂无记录') }}
            </span>
            <a-badge :status="groupBadgeStatus(group)" />
          </div>
        </div>

        <!-- L2: Expanded content -->
        <Transition name="slide">
          <div v-if="isExpanded(group.id)">

            <!-- ── Event list (nextcloud / webapp) ── -->
            <template v-if="isSyncGroup(group)">
              <div v-if="group.events.length === 0" style="padding: 12px 16px; color: #bfbfbf; font-size: 13px">
                暂无记录
              </div>

              <div
                v-for="(event, eIdx) in group.events"
                :key="event.id"
                :style="{
                  padding: '10px 16px 10px 32px',
                  borderTop: '1px solid #f0f0f0',
                  background: eIdx % 2 === 0 ? '#fff' : '#fafafa',
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                }"
                @click="openSyncDetail(event, group)"
                @mouseenter="(e) => (e.currentTarget.style.background = '#f0f5ff')"
                @mouseleave="(e) => (e.currentTarget.style.background = eIdx % 2 === 0 ? '#fff' : '#fafafa')"
              >
                <!-- Nextcloud event row -->
                <template v-if="group.pipeline === 'nextcloud'">
                  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap">
                    <span :style="{ color: eventColor(event), fontSize: '14px', fontWeight: 700, lineHeight: 1 }">
                      {{ event.direction === 'in' ? '▼' : '▲' }}
                    </span>
                    <span style="font-size: 12px; font-weight: 500; color: #262626">
                      {{ event.direction === 'in' ? '写入' : '写出' }}
                    </span>
                    <a-tag
                      :color="event.trigger === 'webhook' ? 'blue' : 'default'"
                      style="margin: 0; font-size: 10px; padding: 0 5px; line-height: 16px"
                    >{{ event.trigger === 'webhook' ? 'webhook' : '定时' }}</a-tag>
                    <a-badge :status="badgeStatus(event.status)" :text="statusLabel(event.status)" />
                    <span style="font-size: 11px; color: #8c8c8c; margin-left: auto">
                      {{ formatTime(event.timestamp) }}
                    </span>
                  </div>
                  <div style="font-size: 12px; color: #595959; margin-top: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap" :title="event.detail">
                    {{ event.record_count }} 条记录{{ event.conflict_count > 0 ? ' · ' + event.conflict_count + ' 处冲突' : '' }}
                    {{ event.detail ? ' · ' + event.detail : '' }}
                  </div>
                </template>

                <!-- Webapp scraper event row -->
                <template v-else>
                  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap">
                    <a-badge :status="badgeStatus(event.status)" :text="statusLabel(event.status)" />
                    <span style="font-size: 11px; color: #8c8c8c; margin-left: auto">
                      {{ formatTime(event.timestamp) }}
                    </span>
                  </div>
                  <div style="font-size: 12px; color: #595959; margin-top: 5px">
                    <template v-if="event.status === 'success'">
                      写入 {{ event.rows_inserted }} · 更新 {{ event.rows_updated }} · 接收 {{ event.rows_received }}
                      <span v-if="event.rows_unmatched > 0" style="color: #fa8c16"> · 未匹配 {{ event.rows_unmatched }}</span>
                    </template>
                    <template v-else>
                      <span style="color: #ff4d4f">{{ event.error_message || '处理失败' }}</span>
                    </template>
                  </div>
                </template>
              </div>
            </template>

            <!-- ── Batch list (excel / db / email) ── -->
            <template v-else>
              <div v-if="group.batches.length === 0" style="padding: 12px 16px; color: #bfbfbf; font-size: 13px">
                该任务暂无批次记录
              </div>

              <div
                v-for="(batch, bIdx) in group.batches"
                :key="batch.id"
                :style="{
                  padding: '10px 16px 10px 32px',
                  borderTop: '1px solid #f0f0f0',
                  background: bIdx % 2 === 0 ? '#fff' : '#fafafa',
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                }"
                @click="openDetail(batch, group)"
                @mouseenter="(e) => (e.currentTarget.style.background = '#f0f5ff')"
                @mouseleave="(e) => (e.currentTarget.style.background = bIdx % 2 === 0 ? '#fff' : '#fafafa')"
              >
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap">
                  <a-tag
                    :color="sourceColor(batch.source)"
                    style="margin: 0; font-size: 10px; padding: 0 5px; line-height: 16px"
                  >{{ sourceLabel(batch.source) }}</a-tag>
                  <a-badge :status="badgeStatus(batch.status)" :text="statusLabel(batch.status)" />
                  <span style="font-size: 11px; color: #8c8c8c; margin-left: auto">
                    {{ batch.created_at ? formatTime(batch.created_at) : '—' }} →
                    {{ batch.completed_at ? formatTime(batch.completed_at) : (batch.created_at ? '进行中' : '等待触发') }}
                  </span>
                </div>

                <div
                  style="font-size: 12px; color: #595959; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap"
                  :title="batch.detail"
                >{{ batch.detail }}</div>

                <div v-if="batch.total_jobs > 0" style="display: flex; align-items: center; gap: 8px">
                  <div style="flex: 1; height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden">
                    <div
                      :style="{
                        width: progressPct(batch) + '%',
                        height: '100%',
                        background: STATUS_COLORS[batch.status] || '#bfbfbf',
                        borderRadius: '3px',
                        transition: 'width 0.5s ease',
                      }"
                    ></div>
                  </div>
                  <span style="font-size: 11px; color: #8c8c8c; white-space: nowrap; flex-shrink: 0">
                    {{ batch.completed_jobs }}/{{ batch.total_jobs }}
                  </span>
                </div>
              </div>
            </template>

          </div>
        </Transition>
      </div>

    </div><!-- end section loop -->

    <!-- Batch detail modal -->
    <a-modal
      v-model:open="modalOpen"
      :title="selectedGroup?.label"
      :footer="null"
      :centered="true"
    >
      <div v-if="selectedBatch">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap">
          <a-tag :color="sourceColor(selectedBatch.source)">{{ sourceLabel(selectedBatch.source) }}</a-tag>
          <a-tag :color="pipelineColor(selectedGroup?.pipeline)">{{ selectedGroup?.pipeline }}</a-tag>
          <a-badge :status="badgeStatus(selectedBatch.status)" :text="statusLabel(selectedBatch.status)" />
        </div>
        <div style="color: #8c8c8c; font-size: 13px; margin-bottom: 14px">
          {{ selectedBatch.created_at ? formatTime(selectedBatch.created_at) : '—' }} →
          {{ selectedBatch.completed_at ? formatTime(selectedBatch.completed_at) : (selectedBatch.created_at ? '进行中' : '等待触发') }}
        </div>
        <div v-if="selectedBatch.total_jobs > 0" style="margin-bottom: 14px">
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
import { ref } from 'vue'
import { RightOutlined } from '@ant-design/icons-vue'

defineProps({
  sections: { type: Array, default: () => [] },
})

const expandedGroups = ref({})
function toggle(id) { expandedGroups.value[id] = !expandedGroups.value[id] }
function isExpanded(id) { return !!expandedGroups.value[id] }

function isSyncGroup(group) { return Array.isArray(group.events) }

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

function eventColor(event) {
  if (event.status === 'error') return '#ff4d4f'
  return event.direction === 'in' ? '#1677ff' : '#52c41a'
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

function scrapeStats(event) {
  return [
    { label: '接收', value: event.rows_received },
    { label: '写入', value: event.rows_inserted, color: '#52c41a' },
    { label: '更新', value: event.rows_updated, color: '#1677ff' },
    { label: '跳过', value: event.rows_skipped },
    { label: '未匹配', value: event.rows_unmatched, color: event.rows_unmatched > 0 ? '#fa8c16' : undefined },
  ]
}

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
.slide-enter-active { animation: slideDown 0.2s ease; }
.slide-leave-active { animation: slideDown 0.15s ease reverse; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-6px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
