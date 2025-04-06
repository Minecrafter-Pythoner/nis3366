<template>
    <BackgroundContainer>
        <div class="max-w-7xl mx-auto grid grid-cols-2 gap-4">
            <div class="main-left">
                <div class="p-12 bg-white border border-gray-200 rounded-lg">
                    <h1 class="mb-6 text-2-xl">登录(*^□^*)</h1>
                    <p class="mb-6 text-gray-500">
                        这是一款交大自主研发的匿名社交平台————
                    </p>
                    <p class="font-bold">
                        什么？还没有账户？？～(∠・ω&lt; )⌒★点击 <RouterLink :to="{ 'name': 'signup' }" class="underline"
                            style="color: aquamarine;">这里</RouterLink>
                        注册！
                    </p>
                    <img src="../assets/go.png" class="mt-4 max-w-full max-h-[400px] object-cover" />
                </div>
            </div>
            <div class="main-right">
                <div class="p-12 border border-gray-200 rounded-lg transparent-bg">
                    <form class="space-y-6" v-on:submit.prevent="submitForm">
                        <div>
                            <label for="">用户名</label><br>
                            <input type="text" v-model="form.username" placeholder="请输入您的用户名"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>

                        <div>
                            <label for="">密码</label><br>
                            <input type="password" v-model="form.password" placeholder="请输入密码"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>

                        <!-- 图片验证码 -->
                        <div>
                            <label for="captcha">验证码</label><br>
                            <div class="flex items-center">
                                <input type="text" v-model="form.captcha_code" placeholder="请输入验证码"
                                    class="w-1/2 mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                                <img :src="captchaImage" alt="验证码" class="ml-4 cursor-pointer"
                                    @click="refreshCaptcha" />
                            </div>
                        </div>

                        <template v-if="errors.length > 0">
                            <div class="bg-red-300 text-white rounded-lg p-6">
                                <p v-for="error in errors" v-bind:key="error">{{ error }}</p>
                            </div>
                        </template>

                        <div>
                            <button class="py-4 px-6 bg-purple-600 text-white rounded-lg">登录</button>
                        </div>
                    </form>

                    <!-- 添加忘记密码的跳转 -->
                    <div class="mt-6">
                        <p class="font-bold" style="color: bisque;">
                            忘记密码？！点击
                            <RouterLink :to="{ 'name': 'forgotpasswd' }" class="underline" style="color:aqua ;">这里
                            </RouterLink> 来找回密码！
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </BackgroundContainer>
</template>
<script>
import axios from 'axios';
import bcrypt from 'bcryptjs'; // 用于加密密码
import { useUserStore } from '@/stores/user';
import BackgroundContainer from '../components/BackgroundContainer.vue';

export default {
    setup() {
        const userStore = useUserStore();
        return {
            userStore
        };
    },
    components: {
        BackgroundContainer
    },

    data() {
        return {
            captchaImage: '', // 存储验证码图片的 Base64 编码
            form: {
                username: '',
                password: '',
                captcha_code: '', // 用户输入的验证码
                captcha_id: '' // 验证码的唯一标识ID
            },
            errors: [] // 存储表单错误信息
        };
    },
    mounted() {
        this.fetchCaptcha(); // 页面加载时获取验证码
    },
    methods: {
        // 获取验证码，不带 Authorization 请求头
        fetchCaptcha() {
            delete axios.defaults.headers.common["Authorization"]; // 显式移除 `Authorization` 头，防止带上无效 token
            axios.get('/api/get-captcha')
                .then(response => {
                    this.captchaImage = 'data:image/png;base64,' + response.data.captcha_image;
                    this.form.captcha_id = response.data.captcha_id; // 保存 captcha_id 以供提交
                })
                .catch(error => {
                    console.error('获取验证码失败', error);
                });
        },

        // 刷新验证码
        refreshCaptcha() {
            this.fetchCaptcha(); // 重新获取验证码
        },

        // 提交表单进行登录
        async submitForm() {
            this.errors = []; // 清空错误信息

            // 表单验证
            if (this.form.username === '') {
                this.errors.push('请输入用户名');
            }
            if (this.form.password === '') {
                this.errors.push('请输入密码');
            }
            if (this.form.captcha_code === '') {
                this.errors.push('请输入验证码');
            }

            if (this.errors.length === 0) {
                try {
                    // 加密密码
                    const salt = '$2b$10$MydCjsAEYPlPsacxglM4Y.'; // 固定盐值
                    const hashedPassword = bcrypt.hashSync(this.form.password, salt); // 加盐哈希密码

                    // 登录请求
                    const loginResponse = await axios.post('/api/login', {
                        account_name: this.form.username,
                        password_hash: hashedPassword,
                        captcha_code: this.form.captcha_code,
                        captcha_id: this.form.captcha_id
                    });

                    // 根据响应结果处理
                    switch (loginResponse.data.error_code) {
                        case 0:
                            // 调用获取 Token 函数
                            const lastUsedIdentity = loginResponse.data.last_used_identity;

                            await this.getTokens();
                            localStorage.setItem('currentIdentity', lastUsedIdentity);
                            alert(`已切换到身份：${lastUsedIdentity}`);

                            // 跳转到 feed 页面并刷新
                            this.$router.push('/feed').then(() => {
                                setTimeout(() => {
                                    window.location.reload(); // 刷新页面
                                }, 0); // 立即刷新
                            });
                            break;
                        case 1:
                            this.errors.push('密码错误，请重新输入');
                            break;
                        case 2:
                            this.errors.push('用户不存在');
                            break;
                        case 3:
                            this.errors.push('验证码错误');
                            this.refreshCaptcha(); // 刷新验证码
                            break;
                        default:
                            this.errors.push('系统错误，登录失败');
                    }

                } catch (error) {
                    console.error('登录失败', error);
                    this.errors.push('登录失败，请重试');
                }
            }
        },

        // 获取 JWT Token
        async getTokens() {
            try {
                const salt = '$2b$10$MydCjsAEYPlPsacxglM4Y.'; // 固定盐值
                const hashedPassword = bcrypt.hashSync(this.form.password, salt); // 加盐哈希密码
                const tokenResponse = await axios.post('/api/token/', {
                    username: this.form.username,
                    password: hashedPassword
                });

                // 保存 Token 并设置全局 Authorization 头部
                this.userStore.setToken(tokenResponse.data);
                localStorage.setItem('username', this.form.username);

            } catch (error) {
                console.error('获取 token 失败', error);
                this.errors.push('获取 token 失败');
            }
        }
    }
};
</script>




<style scoped>
/* 添加适合的样式 */
label {
    font-weight: bold;
    color: bisque;
}


</style>
