<template>
  <div class="invite-panel">
    <h2 class="text-base font-semibold text-gray-700 mb-4">私聊邀请</h2>
    <form @submit.prevent="submitInvite">
      <div class="mb-4">
        <label class="block text-lg font-medium text-indigo-600 mb-2">目标昵称</label>
        <input v-model="dstNickname" class="input-field" placeholder="输入目标用户昵称" required />
      </div>
      <div class="mb-4">
        <label class="block text-lg font-medium text-indigo-600 mb-2">申请信息</label>
        <textarea v-model="message" class="input-field" placeholder="写点申请理由吧" required></textarea>
      </div>
      <button type="submit" class="submit-button">
        发送邀请
      </button>
    </form>
  </div>
</template>

<script>
import { useChatStore } from '@/stores/chatStore';
import { ref } from 'vue';

export default {
  setup() {
    const chatStore = useChatStore();
    const dstNickname = ref('');
    const message = ref('');

    const submitInvite = () => {
      const srcNickname = localStorage.getItem('currentIdentity'); // 获取当前用户昵称
      const publicKey = localStorage.getItem(`identity_${srcNickname}_publicKey`); // 获取存储的公钥

      if (!publicKey) {
        alert('未找到当前身份的公钥，请重新生成身份密钥对');
        return;
      }

      // 发送邀请，包含公钥
      chatStore.sendInvite(srcNickname, dstNickname.value, message.value, publicKey);
    };

    return { dstNickname, message, submitInvite };
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
