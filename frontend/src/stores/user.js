import { defineStore } from 'pinia';
import axios from 'axios';

export const useUserStore = defineStore({
    id: 'user',

    state: () => ({
        user: {
            isAuthenticated: false,
            id: null, // 用户 ID
            access: null, // Access Token
            refresh: null, // Refresh Token
            lastUsedIdentity: null, // 最近使用的身份
        }
    }),

    actions: {
        // 初始化 Store，读取本地存储中的 Token 和身份信息
        initStore() {
            const accessToken = localStorage.getItem('user.access');
            const refreshToken = localStorage.getItem('user.refresh');

            // 检查 token 是否存在
            if (accessToken && refreshToken) {
                this.user.access = accessToken;
                this.user.refresh = refreshToken;
                this.user.id = localStorage.getItem('user.id');
                this.user.lastUsedIdentity = localStorage.getItem('user.lastUsedIdentity');
                this.user.isAuthenticated = true;

                // 设置全局 Axios 头部
                axios.defaults.headers.common["Authorization"] = "Bearer " + this.user.access;

                // 初始化时尝试刷新 token 确保会话有效
                this.refreshToken();
            } else {
                // 没有 token，用户未登录
                this.removeToken();
            }
        },

        // 设置 Token 信息并更新本地存储
        setToken(data) {
            this.user.access = data.access;
            this.user.refresh = data.refresh;
            this.user.isAuthenticated = true;

            // 存储 token 到 localStorage
            localStorage.setItem('user.access', data.access);
            localStorage.setItem('user.refresh', data.refresh);

            // 设置全局 Axios 头部
            axios.defaults.headers.common["Authorization"] = "Bearer " + data.access;

            console.log('Token set successfully:', this.user);
        },

        // 设置用户信息，包括最近使用的身份，并更新本地存储
        setUserInfo(user) {
            this.user.id = user.id;
            this.user.lastUsedIdentity = user.lastUsedIdentity;

            // 存储用户信息到 localStorage
            localStorage.setItem('user.id', user.id);
            localStorage.setItem('user.lastUsedIdentity', user.lastUsedIdentity);

            console.log('User info set:', this.user);
        },

        // 清除 Token 信息并退出登录
        removeToken() {
            this.user.access = null;
            this.user.refresh = null;
            this.user.isAuthenticated = false;
            this.user.id = null;
            this.user.lastUsedIdentity = null;

            // 清除 localStorage 中的信息
            localStorage.removeItem('user.access');
            localStorage.removeItem('user.refresh');
            localStorage.removeItem('user.id');
            localStorage.removeItem('user.lastUsedIdentity');

            // 清除 Axios 头部
            delete axios.defaults.headers.common["Authorization"];

            console.log('Token removed and user logged out.');
        },

        // 刷新 Access Token
        refreshToken() {
            const refreshToken = this.user.refresh;

            if (!refreshToken) {
                console.error("Refresh token is missing or undefined");
                this.removeToken(); // 清除无效的 token
                return;
            }

            axios.post('/api/token/refresh/', { refresh: refreshToken })
                .then((response) => {
                    this.user.access = response.data.access;
                    localStorage.setItem('user.access', response.data.access);

                    // 更新 Authorization 头
                    axios.defaults.headers.common["Authorization"] = "Bearer " + response.data.access;

                    console.log("Token refreshed successfully.");
                })
                .catch((error) => {
                    console.error("Token refresh failed:", error);
                    this.removeToken(); // 如果刷新失败，移除无效的 token
                });
        },

        // 清空用户信息并退出登录
        clearUser() {
            this.removeToken(); // 清除 token 信息
            this.user.isAuthenticated = false;
            console.log("User logged out and cleared from the store.");
        }
    }
});
