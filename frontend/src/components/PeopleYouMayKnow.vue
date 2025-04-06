<template>
    <div class="p-4"
        style="background-color: rgba(255, 255, 255, 0.7); border: 1px solid rgba(229, 231, 235, 1); border-radius: 0.5rem;">
        <h3 class="mb-6 text-base">可能认识的人</h3>
        <div class="space-y-4">
            <div class="flex items-center justify-between" v-for="user in users" :key="user.id">
                <div class="flex items-center space-x-2">
                    <img :src="user.avatar" class="w-[40px] rounded-full" alt="Avatar">
                    <p class="text-xs"><strong>{{ user.name }}</strong></p>
                </div>
                <a href="#" @click.prevent="startChat(user)"
                    class="py-2 px-3 bg-purple-600 text-white text-xs rounded-lg">
                    私聊
                </a>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';

// 动态导入头像
const importAvatars = () => {
    const avatarFiles = import.meta.glob('@/assets/suzume_*.png');
    return Object.keys(avatarFiles).map(file => file);  // 返回图片路径的数组

};

export default {
    data() {
        return {
            users: [],
            errors: [],
            chatUser: null,
            username: '',
            token: '',
            avatars: importAvatars(),  
            identity: ''
        };
    },
    mounted() {
        this.username = localStorage.getItem('username');
        this.identity = localStorage.getItem('currentIdentity');
        this.token = localStorage.getItem('user.access');

        if (!this.username) {
            this.errors.push('未找到用户名，请重新登录');
        } else {
            this.fetchRecommendedUsers();  // 获取推荐用户
        }
    },
    methods: {
        // 获取随机头像路径
        getRandomAvatar() {
            const randomIndex = Math.floor(Math.random() * this.avatars.length);
            const avatarPath = this.avatars[randomIndex];
            return avatarPath;  // 返回相对路径

        },

        // 获取推荐用户列表
        async fetchRecommendedUsers() {
            if (!this.token) {
                this.errors.push('未找到有效的身份认证，请重新登录');
                return;
            }

            try {
                const response = await axios.get('/api/chat/recommend', {
                    params: { nickname: this.identity },
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                // 将推荐用户信息映射为具有头像的对象数组
                this.users = response.data.recommend_lst.map((name, index) => ({
                    id: index + 1,
                    name: name,
                    avatar: this.getRandomAvatar() // 获取随机头像
                }));
            } catch (error) {
                console.error("Error fetching recommended users:", error);
                this.errors.push('无法加载推荐用户，请检查网络连接');
            }
        },

        async sendInvite(targetUsername, publicKey) {
            try {
                const response = await axios.post('/api/chat/invite', {
                    src_nickname: this.identity,
                    dst_nickname: targetUsername,
                    message: `Hi ${targetUsername}, 我想与你进行私聊!`,
                    publickey: publicKey // 使用存储的公钥

                }, {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (response.data.error_code === 0) {
                    alert(`已成功向 ${targetUsername} 发送私聊邀请`);
                } else {
                    alert(`无法向 ${targetUsername} 发送私聊邀请：${response.data.message}`);
                }
            } catch (error) {
                console.error('发送私聊邀请失败:', error);
                alert('发送私聊邀请失败，请检查网络连接');
            }
        },

        startChat(user) {
            this.chatUser = user;

            // 从 localStorage 中获取当前身份的公钥
            const publicKey = localStorage.getItem(`identity_${this.identity}_publicKey`);
            if (!publicKey) {
                alert('未找到当前身份的公钥，请重新生成身份密钥对');
                return;
            }

            // 发送邀请并包含公钥
            this.sendInvite(user.name, publicKey);
        }
    }
};
</script>

<style scoped>
.invite-panel {
    background-color: rgba(255, 255, 255, 0.6);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    font-family: 'Arial', sans-serif;
    color: #333;
}

.input-field {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
    font-family: inherit;
    color: #333;
    outline: none;
    transition: border-color 0.2s ease;
}

.input-field:focus {
    border-color: #4a90e2;
    box-shadow: 0 0 5px rgba(74, 144, 226, 0.3);
}

.submit-button {
    width: 100%;
    padding: 10px;
    background-color: #4a90e2;
    color: white;
    font-size: 1rem;
    font-family: inherit;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.submit-button:hover {
    background-color: #357ABD;
}
</style>
