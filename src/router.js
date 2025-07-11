import { createRouter, createWebHistory } from 'vue-router';
import ProductTopPage from './pages/ProductTopPage.vue';

const routes = [
    { path: '/', component: ProductTopPage },
    { path: '/list', component: () => import('./pages/CartListPage.vue') },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
