<template>
  <div class="request-list-panel">
    <h2 class="text-base font-semibold text-gray-700 mb-4">收到的邀请</h2>

    <ul v-if="invites.length" class="space-y-4">
      <li v-for="invite in invites" :key="invite.timestamp" class="invite-item">
        <p class="text-gray-700">
          <strong class="text-indigo-500">{{ invite.src_nickname }}</strong> 邀请你私聊
        </p>
        <p class="text-gray-500 mb-2">时间: {{ formatTimestamp(invite.timestamp) }}</p>
        <p class="text-gray-600 mb-4">{{ invite.message }}</p>
        <div class="flex space-x-4">
          <button @click="handleInvite(invite.src_nickname, 0)"
            class="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200">
            接受
          </button>
          <button @click="handleInvite(invite.src_nickname, 1)"
            class="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200">
            拒绝
          </button>
        </div>
      </li>
    </ul>
    <p v-else class="text-gray-500">没有收到任何邀请。</p>
  </div>
</template>

<script>
import { useChatStore } from '@/stores/chatStore';
import { onMounted, computed } from 'vue';

export default {
  setup() {
    const chatStore = useChatStore();
    const nickname = localStorage.getItem('currentIdentity');

    // 调用 fetchInvites 获取数据
    onMounted(() => {
      chatStore.fetchInvites(nickname);
    });

    // 监听 chatStore.invites 的变化
    const invites = computed(() => chatStore.invites);

    // 处理邀请
    const handleInvite = (srcNickname, choice) => {
      chatStore.handleInvite(choice, srcNickname, nickname);
    };

    // 格式化时间戳
    const formatTimestamp = (timestamp) => {
      return new Date(timestamp).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    };

    return { invites, handleInvite, formatTimestamp };
  }
};
</script>

<style scoped>
.request-list-panel {
  background-color: rgba(255, 255, 255, 0.3);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.invite-item {
  background-color: rgba(247, 247, 247, 0.3);
  padding: 15px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
