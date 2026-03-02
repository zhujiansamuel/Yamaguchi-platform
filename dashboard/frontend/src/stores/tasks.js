import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref([])
  const connected = ref(false)
  const lastUpdated = ref(null)
  let eventSource = null

  function startStream() {
    if (eventSource) return

    eventSource = new EventSource('/api/tasks/stream')

    eventSource.onopen = () => {
      connected.value = true
    }

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      tasks.value = data.tasks
      lastUpdated.value = data.timestamp
      connected.value = true
    }

    eventSource.onerror = () => {
      connected.value = false
      // Browser automatically retries SSE on error; just update status
    }
  }

  function stopStream() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
      connected.value = false
    }
  }

  return { tasks, connected, lastUpdated, startStream, stopStream }
})
