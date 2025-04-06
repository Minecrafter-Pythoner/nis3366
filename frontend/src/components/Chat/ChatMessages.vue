<template>
  <div class="messages-panel">
    <h2 class="text-base font-semibold text-gray-700 mb-4">聊天记录</h2>

    <div class="space-y-4 mb-4">
      <div
        v-for="msg in chatStore.messages"
        :key="msg.timestamp"
        :class="{ 'message-item sent': isOwnMessage(msg), 'message-item received': !isOwnMessage(msg) }"
      >
        <div class="flex items-center" :class="{ 'justify-end': isOwnMessage(msg) }">
          <img v-if="!isOwnMessage(msg)" :src="leftAvatar" class="w-8 h-8 rounded-full mr-3" alt="Avatar" />
          <div>
            <strong class="mr-2 text-indigo-500" v-if="!isOwnMessage(msg)">{{ msg.src_nickname }}:</strong>
            <span
              :class="{ 'bg-gray-100 text-gray-700': !isOwnMessage(msg), 'bg-indigo-500 text-white': isOwnMessage(msg) }"
              class="px-4 py-2 rounded-lg shadow-sm"
            >
              {{ msg.message }}
            </span>
          </div>
          <img v-if="isOwnMessage(msg)" :src="rightAvatar" class="w-8 h-8 rounded-full ml-3" alt="Avatar" />
        </div>
        <small class="text-gray-400" :class="{ 'text-right': isOwnMessage(msg) }">{{ formatTimestamp(msg.timestamp) }}</small>
      </div>
    </div>

    <div class="flex">
      <input
        v-model="newMessage"
        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
        placeholder="输入消息"
      />
      <button @click="sendMessage" class="ml-2 bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200">
        发送
      </button>
    </div>
  </div>
</template>

<script>
import { useChatStore } from '@/stores/chatStore';
import { ref, watch, onMounted } from 'vue';

// 用来加载头像
const importAvatars = () => {
  const avatarFiles = import.meta.glob('@/assets/suzume_*.png');
  return Object.keys(avatarFiles).map(filePath => filePath);
};

export default {
  props: {
    user: String  // 接收当前聊天的好友
  },
  setup(props) {
    const chatStore = useChatStore();
    const newMessage = ref('');
    const nickname = localStorage.getItem('currentIdentity');
    const avatars = importAvatars();

    const leftAvatar = ref('');
    const rightAvatar = ref('');

    // 获取一个随机头像
    const getRandomAvatar = () => {
      const randomIndex = Math.floor(Math.random() * avatars.length);
      return avatars[randomIndex];
    };

    // 获取一个与当前头像不同的随机头像
    const getDifferentRandomAvatar = (currentAvatar) => {
      let randomIndex;
      do {
        randomIndex = Math.floor(Math.random() * avatars.length);
      } while (avatars[randomIndex] === currentAvatar);
      return avatars[randomIndex];
    };

    leftAvatar.value = getRandomAvatar();
    rightAvatar.value = getDifferentRandomAvatar(leftAvatar.value);

    // 判断消息是否是自己发的
    const isOwnMessage = (msg) => msg.owner === 0;

    // 刷新聊天记录
    const refreshMessages = async () => {
      if (props.user) {
        await chatStore.fetchChatWithUser(props.user, nickname);
        console.log(chatStore.messages)
      }
    };

    // 在 user 变化时刷新聊天记录
    watch(() => props.user, () => {
      refreshMessages();
    });

    let hasFetchedMessages = false;

    // 在组件挂载时初次加载消息
    onMounted(() => {
      if (props.user && !hasFetchedMessages) {
        refreshMessages();
        hasFetchedMessages = true;
      }
    });

    // 发送消息
    const sendMessage = async () => {
      const trimmedMessage = newMessage.value.trim();
      if (trimmedMessage !== '') {
        try {
          await chatStore.sendMessage(nickname, props.user, trimmedMessage);
          newMessage.value = '';  // 清空输入框
          refreshMessages();  // 刷新消息
        } catch (error) {
          console.error('发送消息失败:', error);
        }
      }
    };

    // 格式化时间戳
    const formatTimestamp = (timestamp) => {
      const date = new Date(timestamp * 1000);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    };

    return {
      chatStore,
      newMessage,
      sendMessage,
      isOwnMessage,
      leftAvatar,
      rightAvatar,
      formatTimestamp
    };
  }
};
</script>

<style scoped>
.messages-panel {
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-height: 500px; /* 限制最大高度 */
  overflow-y: auto; /* 滚动条 */
}
</style>
