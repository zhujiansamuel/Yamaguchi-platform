<template>
  <div>
    <!-- Account tabs -->
    <a-segmented
      v-model:value="currentAccount"
      :options="accountOptions"
      style="margin-bottom: 12px"
    />

    <!-- Folder toggle -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px">
      <a-radio-group v-model:value="currentFolder" button-style="solid" size="small">
        <a-radio-button value="inbox">受信トレイ</a-radio-button>
        <a-radio-button value="sent">送信済み</a-radio-button>
      </a-radio-group>
      <div style="display: flex; gap: 8px">
        <a-button type="primary" @click="showCompose = true">
          <template #icon><edit-outlined /></template>
          新規作成
        </a-button>
        <a-button @click="fetchMessages">
          <template #icon><reload-outlined /></template>
          更新
        </a-button>
      </div>
    </div>

    <!-- Main content: left-right split -->
    <div :style="layoutStyle">
      <!-- Left: message list -->
      <a-card
        :style="listStyle"
        :body-style="{ padding: 0 }"
        size="small"
      >
        <a-spin :spinning="loading">
          <div
            v-for="msg in messages"
            :key="msg.uid"
            :style="messageItemStyle(msg)"
            @click="selectMessage(msg)"
          >
            <div style="display: flex; align-items: center; gap: 8px">
              <a-badge v-if="!msg.seen" color="blue" />
              <span style="font-weight: 500; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                {{ currentFolder === 'inbox' ? msg.from : msg.to }}
              </span>
              <paper-clip-outlined v-if="msg.has_attachment" style="color: #999" />
            </div>
            <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #333; margin-top: 4px">
              {{ msg.subject || '(件名なし)' }}
            </div>
            <div style="font-size: 12px; color: #999; margin-top: 2px">
              {{ formatDate(msg.date) }}
            </div>
          </div>
          <a-empty v-if="!loading && messages.length === 0" :image="simpleImage" description="メールなし" style="padding: 40px 0" />
        </a-spin>
        <!-- Pagination -->
        <div v-if="totalMessages > perPage" style="padding: 8px; text-align: center; border-top: 1px solid #f0f0f0">
          <a-pagination
            v-model:current="currentPage"
            :total="totalMessages"
            :page-size="perPage"
            size="small"
            :show-size-changer="false"
            @change="fetchMessages"
          />
        </div>
      </a-card>

      <!-- Right: message detail -->
      <a-card
        :style="detailStyle"
        size="small"
      >
        <template v-if="selectedDetail">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="差出人">{{ selectedDetail.from }}</a-descriptions-item>
            <a-descriptions-item label="宛先">{{ selectedDetail.to }}</a-descriptions-item>
            <a-descriptions-item v-if="selectedDetail.cc" label="CC">{{ selectedDetail.cc }}</a-descriptions-item>
            <a-descriptions-item label="件名">{{ selectedDetail.subject }}</a-descriptions-item>
            <a-descriptions-item label="日時">{{ formatDate(selectedDetail.date) }}</a-descriptions-item>
          </a-descriptions>

          <!-- Attachments -->
          <div v-if="selectedDetail.attachments && selectedDetail.attachments.length" style="margin-top: 12px">
            <span style="font-weight: 500; margin-right: 8px">添付ファイル:</span>
            <a-tag
              v-for="att in selectedDetail.attachments"
              :key="att.part"
              color="blue"
              style="cursor: pointer; margin-bottom: 4px"
              @click="downloadAttachment(att)"
            >
              <paper-clip-outlined /> {{ att.filename }} ({{ formatSize(att.size) }})
            </a-tag>
          </div>

          <!-- Body -->
          <a-divider style="margin: 12px 0" />
          <div v-if="selectedDetail.body_html" v-html="selectedDetail.body_html" class="mail-body" />
          <pre v-else class="mail-body-text">{{ selectedDetail.body_text }}</pre>

          <!-- Actions -->
          <a-divider style="margin: 12px 0" />
          <a-space>
            <a-button size="small" @click="replyTo">
              返信
            </a-button>
            <a-popconfirm title="このメールを削除しますか？" ok-text="削除" cancel-text="キャンセル" @confirm="deleteSelected">
              <a-button size="small" danger>
                削除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
        <a-empty v-else :image="simpleImage" description="メールを選択してください" style="padding: 60px 0" />
      </a-card>
    </div>

    <!-- Compose modal -->
    <a-modal
      v-model:open="showCompose"
      title="メール作成"
      :width="640"
      :footer="null"
      destroy-on-close
    >
      <a-form :model="composeForm" layout="vertical" @finish="handleSend">
        <a-form-item label="差出人" name="from_account" :rules="[{ required: true }]">
          <a-select v-model:value="composeForm.from_account">
            <a-select-option v-for="acc in accounts" :key="acc.key" :value="acc.key">
              {{ acc.address }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="宛先" name="to" :rules="[{ required: true, message: '宛先を入力してください' }]">
          <a-select
            v-model:value="composeForm.to"
            mode="tags"
            placeholder="メールアドレスを入力"
            :token-separators="[',', ' ']"
          />
        </a-form-item>
        <a-form-item label="CC" name="cc">
          <a-select
            v-model:value="composeForm.cc"
            mode="tags"
            placeholder="CC (任意)"
            :token-separators="[',', ' ']"
          />
        </a-form-item>
        <a-form-item label="件名" name="subject" :rules="[{ required: true, message: '件名を入力してください' }]">
          <a-input v-model:value="composeForm.subject" />
        </a-form-item>
        <a-form-item label="本文" name="body" :rules="[{ required: true, message: '本文を入力してください' }]">
          <a-textarea v-model:value="composeForm.body" :rows="10" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="sending">送信</a-button>
            <a-button @click="showCompose = false">キャンセル</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { EditOutlined, ReloadOutlined, PaperClipOutlined } from '@ant-design/icons-vue'
import { message as antMessage, Empty } from 'ant-design-vue'
import { useIsMobile } from '../composables/useIsMobile'

const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE
const isMobile = useIsMobile()

// --- State ---
const accounts = ref([])
const currentAccount = ref('')
const currentFolder = ref('inbox')
const messages = ref([])
const totalMessages = ref(0)
const currentPage = ref(1)
const perPage = 20
const loading = ref(false)
const selectedDetail = ref(null)
const loadingDetail = ref(false)
const showCompose = ref(false)
const sending = ref(false)

const composeForm = reactive({
  from_account: 'contact',
  to: [],
  cc: [],
  subject: '',
  body: '',
})

const accountOptions = computed(() =>
  accounts.value.map((a) => ({ label: a.key, value: a.key }))
)

// --- Layout styles ---
const layoutStyle = computed(() => ({
  display: 'flex',
  flexDirection: isMobile.value ? 'column' : 'row',
  gap: '12px',
}))

const listStyle = computed(() => ({
  width: isMobile.value ? '100%' : '380px',
  flexShrink: 0,
  maxHeight: isMobile.value ? '400px' : 'calc(100vh - 240px)',
  overflowY: 'auto',
}))

const detailStyle = computed(() => ({
  flex: 1,
  maxHeight: isMobile.value ? 'none' : 'calc(100vh - 240px)',
  overflowY: 'auto',
}))

function messageItemStyle(msg) {
  const isSelected = selectedDetail.value && selectedDetail.value.uid === msg.uid
  return {
    padding: '10px 12px',
    borderBottom: '1px solid #f0f0f0',
    cursor: 'pointer',
    background: isSelected ? '#e6f4ff' : (msg.seen ? '#fff' : '#fafafa'),
  }
}

// --- API calls ---
const API_BASE = '/api/mail'

async function fetchAccounts() {
  try {
    const res = await fetch(`${API_BASE}/accounts`)
    accounts.value = await res.json()
    if (accounts.value.length && !currentAccount.value) {
      currentAccount.value = accounts.value[0].key
    }
  } catch (e) {
    antMessage.error('アカウント取得に失敗しました')
  }
}

async function fetchMessages() {
  if (!currentAccount.value) return
  loading.value = true
  selectedDetail.value = null
  try {
    const endpoint = currentFolder.value === 'sent' ? 'sent' : 'inbox'
    const res = await fetch(
      `${API_BASE}/${currentAccount.value}/${endpoint}?page=${currentPage.value}&per_page=${perPage}`
    )
    const data = await res.json()
    messages.value = data.messages || []
    totalMessages.value = data.total || 0
  } catch (e) {
    antMessage.error('メール取得に失敗しました')
    messages.value = []
  } finally {
    loading.value = false
  }
}

async function selectMessage(msg) {
  loadingDetail.value = true
  try {
    const folder = currentFolder.value === 'sent' ? 'Sent' : 'INBOX'
    const res = await fetch(
      `${API_BASE}/${currentAccount.value}/message/${msg.uid}?folder=${folder}`
    )
    selectedDetail.value = await res.json()
    // Mark as read in list
    msg.seen = true
  } catch (e) {
    antMessage.error('メール詳細取得に失敗しました')
  } finally {
    loadingDetail.value = false
  }
}

function downloadAttachment(att) {
  const uid = selectedDetail.value.uid
  const url = `${API_BASE}/${currentAccount.value}/attachment/${uid}/${att.part}`
  window.open(url, '_blank')
}

async function handleSend() {
  sending.value = true
  try {
    const res = await fetch(`${API_BASE}/${composeForm.from_account}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to: composeForm.to,
        cc: composeForm.cc.length ? composeForm.cc : null,
        subject: composeForm.subject,
        body: composeForm.body,
      }),
    })
    if (!res.ok) throw new Error('Send failed')
    antMessage.success('メールを送信しました')
    showCompose.value = false
    resetCompose()
  } catch (e) {
    antMessage.error('送信に失敗しました')
  } finally {
    sending.value = false
  }
}

async function deleteSelected() {
  if (!selectedDetail.value) return
  try {
    const folder = currentFolder.value === 'sent' ? 'Sent' : 'INBOX'
    const res = await fetch(`${API_BASE}/${currentAccount.value}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uids: [selectedDetail.value.uid], folder }),
    })
    if (!res.ok) throw new Error('Delete failed')
    antMessage.success('メールを削除しました')
    selectedDetail.value = null
    fetchMessages()
  } catch (e) {
    antMessage.error('削除に失敗しました')
  }
}

function replyTo() {
  if (!selectedDetail.value) return
  composeForm.from_account = currentAccount.value
  composeForm.to = [selectedDetail.value.from.replace(/.*<(.+)>.*/, '$1')]
  composeForm.cc = []
  composeForm.subject = selectedDetail.value.subject.startsWith('Re:')
    ? selectedDetail.value.subject
    : `Re: ${selectedDetail.value.subject}`
  composeForm.body = `\n\n--- Original Message ---\n${selectedDetail.value.body_text || ''}`
  showCompose.value = true
}

function resetCompose() {
  composeForm.from_account = 'contact'
  composeForm.to = []
  composeForm.cc = []
  composeForm.subject = ''
  composeForm.body = ''
}

// --- Helpers ---
function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// --- Watchers ---
watch(currentAccount, () => {
  currentPage.value = 1
  fetchMessages()
})

watch(currentFolder, () => {
  currentPage.value = 1
  fetchMessages()
})

onMounted(async () => {
  await fetchAccounts()
  fetchMessages()
})
</script>

<style scoped>
.mail-body {
  word-break: break-word;
  line-height: 1.6;
  font-size: 14px;
}
.mail-body :deep(img) {
  max-width: 100%;
  height: auto;
}
.mail-body-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}
</style>
