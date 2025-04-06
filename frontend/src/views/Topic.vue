<template>
    <div class="topic-container max-w-7xl mx-auto p-12 bg-white border border-gray-200 rounded-lg">
        <!-- 帖子标题部分 -->
        <div class="topic-header mb-6 flex items-center justify-between">
            <h1 class="text-3xl font-bold">{{ $route.query.title || '帖子标题' }}</h1>
            <div class="tags flex space-x-2 ml-auto">
                <span v-for="tag in $route.query.tag_lst" :key="tag" :class="['tag', getTagColor(tag)]">
                    {{ tag }}
                </span>
            </div>
            <p class="text-gray-500 mt-2"> 楼主: <strong>{{ floors[0]?.nickname }}</strong> | 发帖时间: {{ formattedDate }}</p>
        </div>
        <!-- 显示标题，tag，楼主，发帖时间 -->
        

        <!-- 帖子内容部分 -->
        <div v-if="floors.length" class="topic-content border-t pt-4 mt-6">
            <div v-for="(floor, index) in floors" :key="floor.create_time"
                class="floor-item border-b border-gray-300 pb-4 mb-4">
                <!-- 按回复的时间排序，遍历所有该楼的回复 -->
                
                <!-- 右上角显示该楼回复的楼层号 -->
                <div v-if="floor.back_to > 0" class="absolute top-0 right-0 text-gray-500 text-sm">
                    回复 #{{ floor.back_to }}
                </div>
                
                <!-- 显示层号，层主，发帖时间 -->
                <p class="floor-info text-gray-600">#{{ index }} : <strong>{{ floor.nickname }}</strong>  | {{
                    formatUpdateTime(floor.create_time) }} </p>
                <div class="floor-content markdown-content mt-2" v-html="renderMarkdown(floor.content)"></div>

                <!-- 渲染图片列表 -->
                <div class="pic-list mt-2">
                    <div v-if="floor.pic_lst && floor.pic_lst.length">
                        <div class="grid grid-cols-2 gap-2">
                            <img v-for="(pic, picIndex) in floor.pic_lst" 
                                 :key="picIndex" 
                                 :src="'data:image/jpeg;base64,' + pic" 
                                 class="w-full rounded-lg" 
                                 alt="楼层图片" />
                        </div>
                    </div>
                </div>

                <div class="like-info mt-2 flex items-center text-gray-500">
                
                <!-- 点赞与点赞数 -->
                <div class="flex items-center space-x-2">
                    <!-- 点赞按钮 -->
                    <button @click="toggleLike(floor, index)" class="like-btn px-4 py-2 text-white rounded-lg">
                        <svg v-if="!floor.is_liked" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="w-6 h-6 text-gray-500">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 21C12 21 7 17 4 12.5C2.3 10.4 3.5 6 7.5 6C9.1 6 10.5 6.7 11.3 8C12.1 6.7 13.5 6 15.1 6C19.1 6 20.3 10.4 18.5 12.5C15.5 17 12 21 12 21Z"/>
                        </svg>
                        <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6 text-red-500">
                            <path fill-rule="evenodd" d="M12 21C12 21 7 17 4 12.5C2.3 10.4 3.5 6 7.5 6C9.1 6 10.5 6.7 11.3 8C12.1 6.7 13.5 6 15.1 6C19.1 6 20.3 10.4 18.5 12.5C15.5 17 12 21 12 21Z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                    <!-- 点赞数 -->
                    <span class="text-sm"> {{ floor.like_num }}</span>
                </div>

                <!-- 回复按钮 -->
                <button @click="replyToFloor(floor)" class="reply-btn px-4 py-2 text-white rounded-lg flex items-center space-x-2" style="margin-left: 2.5rem;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" stroke="currentColor" class="w-6 h-6 text-gray-500">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17l-5-5 5-5M4 12h12c1.1 0 2 .9 2 2v5"/>
                    </svg>
                    <span class="text-gray-500"> 回复 </span>              
                </button>
                </div>
            </div>
        </div>
        
        <!-- 显示回复的楼层 -->
        <div v-if="currentReplyFloor" class="reply-info text-sm text-gray-600 mt-3">
            <p>正在回复楼层 #{{ currentReplyFloor }}</p>
        </div>

        <!-- Markdown 回帖模块 -->
        <div class="reply-container mt-8">
            <h2 class="text-gray-500 mt-2">评论</h2>
            <div id="reply-editor" class="mt-2 py-4 px-6 border border-gray-200 rounded-lg"></div>
            <input type="file" multiple @change="handleFileChange" accept="image/*" class="mt-4">
            <button @click="submitReply" class="mt-4 py-2 px-4 bg-purple-600 text-white rounded-lg">发送评论</button>
            <div v-if="error" class="text-red-500 mt-2">{{ error }}</div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { Editor } from '@toast-ui/editor';
import '@toast-ui/editor/dist/toastui-editor.css';

export default {
    data() {
        return {
            floors: [], // 存储楼层内容
            error: '', // 存储错误信息
            editorInstance: null, // Markdown 编辑器实例
            form: {
                pic_lst: [] // 用于存储选择的图片文件
            },
            currentReplyFloor: 0, // 当前正在回复的楼层 ID
            nickname: localStorage.getItem('currentIdentity'), // 当前用户的昵称
            debounceTimeout: null, // 存储防抖定时器ID
        };
    },
    computed: {
        // 楼层创建时间
        formattedDate() {
            return this.formatUpdateTime(this.floors[0]?.create_time);
        }
    },
    methods: {
        // 获取帖子楼层信息
        async fetchFloors() {
            const { uuid, base_floor } = this.$route.params;
            try {
                const response = await axios.get(`/api/posts/${uuid}/${base_floor}`, {
                    params: {
                        nickname: this.nickname  // 将当前用户的昵称作为查询参数
                    }
                });
                this.floors = response.data.floors;  // 获取楼层信息

                // 初始化点赞状态
                this.floors.forEach(floor => {
                    floor.is_liked = floor.is_liked;  // 准备is_liked
                });
            } catch (error) {
                console.error('获取帖子失败', error);
            }
        },
        // 格式化时间戳
        formatUpdateTime(timestamp) {
            return new Date(timestamp * 1000).toLocaleString();
        },
        // 获取不同标签的颜色
        getTagColor(tag) {
            const tagColors = {
                aboutus: 'bg-blue-200 text-blue-800',
                share: 'bg-green-200 text-green-800',
                ask: 'bg-yellow-200 text-yellow-800',
                advertise: 'bg-purple-200 text-purple-800',
            };
            return tagColors[tag] || 'bg-gray-200 text-gray-800';
        },
        // 渲染 Markdown 格式的内容
        renderMarkdown(content) {
            const cleanHtml = DOMPurify.sanitize(marked(content));
            return cleanHtml;
        },
        // 处理文件选择事件，将选中的文件存储到 form.pic_lst
        handleFileChange(event) {
            this.form.pic_lst = Array.from(event.target.files); // 将文件存储到数组
        },
        // 设置回复的楼层
        replyToFloor(floor) {
            this.currentReplyFloor = floor.index -1;  // 设置当前回复的楼层 ID
        },
        // 提交回帖内容
        async submitReply() {
            const content = this.editorInstance.getMarkdown(); // 获取 Markdown 内容
            const author = this.nickname; // 当前用户的昵称
            const postId = this.$route.params.uuid; // 从路由参数获取帖子 ID

            // 检查文件大小
            for (const file of this.form.pic_lst) {
                if (file.size > 1024 * 1024) { // 检查文件大小是否大于1MB
                    this.error = '上传的图片不能大于1MB';
                    alert('上传的图片不能大于1MB');
                    return;
                }
            }

            const formData = new FormData();
            formData.append('author', author); // UUID 格式的身份标识
            formData.append('content', content); // 回帖内容
            formData.append('reply_to', this.currentReplyFloor); // 回复指定楼层

            this.form.pic_lst.forEach((file) => {
                formData.append('pic_lst', file); //图片列表
            });

            try {
                const response = await axios.post(`/api/posts/${postId}/reply`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data', // 确保使用 multipart/form-data
                    },
                });

                if (response.data.error_code === 0) {
                    alert('回复成功！');
                    this.floors.push({ nickname: author, content: content, create_time: Date.now() / 1000, like_num: 0 });
                } else {
                    this.error = response.data.msg || '回复失败，请重试';
                }
            } catch (error) {
                console.error('回复失败', error);
                this.error = '回复失败，请重试';
            }

            // 初始加载楼层数据
            this.fetchFloors();
        },

        // 点赞或取消点赞，带有防抖
        async toggleLike(floor) {
            // 如果防抖定时器存在，清除上一个定时器
            if (this.debounceTimeout) {
                clearTimeout(this.debounceTimeout);
            }

            // 设置新的防抖定时器，延迟 300ms 执行
            this.debounceTimeout = setTimeout(async () => {
                const postId = this.$route.params.uuid;
                const floorId = floor.index;  // 使用 floor.index 来表示楼层 ID
                const nickname = this.nickname; // 获取当前用户的昵称

                if (floor.is_liked == 1) {
                    // 取消点赞
                    try {
                        const response = await axios.post(`/api/posts/cancel-like`, {
                            nickname,
                            uuid: postId,
                            floor: floorId,
                        });

                        if (response.data.error_code === 0) {
                            floor.like_num -= 1;  // 减少点赞数
                            floor.is_liked = 0;  // 更新点赞状态为 0 未点赞
                        } else {
                            alert('取消点赞失败，请重试');
                        }
                    } catch (error) {
                        console.error('取消点赞失败', error);
                        alert('取消点赞失败，请重试');
                    }
                } else {
                    // 点赞
                    try {
                        const response = await axios.post(`/api/posts/like`, {
                            nickname,
                            uuid: postId,
                            floor: floorId,
                        });

                        if (response.data.error_code === 0) {
                            floor.like_num += 1;  // 增加点赞数
                            floor.is_liked = 1;  // 更新点赞状态为 1 已赞
                        } else {
                            alert('点赞失败，请重试');
                        }
                    } catch (error) {
                        console.error('点赞失败', error);
                        alert('点赞失败，请重试');
                    }
                }
            }, 300); // 防抖，延迟 300 毫秒执行
        }
    },

    // 回复框
    mounted() {
        this.editorInstance = new Editor({
            el: document.querySelector('#reply-editor'),
            height: '200px',
            initialEditType: 'markdown',
            previewStyle: 'vertical',
        });

        // 初始加载楼层数据
        this.fetchFloors();

        // 获取帖子楼层信息
        const { uuid, base_floor } = this.$route.params;
        axios.get(`/api/posts/${uuid}/${base_floor}`, {
            params: {
                nickname: this.nickname  // 将当前用户的昵称作为查询参数
            }
        }).then(response => {
            this.floors = response.data.floors;  // 获取楼层信息

            // 为每个楼层分配一个唯一的 floor_id，并初始化点赞状态
            this.floors.forEach(floor => {
                floor.is_liked = floor.is_liked;  // 转换 is_liked 为布尔值
            });
        }).catch(error => {
            console.error('获取帖子失败', error);
        });
    }
}
</script>

<style scoped>
.topic-container {
    background-color: #ffffff;
    border-radius: 8px;
}

.topic-header {
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
}

.floor-item {
    padding-top: 12px;
    position: relative;
}

.floor-info {
    font-size: 0.875rem;
}

.tags .tag {
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: bold;
}

.reply-container {
    padding: 12px;
    border-top: 1px solid #e2e8f0;
    height: 500px; /* 设置评论框高度为 300px */
}

#reply-editor {
    height: 350px !important; /* 设置编辑器容器高度 */
}

#reply-editor .toastui-editor-defaultUI {
    height: 100% !important; /* 默认 UI 填满编辑器容器 */
}

#reply-editor .toastui-editor-main {
    height: calc(100% - 50px) !important; /* 主编辑区域高度，50px 是工具栏的预留空间 */
    overflow-y: auto; /* 添加滚动条，当内容过多时可以滚动 */
}

.floor-content {
    word-wrap: break-word;
    word-break: break-word;
    overflow-wrap: break-word;
    white-space: normal;
}

.reply-btn {
    margin-left: 8px;
}
</style>