<template>
  <div class="max-w-7xl mx-auto p-12 bg-white border border-gray-200 rounded-lg">
    <h1 class="mb-6 text-2xl">发布话题</h1>
    <form class="space-y-6" @submit.prevent="submitForm">

      <div>
        <label for="tag">选择板块：</label><br>
        <select name="tag" v-model="form.tag" class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
          <option value="share">谈笑风生</option>
          <option value="ask">有求必应</option>
          <option value="advertise">广而告之</option>
          <option value="aboutus">日醒吾身</option>
        </select>
      </div>

      <div>
        <label for="title">标题：</label><br>
        <input type="text" v-model="form.title" placeholder="请输入标题"
          class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
      </div>

      <div>
        <label for="content">内容：</label><br>
        <div id="editor" class="mt-2 py-4 px-6 border border-gray-200 rounded-lg"></div>
      </div>

      <div>
        <label for="pic_lst">上传文件：</label><br>
        <input type="file" multiple @change="handleFiles" accept="image/*"
          class="w-full mt-2 py-4 px-6 border border-gray-200 rounded-lg">
      </div>

      <div>
        <button class="py-4 px-6 bg-purple-600 text-white rounded-lg" type="submit">提交</button>
      </div>

      <div v-if="error" class="text-red-500">{{ error }}</div>
    </form>
    <!-- 展示提交后的内容 -->
    <!-- <div v-if="floors.length > 0" class="mt-6">
      <h2 class="text-xl mb-4">帖子内容</h2>
      <div v-for="floor in floors" :key="floor.id" class="border-t border-gray-200 py-4">
        <p><strong>{{ floor.nickname }}</strong>: {{ floor.message }}</p>
      </div>
    </div> -->
  </div>
</template>

<script>
import axios from 'axios';
import { Editor } from '@toast-ui/editor';
import '@toast-ui/editor/dist/toastui-editor.css';

export default {
  data() {
    return {
      form: {
        nickname: 'default', // 默认昵称
        title: '',
        tag: [],
        content: '',
        pic_lst: [], // 图片列表
      },
      editorInstance: null,
      error: '',
      floors: [], // 添加floors初始化
    };
  },
  mounted() {
    this.editorInstance = new Editor({
      el: document.querySelector('#editor'),
      height: '500px',
      initialEditType: 'markdown',
      previewStyle: 'vertical',
    });
  },
  methods: {
    handleFiles(event) {
      this.form.pic_lst = Array.from(event.target.files); // 获取文件列表
    },
    // 添加清除错误的方法
    clearError() {
      setTimeout(() => {
        this.error = '';
      }, 3000);
    },
    async submitForm() {
      this.form.content = this.editorInstance.getMarkdown(); // 获取 Markdown 内容
      this.error = ''; // 清空错误信息

      // 验证表单
      if (!this.form.title) {
        this.error = '请输入标题';
        return;
      }
      if (!this.form.tag) { // 修改：检查tag是否为空值，不检查length
        this.error = '请选择标签';
        return;
      }
      if (this.form.content.length < 10) {
        this.error = '内容至少包含10个字符';
        return;
      }
      if (this.form.content.length > 1024 * 1024) {
        this.error = '内容过长';
        return;
      }
      // 检查文件大小
      for (const file of this.form.pic_lst) {
        if (file.size > 1 * 1024 * 1024) { // 检查文件大小是否大于1MB
          this.error = '上传的图片不能大于1MB';
          return;
        }
      }

      const formData = new FormData();
      formData.append('nickname', localStorage.getItem('currentIdentity'));
      formData.append('title', this.form.title);
      formData.append('tag', JSON.stringify(this.form.tag)); // 将标签列表转为字符串
      formData.append('content', this.form.content);

      // 添加图片
      this.form.pic_lst.forEach((file) => {
        formData.append('pic_lst', file);
      });

      // try {
      //   const response = await axios.post('/api/posts/create', formData, {
      //     headers: {
      //       'Content-Type': 'multipart/form-data',
      //     },
      //   });

      //   if (response.data.error_code === 0) {
      //     alert('发帖成功！');
      //     const uuid = response.data.uuid; // 获取帖子 UUID
      //     const base_floor = 1; // 第一层楼为1
      //     // alert(`提交成功！${uuid}/${base_floor}`);

      //     try {
      //       const topicResponse = await axios.get(`/api/posts/${uuid}/${base_floor}`); 
      //       this.floors = topicResponse.data.floors; // Assign floors to comments
      //       // alert(this.floors.length > 0 ? this.floors[0].nickname : '没有楼层');
      //     } catch (err) {
      //       console.error('获取楼层信息失败', err);
      //       // 不设置错误信息，因为发帖已经成功
      //     }

      //     this.error = ''; // 确保错误信息被清空
      //     this.$router.push(`/feed`); //返回主页
      //   } else {
      //     this.error = response.data.msg || '提交失败，请重试';
      //     this.clearError(); // 现在可以调用这个方法了
      //   }
      // } catch (error) {
      //   console.error('提交失败', error);
      //   this.error = '提交失败，请重试';
      //   this.clearError(); // 现在可以调用这个方法了
      // }
      try {
        const response = await axios.post('/api/posts/create', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.data.error_code === 0) {
          alert('发帖成功！');
          const uuid = response.data.uuid; // 获取帖子 UUID

          // 直接跳转到帖子页面或主页
          this.$router.push(`/feed`); // 或者使用 this.$router.push(`/post/${uuid}`); 直接跳转到新帖子
        } else {
          this.error = response.data.msg || '提交失败，请重试';
          this.clearError();
        }
      } catch (error) {
        console.error('提交失败', error);
        this.error = '提交失败，请重试';
        this.clearError();
      }
    },
  },
};
</script>

<style scoped>
/* 添加必要的样式 */
</style>