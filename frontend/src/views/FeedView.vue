<template>
    <div class="app-container max-w-7xl mx-auto grid grid-cols-5 gap-4">
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
</style>
