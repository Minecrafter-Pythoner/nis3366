<template>
    <div class="max-w-7xl mx-auto grid grid-cols-4 gap-4">
        <!-- 左侧联系人列表 -->
        <div class="main-left col-span-1">
            <div class="p-4 bg-white border border-gray-200 rounded-lg">
                <div class="space-y-4">
                    <div 
                        v-for="user in users" 
                        :key="user.id" 
                        class="flex items-center justify-between"
                    >
                        <div class="flex items-center space-x-2">
                            <img :src="user.avatar" class="w-[40px] rounded-full" alt="用户头像">
                            <p><strong>{{ user.name }}</strong></p>
                        </div>
                        <span class="text-xs text-gray-500">{{ user.lastActive }}分钟前</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 私聊框 -->
        <div class="main-center col-span-3 space-y-6">
            <!-- 聊天信息展示区域 -->
            <div class="bg-white border border-gray-200 rounded-lg">
                <div class="flex flex-col flex-grow p-4" id="messages">
                    <div 
                        v-for="(msg, index) in messages" 
                        :key="index" 
                        :class="msg.isSentByUser ? 'ml-auto justify-end' : ''" 
                        class="flex w-full mt-2 space-x-3 max-w-md"
                    >
                        <div v-if="!msg.isSentByUser" class="flex-shrink-0 h-10 w-10 rounded-full bg-gray-300">
                            <img :src="chatUser.avatar" class="w-[40px] rounded-full">
                        </div>
                        <div :class="msg.isSentByUser ? 'bg-blue-600 text-white' : 'bg-gray-300'" class="p-3 rounded-lg">
                            <p class="text-sm">{{ msg.text }}</p>
                        </div>
                        <span class="text-xs text-gray-500 leading-none">{{ msg.timestamp }}</span>
                    </div>
                </div>
            </div>
            
            <!-- 消息输入框 -->
            <div class="bg-white border border-gray-200 rounded-lg">
                <div class="p-4">  
                    <textarea v-model="newMessage" class="p-4 w-full bg-gray-100 rounded-lg" placeholder="写消息..."></textarea>
                </div>
                <div class="p-4 border-t border-gray-100 flex justify-between">
                    <a href="#" @click.prevent="sendMessage" class="inline-block py-4 px-6 bg-purple-600 text-white rounded-lg">发送</a>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      users: [],       // 存储从服务器获取的用户列表
      chatUser: null,  // 当前聊天用户的信息
      messages: [],    // 聊天记录
      newMessage: ''   // 待发送的新消息
    };
  },
  methods: {
    // 初始化聊天用户
    initializeChatUser() {
      const userId = this.$route.params.userId;
      this.chatUser = this.users.find(user => user.id === parseInt(userId));
      
      // 模拟已有的聊天记录
      this.messages = [
        { text: '你好！', timestamp: '5分钟前', isSentByUser: false },
        { text: '能看见吗？', timestamp: '4分钟前', isSentByUser: false },
        { text: '看到了！', timestamp: '3分钟前', isSentByUser: true }
      ];
    },
    // 发送消息
    sendMessage() {
      if (this.newMessage.trim() === '') return;

      // 添加新消息到消息列表
      this.messages.push({
        text: this.newMessage,
        timestamp: '刚刚',
        isSentByUser: true
      });

      // 清空输入框
      this.newMessage = '';
    },
    // 获取用户列表
    async fetchUsers() {
      try {
        const response = await axios.get('/api/show-identities/');
        this.users = response.data.map((user, index) => ({
          id: user.id,
          name: user.name,
          avatar: `https://api.multiavatar.com/${user.name}.svg`, 
          lastActive: Math.floor(Math.random() * 60) + 1 
        }));
        
        this.initializeChatUser(); // 在用户列表加载完毕后初始化聊天用户
      } catch (error) {
        console.error('无法获取用户列表:', error);
      }
    }
  },
  mounted() {
    this.fetchUsers(); // 加载用户列表
  }
}
</script>
