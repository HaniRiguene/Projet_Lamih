// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import MainPage from '@/views/MainPage.vue';
import AddForm from '@/views/AddForm.vue';
import ModifyForm from '@/views/ModifyForm.vue';
import DeleteForm from '@/views/DeleteForm.vue';

const routes = [
  { path: '/', component: MainPage },
  { path: '/add', component: AddForm },
  { path: '/modify', component: ModifyForm },
  { path: '/delete', component: DeleteForm }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
