<template>
    <div>
        <!-- 按钮来触发模拟发帖 -->
        <button @click="addPost" class="inline-block py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition">
            发布模拟帖子
        </button>

        <!-- 显示模拟帖子内容 -->
    </div>
</template>

<script>
export default {
    data() {
        return {
            // 预设的10条模拟发帖内容
            samplePosts: [
                { id: 1001, title: '探索新的编程语言', body: '在这个快速发展的时代，学习新技术是至关重要的。最近我开始研究 Rust，这是一种内存安全的编程语言。你们有推荐的学习资源吗？', date: '2024年10月18日' },
                { id: 1002, title: '旅行的意义', body: '旅行不仅是对未知的探索，更是对自我的重新发现。去过的每一个地方都留下了难忘的回忆，你们的旅行故事是什么？', date: '2024年10月17日' },
                { id: 1003, title: '健康生活方式', body: '保持健康的生活方式变得越来越重要。每天锻炼、健康饮食和保持良好作息是我的秘诀。你们有什么健康小贴士吗？', date: '2024年10月16日' },
                { id: 1004, title: '学习如何学习', body: '最近读了一本关于“学习如何学习”的书，感觉很有启发。学习的关键不在于学习时间的长短，而在于学习方法。你们有什么高效学习的方法吗？', date: '2024年10月15日' },
                { id: 1005, title: '工作与生活的平衡', body: '如何在快节奏的工作和生活之间找到平衡？我发现适时地放松和自我反思对保持身心健康很重要。你们是怎么做的？', date: '2024年10月14日' },
                { id: 1006, title: '阅读的乐趣', body: '最近开始了《百年孤独》的阅读之旅。每一本书都是一扇通向新世界的大门。你们最近在读什么书？', date: '2024年10月13日' },
                { id: 1007, title: '电影推荐', body: '周末看了一部老电影《肖申克的救赎》，让我对人生和自由有了新的理解。你们有推荐的好电影吗？', date: '2024年10月12日' },
                { id: 1008, title: '编程项目', body: '最近完成了一个基于 Vue.js 的个人项目，感觉收获颇多。你们在做什么有趣的编程项目？', date: '2024年10月11日' },
                { id: 1009, title: '美食探索', body: '作为一个吃货，我最近尝试了几道新的菜式，发现了几家隐藏的美食小店。你们有什么推荐的美食？', date: '2024年10月10日' },
                { id: 1010, title: '音乐分享', body: '最近迷上了古典音乐，尤其是贝多芬的交响曲。音乐能带来心灵的平静和力量。你们最近在听什么音乐？', date: '2024年10月9日' }
            ],
            posts: [] // 存储已发布的帖子
        };
    },

    methods: {
        // 模拟发布帖子
        addPost() {
            const newPost = this.samplePosts.shift(); // 从数组中取出一个帖子
            if (newPost) {
                this.posts.push(newPost); // 将新帖子添加到已发布列表
                this.$emit('post-added', newPost); // 发射 'post-added' 事件并传递帖子给父组件
            } else {
                alert('没有更多的模拟帖子了'); // 当所有模拟帖子都已发布时提示
            }
        }
    }
};
</script>

<style scoped>
button {
    margin-top: 10px;
}

.bg-gray-100 {
    background-color: #f7fafc; 
}

.border {
    border: 1px solid #e2e8f0; 
}

.font-semibold {
    font-weight: 600; 
}

.text-lg {
    font-size: 1.125rem; 
}

.text-gray-800 {
    color: #2d3748; 
}

.text-gray-700 {
    color: #4a5568; 
}

.text-gray-500 {
    color: #a0aec0; 
}
</style>
