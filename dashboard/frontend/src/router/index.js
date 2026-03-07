import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import MailView from '../views/MailView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
  },
  {
    path: '/mail',
    name: 'mail',
    component: MailView,
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
