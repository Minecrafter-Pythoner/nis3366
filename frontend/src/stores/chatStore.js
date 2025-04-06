import { defineStore } from 'pinia';
import axios from 'axios';
import { useUserStore } from './user';
import EC from 'elliptic';
import CryptoJS from 'crypto-js';  // 导入用于AES加密的库

const ec = new EC.ec('secp256k1');

export const useChatStore = defineStore('chat', {
    state: () => ({
        invites: [],
        messages: [],
        inviteStates: [],
        chatError: null,
        currentChatUser: null,
        approvedFriends: [],
    }),
    actions: {
        handleError(error, customMessage) {
            console.error(customMessage, error);
            this.chatError = customMessage || '操作失败';
        },

        setup() {
            const currentIdentity = localStorage.getItem('currentIdentity');
            this.loadFriendsForCurrentIdentity(currentIdentity);
        },

        loadFriendsForCurrentIdentity(nickname) {
            const savedFriends = JSON.parse(localStorage.getItem(`approvedFriends_${nickname}`)) || [];
            this.approvedFriends = savedFriends;
        },

        switchIdentity(newNickname) {
            localStorage.setItem('currentIdentity', newNickname);
            this.loadFriendsForCurrentIdentity(newNickname);
        },

        getAuthHeaders() {
            const userStore = useUserStore();
            const token = userStore.user.access;
            return token ? { Authorization: `Bearer ${token}` } : {};
        },

        // 发送私聊邀请，包含公钥
        async sendInvite(srcNickname, dstNickname, message, publicKey) {
            try {
                const response = await axios.post('/api/chat/invite', {
                    src_nickname: srcNickname,
                    dst_nickname: dstNickname,
                    message,
                    publickey: publicKey
                }, {
                    headers: this.getAuthHeaders()
                });

                if (response.data.error_code === 0) {
                    alert('私聊邀请发送成功');
                } else {
                    this.chatError = response.data.msg;
                    alert('发送私聊邀请失败: ' + response.data.msg);
                }
            } catch (error) {
                this.handleError(error, '发送私聊邀请失败');
            }
        },

        // 获取收到的私聊邀请
        async fetchInvites(nickname) {
            try {
                const response = await axios.get('/api/chat/get-invite', {
                    params: { nickname },
                    headers: this.getAuthHeaders()
                });
                this.invites = response.data.invite_message_lst || [];
            } catch (error) {
                this.handleError(error, '获取邀请失败');
            }
        },

        // 获取邀请状态列表
        async fetchInviteStates(nickname) {
            try {
                const response = await axios.get('/api/chat/invite-state', {
                    params: { nickname },
                    headers: this.getAuthHeaders()
                });
                this.inviteStates = response.data.state_lst || [];
            } catch (error) {
                this.handleError(error, '获取邀请状态失败');
            }
        },

        // 处理私聊邀请（接受或拒绝）
        async handleInvite(choice, srcNickname, dstNickname) {
            try {
                const requestData = {
                    choice,
                    src_nickname: srcNickname,
                    dst_nickname: dstNickname
                };

                // 如果选择接受邀请 (choice === 0)，需要提供接收者的公钥
                if (choice === 0) {
                    const publicKey = localStorage.getItem(`identity_${dstNickname}_publicKey`);
                    if (!publicKey) {
                        alert('未找到当前身份的公钥，请重新生成身份密钥对');
                        return;
                    }
                    requestData.publickey = publicKey;
                }

                const response = await axios.post('/api/chat/choose', requestData, {
                    headers: this.getAuthHeaders()
                });

                if (response.data.error_code === 0) {
                    alert(choice === 0 ? '已接受邀请' : '已拒绝邀请');
                    if (choice === 0) {
                        this.currentChatUser = srcNickname;

                        // 将 dst_nickname 添加到 FriendList
                        if (!this.approvedFriends.includes(srcNickname)) {
                            this.approvedFriends.push(srcNickname);
                            const currentIdentity = localStorage.getItem('currentIdentity');
                            localStorage.setItem(`approvedFriends_${currentIdentity}`, JSON.stringify(this.approvedFriends));
                        }

                        // 这里添加对方的好友列表
                        const oppositeApprovedFriends = JSON.parse(localStorage.getItem(`approvedFriends_${srcNickname}`)) || [];
                        if (!oppositeApprovedFriends.includes(dstNickname)) {
                            oppositeApprovedFriends.push(dstNickname);
                            localStorage.setItem(`approvedFriends_${srcNickname}`, JSON.stringify(oppositeApprovedFriends));
                        }
                        await this.fetchInvites(dstNickname);
                    }
                } else {
                    this.chatError = response.data.message;
                }
            } catch (error) {
                this.handleError(error, '处理邀请失败');
            }
        },

        async fetchPublicKey(nickname, currentIdentity) {
            try {
                const response = await axios.get(`/api/chat/publickey/${nickname}`, {
                    params: { nickname:currentIdentity },
                    headers: this.getAuthHeaders(),
                });

                if (response.data.error_code === 0) {
                    const publicKey = response.data.publickey;
                    localStorage.setItem(`identity_${nickname}_publicKey`, publicKey);
                    return publicKey;
                } else {
                    this.chatError = response.data.msg;
                    return null;
                }
            } catch (error) {
                this.handleError(error, '获取对方公钥失败');
                return null;
            }
        },

        // 利用ECDH生成共享密钥
        generateSharedKey(publicKey, privateKey) {
            if (!publicKey || !privateKey) {
                console.error('公钥或私钥未找到，无法生成共享密钥');
                throw new Error('公钥或私钥未找到');
            }

            try {
                const key = ec.keyFromPrivate(privateKey, 'hex');
                const pubKey = ec.keyFromPublic(publicKey, 'hex');
                const sharedSecret = key.derive(pubKey.getPublic()).toString(16);
                return sharedSecret;
            } catch (error) {
                console.error('共享密钥生成失败:', error);
                throw new Error('共享密钥生成失败');
            }
        },


        // 使用共享密钥进行AES加密
        encryptMessage(sharedKey, message) {
            return CryptoJS.AES.encrypt(message, sharedKey).toString();
        },

        // 使用共享密钥进行AES解密
        decryptMessage(sharedKey, encryptedMessage) {
            const bytes = CryptoJS.AES.decrypt(encryptedMessage, sharedKey);
            return bytes.toString(CryptoJS.enc.Utf8);
        },

        async sendMessage(srcNickname, dstNickname, message) {
            if (!message || message.trim() === '') {
                alert('消息不能为空');
                return;
            }

            // 获取对方的公钥
            let publicKey = localStorage.getItem(`identity_${dstNickname}_publicKey`);
            //let publicKey = await this.fetchPublicKey(dstNickname, srcNickname);
            if (!publicKey) {
                publicKey = await this.fetchPublicKey(dstNickname, srcNickname);
                if (!publicKey) {
                    alert('未找到对方的公钥，无法发送消息');
                    return;
                }
            }

            // 获取当前身份的私钥
            const privateKey = localStorage.getItem(`identity_${srcNickname}_privateKey`);
            if (!privateKey) {
                alert('未找到当前身份的私钥');
                return;
            }

            // 生成共享密钥
            const sharedKey = this.generateSharedKey(publicKey, privateKey);

            // 使用共享密钥加密消息
            const encryptedMessage = this.encryptMessage(sharedKey, message);

            try {
                const response = await axios.post('/api/chat/send', {
                    src_nickname: srcNickname,
                    dst_nickname: dstNickname,
                    message: encryptedMessage,
                }, {
                    headers: this.getAuthHeaders(),
                });

                if (response.data.error_code === 0) {
                    alert('消息发送成功');
                    this.messages.push({
                        src_nickname: srcNickname,
                        last_message: encryptedMessage,
                        timestamp: new Date().toISOString(),
                    });
                } else {
                    this.chatError = response.data.message;
                }
            } catch (error) {
                this.handleError(error, '发送消息失败');
            }
        },

        async fetchMessages(nickname) {
            try {
                const response = await axios.get('/api/chat/receive', {
                    params: { nickname },
                    headers: this.getAuthHeaders(),
                });

                // 获取当前身份的私钥
                const privateKey = localStorage.getItem(`identity_${nickname}_privateKey`);
                if (!privateKey) {
                    alert('未找到当前身份的私钥，无法解密消息');
                    return;
                }

                // 解密所有消息
                this.messages = await Promise.all(
                    (response.data.message_lst || []).map(async (msg) => {
                        // 获取共享密钥
                        const publicKey = localStorage.getItem(`identity_${msg.src_nickname}_publicKey`);
                        const sharedKey = this.generateSharedKey(publicKey, privateKey);
                        const decryptedMessage = this.decryptMessage(sharedKey, msg.last_message);
                        return {
                            ...msg,
                            last_message: decryptedMessage,
                        };
                    })
                );
            } catch (error) {
                this.handleError(error, '获取消息失败');
            }
        },

        async fetchChatWithUser(targetNickname, currentUserNickname) {
            try {
                const response = await axios.get(`/api/chat/${targetNickname}`, {
                    params: { nickname: currentUserNickname },
                    headers: this.getAuthHeaders(),
                });

                const privateKey = localStorage.getItem(`identity_${currentUserNickname}_privateKey`);
                if (!privateKey) {
                    alert('未找到当前身份的私钥，无法解密聊天记录');
                    return;
                }

                if (1) {
                    //先按照时间戳排序
                    response.data.message_lst.sort((a, b) => a.timestamp - b.timestamp);
                    this.messages = await Promise.all(
                        response.data.message_lst.map(async (msg) => {
                            // 获取并验证公钥
                            const publicKey = localStorage.getItem(`identity_${targetNickname}_publicKey`);
                            if (!publicKey) {
                                console.error('未找到对方的公钥，无法解密消息');
                                return { ...msg, message: '[解密失败：公钥缺失]' };
                            }

                            try {
                                // 生成共享密钥并解密消息
                                const sharedKey = this.generateSharedKey(publicKey, privateKey);
                                const decryptedMessage = this.decryptMessage(sharedKey, msg.message); // 使用 msg.message 代替 msg.last_message
                                return { ...msg, message: decryptedMessage };
                            } catch (error) {
                                console.error('解密消息失败:', error);
                                return { ...msg, message: '[解密失败]' };
                            }
                        })
                    );
                }
            } catch (error) {
                this.handleError(error, '获取私聊记录失败');
            }
        }


    },
});
