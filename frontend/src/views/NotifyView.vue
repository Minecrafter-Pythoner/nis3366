<template>
  <div class="app-container max-w-7xl mx-auto grid grid-cols-5 gap-4">
      <!-- 可能认识的人部分 -->
      <aside class="col-span-1 space-y-4">
          <PeopleYouMayKnow />
      </aside>

      <!-- 主体部分：回复列表 -->
      <div class="main-center col-span-3 space-y-4">
          <h2 class="text-2xl font-semibold">我的帖子回复</h2>

          <!-- 回复列表 -->
          <div v-for="reply in replies" :key="reply.id" class="p-4 bg-white border border-gray-200 rounded-lg shadow-md">
              <div><strong>{{ reply.user.name }}</strong>: {{ reply.body }}</div>
              <div v-if="reply.image">
                  <img :src="reply.image" alt="回复图片" class="mt-2 max-w-full" />
              </div>
              <div class="text-sm text-gray-500">{{ reply.createdAt }}</div>
          </div>
      </div>

      <!-- 热门话题部分 -->
      <div class="main-right col-span-1 space-y-4">
          <Trends />
      </div>
  </div>
</template>

<script>
import axios from 'axios';
import PeopleYouMayKnow from '../components/PeopleYouMayKnow.vue';
import Trends from '../components/Trends.vue';

export default {
  name: "RepliesView",
  components: {
      PeopleYouMayKnow,
      Trends,
  },
  data() {
      return {
          replies: [], // 存储回复
      };
  },
  mounted() {
      this.getReplies(); // 页面加载时获取回复
  },
  methods: {
      // 从后端获取回复列表
      getReplies() {
          axios
              .get('/api/replies/') // 确保这里的 API 路径是正确的
              .then(response => {
                  this.replies = response.data; // 将获取的回复数据存储到replies数组中
              })
              .catch(error => {
                  console.log('错误', error);
              });
      },
  }
}
</script>

<style scoped>
.app-container {
  background-image: url('@/assets/bg.jpg'); 
  background-size: cover; 
  background-position: center;
  min-height: 100vh;
}

img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin-top: 10px;
}
</style>
