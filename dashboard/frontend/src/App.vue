<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <span v-if="!collapsed">Yamaguchi</span>
        <span v-else>Y</span>
      </div>
      <a-menu theme="dark" :selected-keys="[currentRoute]" mode="inline">
        <a-menu-item key="dashboard">
          <template #icon><dashboard-outlined /></template>
          <router-link to="/">任务总览</router-link>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 16px; display: flex; align-items: center; justify-content: space-between">
        <span style="font-size: 18px; font-weight: 600">统一任务仪表盘</span>
        <a-tag :color="connected ? 'green' : 'red'">
          {{ connected ? '实时连接中' : '连接断开' }}
        </a-tag>
      </a-layout-header>

      <a-layout-content style="margin: 16px">
        <router-view />
      </a-layout-content>

      <a-layout-footer style="text-align: center; color: #999">
        Yamaguchi Platform Dashboard v0.1.0
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { DashboardOutlined } from '@ant-design/icons-vue'
import { useTaskStore } from './stores/tasks'

const collapsed = ref(false)
const route = useRoute()
const currentRoute = computed(() => route.name || 'dashboard')

const taskStore = useTaskStore()
const connected = computed(() => taskStore.connected)

taskStore.startStream()
</script>

<style>
.logo {
  height: 32px;
  margin: 16px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
