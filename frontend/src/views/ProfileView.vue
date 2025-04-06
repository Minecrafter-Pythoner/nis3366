<template>
    <div class="max-w-7xl mx-auto p-12 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white rounded-2xl shadow-2xl transform hover:scale-105 transition-all duration-300">
        <!-- 标题区域 -->
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-4xl font-bold tracking-wide text-center-2xl">{{ username }} 的个人页面</h1>
        </div>

        <!-- 身份管理和图片框 -->
        <div class="bg-white text-black p-6 rounded-lg shadow-md flex justify-between items-start">
            <!-- 身份管理组件 -->
            <div class="w-2/3">
                <IdentityManagement />
            </div>

            <!-- 右侧图片框 -->
            <div class="ml-6 flex justify-center items-center w-[35%] h-[35%]">
                <img :src="imagePath" alt="用户图片" class="w-full h-full object-cover rounded-lg border-4 border-gray-400" />
            </div>
        </div>
    </div>
</template>

<!-- <div class="w-1/3 ml-6 transform scale-105 translate-y-2">
    <img :src="imagePath" alt="用户图片" class="w-full h-72 object-cover rounded-lg border-4 border-gray-400" />
</div> -->

<script>
import IdentityManagement from '@/components/Identity.vue';
import { useUserStore } from '@/stores/user';
import userImage from '@/assets/xiangzi.png';

export default {
    components: {
        IdentityManagement
    },
    setup() {
        const userStore = useUserStore();

        return {
            userStore,
            imagePath: userImage,
        };
    },
    computed: {
        username() {
            return localStorage.getItem('username') || this.userStore.user.username;
        }
    }
};
</script>

<style scoped>
/* 增强外观的样式 */
h1 {
    text-shadow: 2px 4px 6px rgba(0, 0, 0, 0.3);
}
.shadow-2xl {
    box-shadow: 0px 10px 15px rgba(0, 0, 0, 0.2), 0px 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
