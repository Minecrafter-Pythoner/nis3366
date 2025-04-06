<template>
    <div class="max-w-7xl mx-auto p-12 bg-white border border-gray-200 rounded-lg">
        <h1 class="mb-6 text-2xl">找回密码 (*^▽^*)</h1>
        <p class="mb-6 text-gray-500">
            请输入您的用户名，然后回答安全问题，以找回您的密码。
        </p>
        <form class="space-y-6" v-on:submit.prevent="submitForm">
            <div>
                <label for="username">用户名</label><br>
                <input type="text" v-model="form.username" placeholder="请输入您的用户名"
                    class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
            </div>

            <div v-if="securityQuestions.length > 0">
                <div v-for="(question, index) in securityQuestions" :key="index" class="mt-4">
                    <label :for="'securityAnswer' + index">{{ question }}</label><br>
                    <input type="text" v-model="form.securityAnswers[index]" placeholder="请输入答案"
                        class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                </div>
            </div>

            <template v-if="errors.length > 0">
                <div class="bg-red-300 text-white rounded-lg p-6">
                    <p v-for="error in errors" v-bind:key="error">{{ error }}</p>
                </div>
            </template>

            <div v-if="showResetPassword">
                <label for="newPassword">新密码</label><br>
                <input type="password" v-model="form.newPassword" placeholder="请输入新密码"
                    class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
                <label for="confirmNewPassword" class="mt-4">确认新密码</label><br>
                <input type="password" v-model="form.confirmNewPassword" placeholder="请再次输入新密码"
                    class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
            </div>

            <div>
                <button class="py-4 px-6 bg-purple-600 text-white rounded-lg" type="submit">{{ showResetPassword ?
                    '重置密码' : '下一步'
                    }}</button>
            </div>
        </form>
    </div>
</template>
<script>
import axios from 'axios';
import bcrypt from 'bcryptjs';

export default {
    data() {
        return {
            form: {
                username: '',
                securityAnswers: ['', '', ''],
                newPassword: '',
                confirmNewPassword: ''
            },
            securityQuestions: [], // 存储从后端获取的安全问题
            errors: [],
            showResetPassword: false // 用于控制是否显示重置密码部分
        };
    },
    methods: {

        // 获取安全问题
        async fetchSecurityQuestions() {
            try {
                const response = await axios.post('/api/get-security-questions', { username: this.form.username });
                if (response.data.questions) {
                    this.securityQuestions = response.data.questions;
                    this.showResetPassword = true; // 切换到密码重置步骤
                } else {
                    this.errors.push(response.data.message || '获取安全问题失败');
                }
            } catch (error) {
                this.errors.push('获取安全问题失败，请确认用户名是否正确');
            }
        },

        async submitForm() {
            this.errors = []; // 清空错误信息

            if (!this.showResetPassword) {
                // 验证用户名输入
                if (this.form.username === '') {
                    this.errors.push('请输入用户名');
                } else {
                    await this.fetchSecurityQuestions(); // 获取安全问题
                }
            } else {
                // 验证安全问题并重置密码
                if (this.form.securityAnswers.some(answer => answer === '')) {
                    this.errors.push('请回答所有的安全问题');
                } else if (this.form.newPassword === '' || this.form.confirmNewPassword === '') {
                    this.errors.push('请输入新密码并确认新密码');
                } else if (this.form.newPassword !== this.form.confirmNewPassword) {
                    this.errors.push('两次输入的新密码不一致');
                } else if (!this.validatePassword(this.form.newPassword)) {
                    this.errors.push('密码必须至少包含6位，且同时包含大写字母、小写字母和数字');
                } else {
                    // 对新密码和安全问题答案进行加盐哈希
                    const salt = '$2b$10$MydCjsAEYPlPsacxglM4Y.'; // 生成盐
                    const hashedPassword = bcrypt.hashSync(this.form.newPassword, salt);
                    const hashedAnswers = this.form.securityAnswers.map(answer => bcrypt.hashSync(answer, salt));

                    try {
                        // 提交安全问题答案和新密码重置请求
                        const response = await axios.post('/api/verify-reset', {
                            username: this.form.username,
                            security_answers: hashedAnswers,
                            new_password: hashedPassword
                        });
                        if (response.data.success) {
                            alert('密码重置成功，请返回登录页面');
                            this.$router.push({ name: 'login' });
                        } else {
                            this.errors.push(response.data.message || '密码重置失败，请重试');
                        }
                    } catch (error) {
                        this.errors.push('密码重置失败，请重试');
                    }
                }
            }
        },

        // 验证密码强度和支持的特殊字符
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
}

input {
    border: 1px solid gray;
    border-radius: 5px;
    padding: 10px;
    width: 100%;
}

button {
    background-color: purple;
    color: white;
    padding: 10px;
    border-radius: 5px;
    cursor: pointer;
}

button:hover {
    background-color: darkblue;
}
</style>
