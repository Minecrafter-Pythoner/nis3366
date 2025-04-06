<template>
  <div class="chat-container">
    <div class="content-wrapper">
      <div class="left-panel">
        <div class="invite-section">
          <ChatInvite />
        </div>
        <div class="request-list-section">
          <ChatRequestList />
        </div>
      </div>

      <div class="right-panel">
        <FriendList @friend-selected="fetchChatWithFriend" /> <!-- 好友列表 -->
        <ChatMessages v-if="currentChatUser" :user="currentChatUser" /> <!-- 显示聊天记录 -->
      </div>
    </div>
  </div>
</template>

<script>
import ChatInvite from '@/components/Chat/ChatInvite.vue';
import ChatRequestList from '@/components/Chat/ChatRequestList.vue';
import ChatMessages from '@/components/Chat/ChatMessages.vue';
import FriendList from '@/components/Chat/FriendList.vue';
import { ref } from 'vue';

export default {
  components: {
    ChatInvite,
    ChatRequestList,
    ChatMessages,
    FriendList
  },
  setup() {
    const currentChatUser = ref(null); // 当前聊天用户

    const fetchChatWithFriend = (nickname) => {
      console.log('Selected friend:', nickname);  // 检查控制台输出
      currentChatUser.value = nickname;  // 更新聊天用户
    };

    return {
      currentChatUser,
      fetchChatWithFriend
    };
  }
};
</script>


<style scoped>
.chat-container {
  background-image: url('@/assets/bg.jpg'); /* 使用本地背景图片 */
  background-size: cover;
  background-position: center;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-wrapper {
  display: flex;
  background: rgba(255, 255, 255, 0.6); /* 半透明白色背景 */
  border-radius: 16px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.2); /* 阴影效果 */
  overflow: hidden;
  width: 80%;
  max-width: 1200px;
  min-height: 80vh;
}

.left-panel {
  width: 50%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  background-color: rgba(255, 255, 255, 0.5); 
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  gap: 10px;
}

.invite-section, .request-list-section {
  margin: 0;
  padding: 0;
}

.request-list-section {
  margin-top: 10px;
}

/* 右侧面板样式 */
.right-panel {
  width: 50%;
  padding: 10px; /* 减少右侧内边距 */
  display: flex;
  flex-direction: column;
  background-color: rgba(255, 255, 255, 0.2);
  flex-grow: 1; 
  overflow-y: auto; /* 增加滚动条 */
}

.right-panel > * {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

/* 调整 ChatMessages 样式 */
.chat-container .chat-messages {
  font-size: 0.85rem; /* 缩小字体 */
  padding: 10px; /* 减少内边距 */
  max-height: 60vh; /* 限制最大高度 */
  overflow-y: auto; /* 增加滚动条 */
}

.chat-container h2 {
  font-size: 1.2rem;
  margin-bottom: 0.8rem;
  color: #333;
}

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
    width: 95%;
  }

  .left-panel, .right-panel {
    width: 100%;
    border: none;
    padding: 10px;
  }
}
</style>
