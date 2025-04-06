<template>
    <div class="max-w-7xl mx-auto grid grid-cols-4 gap-4">
        <div class="main-left col-span-3">
            <div class="bg-white border border-gray-200 rounded-lg">
                <form @submit.prevent="submitForm" class="p-4 flex space-x-4">
                    <input v-model="query" type="search" class="p-4 w-full bg-gray-100 rounded-lg" placeholder="输入#搜索tag，直接输入搜索标题">
                    <button class="inline-block py-4 px-6 bg-purple-600 text-white rounded-lg">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                            stroke="currentColor" class="w-6 h-6">
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"></path>
                        </svg>
                    </button>
                </form>
            </div>
            <PostList :posts="posts" :selectedTag.sync="selectedTag" />
        </div>
        <div class="main-right col-span-1 space-y-4">
            <PeopleYouMayKnow />
            <Trends />
        </div>
    </div>
</template>

<script>
import PeopleYouMayKnow from '../components/PeopleYouMayKnow.vue';
import Trends from '../components/Trends.vue';
import PostList from '../components/PostList.vue';
import axios from 'axios';

export default {
    name: "SearchView",
    components: {
        PeopleYouMayKnow,
        Trends,
        PostList,
    },
    data() {
        return {
            query: '',
            posts: [],
            selectedTag: null,
        };
    },
    methods: {
        async submitForm() {
            const isTagSearch = this.query.startsWith("#");
            const apiUrl = isTagSearch ? '/api/searchtag' : '/api/search';
            // 将标签添加引号发送给后端
            const searchParam = isTagSearch ? { tag: `"${this.query.slice(1)}"` } : { keyword: this.query };

            try {
                const response = await axios.get(apiUrl, { params: searchParam });
                // 去除返回数据中的引号
                this.posts = response.data.posts.map(post => ({
                    ...post,
                    tag_lst: post.tag_lst.map(tag => tag.replace(/['"]+/g, ''))
                }));
            } catch (error) {
                console.error('搜索失败:', error);
            }
        }
    }

}
</script>
