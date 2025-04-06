<template>
  <!-- 哥特风格加载层 -->
  <div v-if="loading" class="gothic-loading">
      <div class="loading-container">
          <img src="@/assets/home.jpg" alt="Gothic Loading" class="gothic-image">
          <div class="loading-text">Loading...</div>
      </div>
  </div>
  <!-- 主内容 -->
  <div v-else class="app-container max-w-7xl mx-auto grid grid-cols-5 gap-4">
      <aside class="col-span-1 space-y-4">
          <PeopleYouMayKnow />
      </aside>
      <div class="main-center col-span-3 space-y-4">
          <!-- 标签筛选信息 -->
          <div v-if="selectedTag" class="mb-4">
              <button @click="clearTagFilter" class="py-1 px-4 bg-gray-300 rounded-full">
                  清除标签: {{ selectedTag }}
              </button>
          </div>
          <!-- 帖子列表容器 -->
          <div class="post-list">
              <PostList :posts="filteredPosts" @update:selectedTag="setSelectedTag" />
          </div>
      </div>
      <div class="main-right col-span-1 space-y-4">
          <Trends />
      </div>
  </div>
</template>

<script>
import axios from 'axios';
import PeopleYouMayKnow from '../components/PeopleYouMayKnow.vue';
import Trends from '../components/Trends.vue';
import PostList from '../components/PostList.vue';

export default {
  name: "FeedView",
  components: {
      PeopleYouMayKnow,
      Trends,
      PostList,
  },
  data() {
      return {
          posts: [], // 存储从后端获取的帖子
          selectedTag: null, // 当前选中的标签
          loading: true, // 加载状态
      };
  },
  computed: {
      // 根据 selectedTag 筛选帖子
      filteredPosts() {
          if (this.selectedTag) {
              return this.posts.filter(post => post.tag_lst.includes(this.selectedTag));
          }
          return this.posts;
      }
  },
  mounted() {
      // 模拟加载效果，2秒后显示内容
      setTimeout(() => {
          this.loading = false;
      }, 2000);
      
      this.getFeed(); // 页面加载时获取帖子
  },
  methods: {
      // 从后端获取帖子列表
      getFeed() {
          axios.get('/api/posts/')
              .then(response => {
                  // 去掉每个标签中的引号
                  this.posts = response.data.posts.map(post => ({
                      ...post,
                      tag_lst: post.tag_lst.map(tag => tag.replace(/['"]+/g, ''))
                  }));
              })
              .catch(error => console.log('error', error));
      },
      // 设置选中的标签
      setSelectedTag(tag) {
          this.selectedTag = tag;
      },
      // 清除标签筛选
      clearTagFilter() {
          this.selectedTag = null;
      }
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

.post-list {
  max-height: 1280px; /* 设置最大高度 */
  overflow-y: auto;  /* 允许垂直滚动 */
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.534); /* 背景色可以根据需要调整 */
  border-radius: 10px; /* 圆角 */
  box-shadow: 0 2px 10px rgba(41, 179, 243, 0.5); /* 阴影效果 */
}

/* 哥特风格加载效果 */
.gothic-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-container {
  position: relative;
  text-align: center;
}

.gothic-image {
  max-width: 80%;
  max-height: 80vh;
  opacity: 0.8;
  filter: grayscale(30%) contrast(120%) sepia(20%);
  box-shadow: 0 0 30px rgba(128, 0, 128, 0.6);
  border: 2px solid #441144;
  animation: pulse 2s infinite, flicker 4s infinite;
}

.loading-text {
  position: absolute;
  bottom: -40px;
  left: 0;
  right: 0;
  margin: auto;
  color: #c9a0dc;
  font-family: 'Times New Roman', serif;
  font-size: 24px;
  text-transform: uppercase;
  letter-spacing: 6px;
  animation: glow 1.5s ease-in-out infinite alternate;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}

@keyframes glow {
  from { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #c9a0dc, 0 0 20px #c9a0dc; }
  to { text-shadow: 0 0 10px #fff, 0 0 15px #e60073, 0 0 20px #e60073, 0 0 25px #e60073; }
}

@keyframes flicker {
  0%, 100% { opacity: 0.8; }
  3%, 9%, 15%, 25% { opacity: 0.75; }
  7%, 17%, 23% { opacity: 0.9; }
}
</style>