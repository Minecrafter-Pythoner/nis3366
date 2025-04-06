<template>
    <div>
        <div v-for="post in posts" :key="post.uuid" @click="goToTopic(post.uuid, post.title, post.tag_lst)"
            class="cursor-pointer p-4 bg-white border border-gray-200 rounded-lg shadow-md">
            <p class="text-gray-600">发帖人: {{ post.nickname }}</p>
            <h2 class="text-lg font-bold">{{ post.title }}</h2>

            <!-- 标签列表 -->
            <div class="tags mt-2 flex space-x-2">
                <span v-for="tag in post.tag_lst" :key="tag" class="tag text-xs font-semibold px-2 py-1 rounded-full"
                    :style="{ backgroundColor: tagColors[tag] || tagColors.default }" @click.stop="filterByTag(tag)">
                    {{ tag }}
                </span>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        posts: Array,
        selectedTag: {
            type: String,
            default: null
        }
    },
    data() {
        return {
            tagColors: {
                "share": "#38b2ac",
                "ask": "#f6ad55",
                "advertise": "#ed64a6",
                "aboutus": "#667eea",
                "default": "#a0aec0",
            }
        };
    },
    methods: {
        goToTopic(uuid, title, tag_lst) {
            this.$router.push({ name: 'Topic', params: { uuid, base_floor: 1 }, query: { title, tag_lst } });
        },
        filterByTag(tag) {
            this.$emit('update:selectedTag', tag); // 发送事件更新父组件中的 selectedTag
        }
    }
}
</script>

<style scoped>
.tag {
    color: #fff;
    cursor: pointer;
    transition: background-color 0.2s;
}

.tag:hover {
    opacity: 0.8;
}
</style>
