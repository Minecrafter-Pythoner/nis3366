import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SignupView from '../views/SignupView.vue'
import LoginView from '../views/LoginView.vue'
import FeedView from '../views/FeedView.vue'
import MessagesView from '../views/MessagesView.vue'
import SearchView from '../views/SearchView.vue'
import ProfileView from '../views/ProfileView.vue'
import ForgotPasswdView from '../views/ForgotPasswdView.vue'
import NotifyView from '../views/NotifyView.vue'
import ChatView from '@/views/ChatView.vue'; 
import Topic from '../views/Topic.vue';
import UserHistory from '../views/HistoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView 
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/feed',
      name: 'feed',
      component: FeedView
    },
    {
      path: '/messages',
      name: 'messages',
      component: MessagesView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue') // 懒加载
    },
    {
      path: '/forgotpasswd',
      name: 'forgotpasswd',
      component: ForgotPasswdView
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('../views/Create.vue') 
    },
    {
      path: '/posts/:uuid/:base_floor',
      name: 'Topic',
      component: Topic,
  
    },
    {
      path: '/notify',
      name: 'notify',
      component: NotifyView
    },
    {
      path: '/chat',  // 添加 Chat 路由
      name: 'chat',
      component: ChatView
    },
    {
      path: '/history',
      name: 'history',
      component: UserHistory
    }
  ]
})

export default router
