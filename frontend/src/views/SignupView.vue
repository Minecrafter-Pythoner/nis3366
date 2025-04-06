<template>
    <BackgroundContainer>
        <div class="max-w-7xl mx-auto grid grid-cols-2 gap-4">
            <div class="main-left">
                <div class="p-12 bg-white border border-gray-200 rounded-lg">
                    <h1 class="mb-6 text-2-xl">欢迎注册━(*・‿・*)ノ!</h1>
                    <p class="mb-6 text-gray-500">这是一款交大自主研发的匿名社交平台————</p>
                    <p class="font-bold">
                        什么？已经有账号了？Σ(⊙□⊙"点击
                        <RouterLink :to="{ 'name': 'login' }" class="underline" style="color: aquamarine;">这里
                        </RouterLink>
                        来登录！
                    </p>
                    <img src="../assets/go.png" class="mt-4 max-w-full max-h-[400px] object-cover" />
                </div>
            </div>
            <div class="main-right">
                <div class="p-12 border border-gray-200 rounded-lg transparent-bg">
                    <form class="space-y-6" v-on:submit.prevent="submitForm">
                        <div>
                            <label for="username">用户名</label><br>
                            <input type="text" v-model="form.username" placeholder="请输入您的用户名"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>

                        <div>
                            <label for="password">密码</label><br>
                            <input type="password" v-model="form.password" placeholder="设置一个密码"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>

                        <div>
                            <label for="confirm_password">确认密码</label><br>
                            <input type="password" v-model="form.confirm_password" placeholder="请再次输入密码"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>

                        <!-- 安全问题选择与答案填写 -->
                        <div>
                            <label for="security_question_1">{{ securityQuestions[0] }}</label><br>
                            <input type="text" v-model="form.security_answer_1" placeholder="请输入答案"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>
                        <div>
                            <label for="security_question_2">{{ securityQuestions[1] }}</label><br>
                            <input type="text" v-model="form.security_answer_2" placeholder="请输入答案"
                                class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                        </div>
                        <div>
                            <label for="security_question_3">{{ securityQuestions[2] }}</label><br>
                            <input type="text" v-model="form.security_answer_3" placeholder="请输入答案"
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
                            <button class="py-4 px-6 bg-purple-600 text-white rounded-lg">注册</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </BackgroundContainer>
</template>
<script>
import axios from 'axios';
import bcrypt from 'bcryptjs'; // 用于加密密码
import BackgroundContainer from '@/components/BackgroundContainer.vue';
import EC from 'elliptic';

export default {
    components: {
        BackgroundContainer
    },
    data() {
        return {
            securityQuestions: [], // 存储随机选择的三个安全问题
            captchaImage: '', // 验证码的 Base64 图片
            form: {
                username: '',
                password: '',
                confirm_password: '',
                security_question_1: '',
                security_answer_1: '',
                security_question_2: '',
                security_answer_2: '',
                security_question_3: '',
                security_answer_3: '',
                captcha_code: '', // 用户输入的验证码
                captcha_id: '' // 验证码的唯一标识ID
            },
            errors: []
        };
    },
    mounted() {
        this.fetchSecurityQuestions(); // 页面加载时获取随机的安全问题
        this.fetchCaptcha(); // 页面加载时获取验证码
    },
    methods: {
        // 获取随机的安全问题
        fetchSecurityQuestions() {
            axios.get('/api/get-random-security-questions')
                .then(response => {
                    this.securityQuestions = response.data.questions; // 从后端获取的三个随机安全问题
                    this.form.security_question_1 = this.securityQuestions[0];
                    this.form.security_question_2 = this.securityQuestions[1];
                    this.form.security_question_3 = this.securityQuestions[2];
                })
                .catch(error => {
                    console.error('获取安全问题失败', error);
                });
        },
        // 获取验证码
        fetchCaptcha() {
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

        createDefaultIdentity() {
            const formData = new FormData();
            formData.append('username', this.form.username);

            axios.post('/api/create-first-identity/', formData)
                .then(response => {
                    const { error_code, nickname } = response.data;
                    if (error_code === 0) {
                        // 自动切换到默认身份
                        localStorage.setItem('currentIdentity', nickname);
                        //为默认身份生成公私钥
                        const ec = new EC.ec('secp256k1');
                        const keyPair = ec.genKeyPair();
                        const privateKey = keyPair.getPrivate('hex');
                        const publicKey = keyPair.getPublic('hex');

                        // 存储公私钥，关联到身份
                        localStorage.setItem(`identity_${nickname}_privateKey`, privateKey);
                        localStorage.setItem(`identity_${nickname}_publicKey`, publicKey);
                        alert(`默认身份已创建并切换到身份：${nickname}`);
                        this.$router.push('/login');
                    } else if (error_code === 1) {
                        this.errors.push('身份创建失败');
                    }
                })
                .catch(error => {
                    this.errors.push('无法创建默认身份，请重试');
                });
        },
        // 提交表单
        submitForm() {
            this.errors = [];

            if (this.form.username === '') {
                this.errors.push('请输入用户名');
            }

            if (this.form.password === '') {
                this.errors.push('请输入密码');
            } else if (!this.validatePassword(this.form.password)) {
                this.errors.push('密码必须至少包含6位，且同时包含大写字母、小写字母和数字');
            }

            if (this.form.password !== this.form.confirm_password) {
                this.errors.push('两次输入的密码不一致');
            }

            // 验证安全问题是否填写完整
            if (this.form.security_answer_1 === '' || this.form.security_answer_2 === '' || this.form.security_answer_3 === '') {
                this.errors.push('请回答所有的安全问题');
            }

            // 验证验证码是否输入
            if (this.form.captcha_code === '') {
                this.errors.push('请输入验证码');
            }

            if (this.errors.length === 0) {

                // 固定盐值
                
                const salt = '$2b$10$MydCjsAEYPlPsacxglM4Y.'; // 生成盐
                const hashedPassword = bcrypt.hashSync(this.form.password, salt); // 加盐哈希密码
                const hashedSecurityAnswer1 = bcrypt.hashSync(this.form.security_answer_1, salt);
                const hashedSecurityAnswer2 = bcrypt.hashSync(this.form.security_answer_2, salt);
                const hashedSecurityAnswer3 = bcrypt.hashSync(this.form.security_answer_3, salt);

                // 发送注册请求到后端
                axios.post('/api/register', {
                    username: this.form.username,
                    password: hashedPassword,
                    captcha_code: this.form.captcha_code, // 用户输入的验证码
                    captcha_id: this.form.captcha_id, // 验证码的唯一ID
                    security_question_1: this.form.security_question_1,
                    security_answer_1: hashedSecurityAnswer1,
                    security_question_2: this.form.security_question_2,
                    security_answer_2: hashedSecurityAnswer2,
                    security_question_3: this.form.security_question_3,
                    security_answer_3: hashedSecurityAnswer3
                })
                    .then(response => {
                        switch (response.data.error_code) {
                            case 0:
                                // 注册成功
                                this.errors.push('注册成功');
                                this.createDefaultIdentity();
                                break;
                            case 1:
                                this.errors.push('用户名已存在，请重新输入');
                                break;
                            case 2:
                                this.errors.push('验证码错误！');
                                break;
                            default:
                                this.errors.push('系统错误，注册失败');
                        }
                    })
                    .catch(error => {
                        console.error('注册错误', error);
                        this.errors.push('注册失败，请重试');
                    });
            }
        },

        // 重置表单
        resetForm() {
            this.form.username = '';
            this.form.password = '';
            this.form.confirm_password = '';
            this.form.security_answer_1 = '';
            this.form.security_answer_2 = '';
            this.form.security_answer_3 = '';
            this.form.captcha_code = '';
            this.form.captcha_id = '';
        },

        // 验证密码强度
        validatePassword(password) {
            // 允许的特殊字符
            const allowedSpecialChars = /[!@#$%^&*(),.?":{}|<>_\-+=]/;
            // 验证密码是否包含大写字母、小写字母、数字和允许的特殊字符，且长度至少为6
            const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d!@#$%^&*(),.?":{}|<>_\-+=]{6,}$/;
            const hasUnsupportedChar = /[^A-Za-z\d!@#$%^&*(),.?":{}|<>_\-+=]/.test(password);

            if (hasUnsupportedChar) {
                this.errors.push('特殊字符不支持');
                return false;
            }

            return passwordRegex.test(password);
        }

    }
};
</script>
<style scoped>
/* 添加必要的样式 */
label {
    font-weight: bold;
    color: bisque;
}

</style>
