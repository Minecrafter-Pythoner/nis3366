<template>
    <div class="p-4" style="background-color: rgba(255, 255, 255, 0.7); border: 1px solid rgba(229, 231, 235, 1); border-radius: 0.5rem;">
        <h3 class="mb-6 text-base">热门话题</h3>
        <div class="space-y-4">
            <div v-for="post in posts" :key="post.uuid" @click="goToTopic(post.uuid, post.title, post.tag_lst)"
            class="cursor-pointer p-4 bg-white border border-gray-200 rounded-lg shadow-md">
                <div class="flex justify-between items-center">
                    <h2 class="text-lg font-bold">{{ post.title }}</h2> <!-- 显示帖子标题 -->
                    <span class="text-xs text-gray-400">{{ post.tag_lst.join(', ') }}</span> <!-- 显示标签 -->
                </div>
            </div>

        </div>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    data() {
        return {
            posts: [] // 存储热门帖子数据
        };
    },
    mounted() {
        this.getTrend(); // 在组件挂载时获取热门帖子
    },
    methods: {
        // 从后端获取热门帖子列表
        getTrend() {
            axios
                .get('/api/posts/hot')
                .then(response => {
                    // 去掉每个标签中的引号
                    this.posts = response.data.posts.map(post => ({
                        ...post,
                        tag_lst: post.tag_lst.map(tag => tag.replace(/['"]+/g, ''))
                    }));
                })
                .catch(error => {
                    console.error('Error fetching hot posts:', error);
                });
        },

        // 跳转到帖子详情页面
        goToTopic(uuid, title, tag_lst) {
            this.$router.push({ name: 'Topic', params: { uuid, base_floor: 1 }, query: { title, tag_lst } });
        }
    },
};
</script>

<style scoped>
/* 可以根据需要添加样式 */
</style>
