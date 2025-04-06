<template>
  <div class="container mx-auto px-4 py-6">
    <!-- 历史记录标题 -->
    <div class="history-header mb-6">
      <h1 class="text-3xl font-bold">发帖历史记录</h1>
      <p class="text-gray-500 mt-2">用户: <strong>{{ nickname }}</strong> | 共 {{ notices.length }} 条记录</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-10">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      <p class="text-gray-500 mt-2">加载中...</p>
    </div>

    <!-- 错误信息 -->
    <div v-else-if="error" class="text-center py-10">
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">获取数据失败!</strong>
        <span class="block sm:inline"> {{ error }}</span>
      </div>
      <button @click="fetchHistory" class="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
        重试
      </button>
    </div>

    <!-- 历史记录列表 -->
    <div v-else-if="notices.length" class="history-content border-t pt-4 mt-6">
      <div v-for="(notice, index) in notices" :key="index"
        class="history-item border-b border-gray-300 pb-4 mb-4 relative hover:bg-gray-50 p-3 rounded">
        <!-- 显示帖子标题、发布时间和审核状态 -->
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-black mt-1 font-semibold">{{ notice.title }}</h2>
            <p class="text-gray-500 mt-1">发布时间: {{ formatDate(notice.timestamp) }}</p>
          </div>
          <div class="status-badge">
            <span v-if="notice.passed === 0" class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
              审核通过
            </span>
            <span v-else-if="notice.passed === 1" class="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
              未通过审核
            </span>
            <span v-else class="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
              审核中
            </span>
          </div>
        </div>

        <!-- 查看详情按钮
        <button @click="viewPostDetail(notice)" 
                class="mt-3 text-blue-600 hover:text-blue-800 flex items-center"
                :disabled="!notice.id">
          <span>{{ notice.id ? '查看详情' : '无法查看 (缺少ID)' }}</span>
          <svg v-if="notice.id" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button> -->
      </div>
    </div>

    <!-- 无历史记录时显示 -->
    <div v-else class="text-center py-10">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-gray-500 mt-4 text-lg">暂无发帖历史记录</p>
      <p class="text-gray-400 mt-2">您还未发布任何帖子，或记录可能在加载中</p>
    </div>

    <!-- 开发调试信息 -->
    <div v-if="showDebug" class="mt-8 p-4 border border-gray-300 rounded bg-gray-50">
      <h3 class="font-bold mb-2">调试信息</h3>
      <div class="text-xs font-mono overflow-x-auto">
        <p>昵称: {{ nickname }}</p>
        <p>记录数量: {{ notices.length }}</p>
        <p>API返回数据: <span v-if="apiResponse">有</span><span v-else>无</span></p>
        <div v-if="apiResponse" class="mt-2">
          <pre>{{ JSON.stringify(apiResponse, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <!-- 返回按钮 -->
    <div class="flex justify-center mt-6">
      <button @click="goBack" class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回主页
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      nickname: '', // 用户昵称
      notices: [], // 历史记录列表
      loading: false, // 加载状态
      error: null, // 错误信息
      showDebug: false, // 是否显示调试信息，可以通过控制台设置为true
      apiResponse: null // 保存API原始响应用于调试
    };
  },
  created() {
    // 从本地存储获取当前用户身份，与发帖功能保持一致
    this.nickname = localStorage.getItem('currentIdentity') || '';
    
    // 获取历史记录
    this.fetchHistory();
    
    // 添加查询参数debug=true以启用调试模式
    const urlParams = new URLSearchParams(window.location.search);
    this.showDebug = urlParams.get('debug') === 'true';
  },
  methods: {
    // 获取历史记录
    async fetchHistory() {
      if (!this.nickname) {
        this.error = '无法获取用户信息，请先登录';
        return;
      }
      
      this.loading = true;
      this.error = null; // 清空之前的错误信息
      
      try {
        console.log('正在获取用户历史记录，昵称:', this.nickname);
        
        const response = await axios.get('/api/posts/notice', {
          params: {
            nickname: this.nickname
          }
        });
        
        console.log('API返回原始数据:', response.data);
        this.apiResponse = response.data; // 保存原始响应用于调试
        
        if (response.data && Array.isArray(response.data.notice_lst)) {
          // 验证和处理通知列表
          this.notices = this.validateAndProcessNotices(response.data.notice_lst);
          console.log('获取到历史记录:', this.notices.length, '条记录');
        } else if (response.data && typeof response.data === 'object') {
          // 尝试找到可能的其他键名
          const possibleKeys = Object.keys(response.data);
          console.log('API返回的顶级键:', possibleKeys);
          
          // 尝试找到可能包含数组的键
          for (const key of possibleKeys) {
            if (Array.isArray(response.data[key])) {
              console.log(`发现数组键 "${key}"，长度:`, response.data[key].length);
              this.notices = this.validateAndProcessNotices(response.data[key]);
              break;
            }
          }
          
          if (this.notices.length === 0) {
            console.log('未找到有效的记录数组，使用空数组');
            this.notices = [];
          }
        } else {
          console.log('API返回数据结构不符合预期');
          this.notices = []; // 确保notices是空数组
          if (!response.data) {
            this.error = 'API返回空数据';
          } else {
            this.error = 'API返回的数据格式不正确';
          }
        }
      } catch (error) {
        console.error('获取历史记录失败:', error);
        
        if (error.response) {
          // 服务器返回错误状态码
          console.error('服务器响应:', error.response.status, error.response.data);
          this.error = `获取历史记录失败: 服务器返回 ${error.response.status} 错误`;
        } else if (error.request) {
          // 请求已发送但没有收到响应
          console.error('未收到服务器响应');
          this.error = '获取历史记录失败: 服务器无响应，请检查网络连接';
        } else {
          // 发送请求时出错
          this.error = '获取历史记录失败: ' + error.message;
        }
      } finally {
        this.loading = false;
      }
    },
    
    // 验证和处理通知列表
    validateAndProcessNotices(notices) {
      if (!Array.isArray(notices)) {
        console.error('无效的通知列表格式:', notices);
        return [];
      }
      
      return notices
        .filter(notice => {
          // 验证每个通知条目是否包含所需的属性
          const isValid = notice && 
                        typeof notice === 'object' && 
                        'timestamp' in notice && 
                        'title' in notice && 
                        'passed' in notice;
          
          if (!isValid) {
            console.warn('发现无效的通知条目:', notice);
          }
          
          return isValid;
        })
        .map(notice => {
          // 确保所有属性都有有效的默认值
          return {
            ...notice,
            title: notice.title || '无标题',
            timestamp: notice.timestamp || 0,
            passed: typeof notice.passed === 'number' ? notice.passed : -1,
            id: notice.id || '' // 确保id存在，即使为空字符串
          };
        })
        .sort((a, b) => b.timestamp - a.timestamp); // 再次按时间从新到旧排序
    },
    
    // 格式化日期
    formatDate(timestamp) {
      if (!timestamp) return '未知时间';
      
      // 检查timestamp是否为数字
      const ts = typeof timestamp === 'string' ? parseInt(timestamp) : timestamp;
      
      if (isNaN(ts)) {
        console.error('无效的时间戳:', timestamp);
        return '无效时间';
      }
      
      try {
        const date = new Date(ts * 1000); // 将秒转为毫秒
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      } catch (e) {
        console.error('格式化日期出错:', e);
        return '时间格式错误';
      }
    },
    
    // 查看帖子详情
    viewPostDetail(notice) {
      if (!notice || !notice.id) {
        console.error('帖子信息不完整:', notice);
        alert('无法查看帖子详情，信息不完整');
        return;
      }
      
      // 跳转到帖子详情页面
      this.$router.push({
        path: `/posts/${notice.id}/1`, // 直接使用路径形式，访问第一层楼
        query: { 
          title: notice.title,
          from: 'history'
        }
      });
    },
    
    // 返回主页
    goBack() {
      this.$router.push('/feed'); // 使用你发帖成功后跳转的路径
    }
  }
};
</script>

<style scoped>
.history-item {
  transition: all 0.3s ease;
}
.history-item:hover {
  background-color: #f9fafb;
}
.status-badge {
  font-weight: 500;
}
</style>