<template>
    <div class="max-w-7xl mx-auto p-12 bg-white border border-gray-200 rounded-lg">
        <h4 class="text-xl">身份管理（戴上假面吧）</h4>
        <h6 class="text-xl" style="color:aliceblue;"> ____________________ </h6>

        <!-- 显示当前用户已注册的身份以及公私钥的操作按钮 -->
        <div v-if="registeredIdentities.length > 0">
            <h2 class="mb-6 text-2xl">当前已注册身份：</h2>
            <ul class="list-disc pl-6">
                <!-- 高亮（背景黄色）当前身份 -->
                <li v-for="identity in registeredIdentities" :key="identity.nickname"
                    :class="{
                        'bg-yellow-200 text-1xl': identity.nickname === currentIdentity, 
                        'flex': true, 
                        'items-center': true, 
                        'justify-between': true, 
                        'gap-4': true
                    }">
                    <span>{{ identity.nickname }}</span>
                    <div class="flex space-x-4">
                        <button class="bg-purple-500 text-white px-4 py-1 rounded"
                            @click="downloadKeys(identity.nickname)">
                            下载公私钥
                        </button>
                        <button class="bg-green-500 text-white px-4 py-1 rounded"
                            @click="uploadKeys(identity.nickname)">
                            上传公私钥
                        </button>
                        <button class="bg-red-500 text-white px-4 py-1 rounded"
                            @click="deleteIdentity(identity.nickname)">
                            删除身份
                        </button>
                        <button class="bg-blue-500 text-white px-4 py-1 rounded"
                            @click="switchIdentity(identity.nickname)">
                            切换身份
                        </button>
                    </div>
                </li>
            </ul>
        </div>

        <!-- 注册新身份表单 -->
        <form class="space-y-6 mt-6" v-on:submit.prevent="submitForm">
            <div v-if="errors.length > 0">
                <div class="bg-red-300 text-white rounded-lg p-6">
                    <p v-for="error in errors" v-bind:key="error">{{ error }}</p>
                </div>
            </div>

            <div v-if="nickname">
                <div class="bg-green-300 text-white rounded-lg p-6">
                    <p>注册成功，昵称：{{ nickname }}</p>
                </div>
            </div>

            <div>
                <button class="py-4 px-6 bg-purple-800 text-white rounded-lg large-button" type="submit"
                    :disabled="registeredIdentities.length >= 5">
                    注册新身份
                </button>
            </div>

            <div v-if="registeredIdentities.length >= 5" class="text-red-500 mt-4">
                您已注册了5个身份，无法再注册更多身份。
            </div>
        </form>
    </div>
</template>

<script>
import axios from 'axios';
import EC from 'elliptic';

export default {
    data() {
        return {
            username: '', // 当前用户名
            currentIdentity: localStorage.getItem('currentIdentity') || '', // 当前身份
            registeredIdentities: [], // 已注册的身份列表
            nickname: '', // 成功注册后的身份昵称
            errors: [] // 错误信息
        };
    },
    mounted() {
        this.username = localStorage.getItem('username');
        if (!this.username) {
            this.errors.push('未找到用户名，请重新登录');
        } else {
            this.fetchRegisteredIdentities(); // 加载已注册的身份
        }
    },
    methods: {
        // 获取已注册的身份列表
        async fetchRegisteredIdentities() {
            const token = localStorage.getItem('user.access');
            if (!token) {
                this.errors.push('未找到有效的身份认证，请重新登录');
                return;
            }
            try {
                const response = await axios.get(`/api/show-identities/?username=${this.username}`);
                this.registeredIdentities = response.data.identities.map(identity => ({ nickname: identity }));
            } catch (error) {
                this.errors.push('无法加载已注册身份，请检查网络连接');
            }
        },

        // 注册新身份并生成公私钥
        async submitForm() {
            this.errors = []; // 清空错误信息
            this.nickname = ''; // 清空成功信息

            if (this.registeredIdentities.length >= 5) {
                this.errors.push('身份数量已达到上限');
                return;
            }

            const formData = new FormData();
            formData.append('username', this.username);

            try {
                const response = await axios.post('/api/create-identity/', formData);
                const { error_code, nickname } = response.data;
                if (error_code === 0) {
                    this.nickname = nickname;
                    this.generateAndStoreKeyPair(nickname); // 为新身份生成公私钥
                    this.fetchRegisteredIdentities();
                } else if (error_code === 1) {
                    this.errors.push('注册失败，身份数量已超过5个');
                }
            } catch (error) {
                this.errors.push('注册失败，请检查网络连接或重试');
            }
        },

        // 切换身份
        async switchIdentity(nickname) {
            localStorage.setItem('currentIdentity', nickname);
            this.currentIdentity = nickname; // 更新当前身份

            try {
                const response = await axios.post('/api/update-identity/', {
                    username: this.username,
                    identity: nickname
                });

                if (response.data.error_code === 0) {
                    alert(`已切换到身份：${nickname}`);
                    this.loadIdentityKeys(nickname); // 切换身份时加载公私钥
                    window.location.reload();
                } else {
                    this.errors.push('切换身份失败，请重试');
                }
            } catch (error) {
                this.errors.push('切换身份失败，请检查网络连接');
            }
        },

        // 删除身份
        async deleteIdentity(nickname) {
            if (nickname === localStorage.getItem('currentIdentity')) {
                alert('不能删除当前身份，请先切换身份');
                return;
            }
            try {
                const response = await axios.delete('/api/delete-identity/', {
                    data: {
                        username: this.username,
                        nickname: nickname
                    }
                });

                if (response.data.error_code === 0) {
                    this.registeredIdentities = this.registeredIdentities.filter(
                        identity => identity.nickname !== nickname
                    );
                    this.removeIdentityKeys(nickname); // 删除身份时清除公私钥
                    alert('身份删除成功');
                } else if (response.data.error_code === 1) {
                    this.errors.push('删除失败，用户名和身份昵称不匹配');
                } else if (response.data.error_code === 2) {
                    this.errors.push('删除失败，未找到用户');
                }
            } catch (error) {
                this.errors.push('删除身份失败，请检查网络连接或重试');
            }
        },

        // 生成并存储公私钥对
        generateAndStoreKeyPair(nickname) {
            const ec = new EC.ec('secp256k1');
            const keyPair = ec.genKeyPair();
            const privateKey = keyPair.getPrivate('hex');
            const publicKey = keyPair.getPublic('hex');

            // 存储公私钥，关联到身份
            localStorage.setItem(`identity_${nickname}_privateKey`, privateKey);
            localStorage.setItem(`identity_${nickname}_publicKey`, publicKey);

            console.log(`生成并存储公私钥对：${nickname}`);
        },

        // 加载身份的公私钥
        loadIdentityKeys(nickname) {
            const privateKey = localStorage.getItem(`identity_${nickname}_privateKey`);
            const publicKey = localStorage.getItem(`identity_${nickname}_publicKey`);

            if (privateKey && publicKey) {
                console.log(`加载公私钥对：${nickname}`);
            } else {
                console.error(`未找到公私钥对：${nickname}`);
            }
        },

        // 删除身份的公私钥
        removeIdentityKeys(nickname) {
            localStorage.removeItem(`identity_${nickname}_privateKey`);
            localStorage.removeItem(`identity_${nickname}_publicKey`);

            console.log(`删除公私钥对：${nickname}`);
        },

        // 下载公私钥到本地
        downloadKeys(nickname) {
            const privateKey = localStorage.getItem(`identity_${nickname}_privateKey`);
            const publicKey = localStorage.getItem(`identity_${nickname}_publicKey`);

            if (privateKey && publicKey) {
                const keys = {
                    privateKey: privateKey,
                    publicKey: publicKey
                };

                const blob = new Blob([JSON.stringify(keys)], { type: 'application/json' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${nickname}_keys.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
        
                console.log(`下载公私钥对：${nickname}`);
            } else {
                console.error(`未找到公私钥对：${nickname}`);
            }
        },

        // 上传公私钥
        uploadKeys(nickname) {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = async (event) => {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = async () => {
                        try {
                            const keys = JSON.parse(reader.result);
                            const { privateKey, publicKey } = keys;
                            if (privateKey && publicKey) {
                                localStorage.setItem(`identity_${nickname}_privateKey`, privateKey);
                                localStorage.setItem(`identity_${nickname}_publicKey`, publicKey);
                                alert('公私钥上传成功');
                            } else {
                                alert('无效的公私钥文件');
                            }
                        } catch (error) {
                            alert('无法解析公私钥文件');
                        }
                    };
                    reader.readAsText(file);
                }
            };
            input.click();
        }
    }
};
</script>

<style scoped>
.bg-yellow-200 {
    background-color: #fef3c7;
}
.large-button {
    font-size: 1.125rem;
    padding: 12px 24px;
}
.text-xl {
    color: #a8126f;
    font-size: 2.2rem;
}
</style>
