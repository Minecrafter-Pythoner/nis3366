<template>
  <div class="friend-list">
    <h2 class="text-base font-semibold text-gray-700 mb-4">好友列表</h2>
    <ul class="friend-list-items">
      <li v-for="friend in approvedFriends" :key="friend">
        <button 
          @click="selectFriend(friend)" 
          class="friend-item"
          :class="{ 'friend-item-active': selectedFriend === friend }"
        >
          {{ friend }}
        </button>
      </li>
    </ul>
  </div>
</template>

<script>
import { computed, onMounted, watch, ref } from 'vue';
import { useChatStore } from '@/stores/chatStore';

export default {
  setup(props, { emit }) {
    const chatStore = useChatStore();
    const selectedFriend = ref(null);

    onMounted(() => {
      const currentIdentity = localStorage.getItem('currentIdentity');
      
      if (currentIdentity) {
        chatStore.loadFriendsForCurrentIdentity(currentIdentity);
        chatStore.fetchInviteStates(currentIdentity);
      }
    });

    watch(
      () => chatStore.approvedFriends,
      (newVal) => {
        const currentIdentity = localStorage.getItem('currentIdentity');
        if (currentIdentity) {
          localStorage.setItem(`approvedFriends_${currentIdentity}`, JSON.stringify(newVal));
        }
      },
      { deep: true }
    );

    const selectFriend = (friend) => {
      selectedFriend.value = friend;
      emit('friend-selected', friend);
    };

    return {
      approvedFriends: computed(() => chatStore.approvedFriends),
      selectFriend,
      selectedFriend
    };
  }
};
</script>

<style scoped>
.friend-list {
  background-color: rgba(255, 255, 255, 0.5); /* 半透明背景 */
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 520px; /* 调整为更窄的宽度 */
  height: 150px; /* 限制高度 */
  overflow-y: auto; /* 添加滚动条 */
  border: 1px solid rgba(0, 0, 0, 0.1); /* 微弱的边框 */
}

.friend-list h2 {
  margin-top: 0;
  font-size: 1rem;
  color: #4a4a4a;
}

.friend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  background-color: #e3f2fd; /* 更柔和的背景色 */
  color: #1565c0; /* 深蓝色文本 */
  border: 1px solid #bbdefb; /* 边框颜色与背景协调 */
  border-radius: 5px;
  margin-bottom: 8px; /* 调整间距 */
  cursor: pointer;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.friend-item:hover {
  background-color: #bbdefb; /* 悬停时变深的颜色 */
  color: #0d47a1; /* 悬停时变深的文字颜色 */
  border-color: #0d47a1;
}

/* 新增：活跃状态的样式 */
.friend-item-active {
  background-color: #90caf9; /* 更深的背景色 */
  color: #0d47a1; /* 更深的文本颜色 */
  border-color: #0d47a1; /* 更深的边框颜色 */
  font-weight: 500; /* 略微加粗 */
  box-shadow: 0 2px 4px rgba(13, 71, 161, 0.2); /* 添加微小阴影增强立体感 */
}
</style>