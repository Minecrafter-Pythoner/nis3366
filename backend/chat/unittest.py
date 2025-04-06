import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

from .chat import app, get_db, config_dic, get_current_active_user
from ..topic.model import APost
from ..login.models import AnonymousIdentity
from ..login.database import SessionLocal, Base
from .models import AnonymousIdentity, ChatInvitation, Chat, Message
import os


# 配置测试数据库
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# 依赖覆盖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_active_user():
    return None, [f"user{i}" for i in range(1,5)]

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app)

class TestChatAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = TestingSessionLocal()
        
        # 清空表
        cls.db.query(Message).delete()
        cls.db.query(Chat).delete()
        cls.db.query(ChatInvitation).delete()
        cls.db.query(AnonymousIdentity).delete()
        
        
        
        cls.db.commit()
        cls.client = TestClient(app)
    
    @classmethod
    def tearDownClass(cls):
        cls.db.query(Message).delete()
        cls.db.query(Chat).delete()
        cls.db.query(ChatInvitation).delete()
        cls.db.query(AnonymousIdentity).delete()
        cls.db.commit()
        cls.db.close()
        try:
            os.remove("./test.db")
        except:
            pass
    
    def tearDown(self):
        self.db.query(Message).delete()
        self.db.query(Chat).delete()
        self.db.query(ChatInvitation).delete()
        self.db.query(AnonymousIdentity).delete()
        self.db.commit()
        self.db.close()
    
    def setUp(self):
        self.user1 = AnonymousIdentity(nickname="user1", user_id=1, id=1)
        self.user2 = AnonymousIdentity(nickname="user2", user_id=2, id=2)
        self.user3 = AnonymousIdentity(nickname="user3", user_id=3, id=3)
        self.user4 = AnonymousIdentity(nickname="user4", user_id=4, id=4)

        self.db.add_all([self.user1, self.user2, self.user3, self.user4])
        self.db.commit()
        # self.client = TestClient(app)
    
    def test_create_chat_invite(self):
        # 测试创建邀请
        response = self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"error_code": 0, "message": "Invite sent successfully"})
        
        # 测试重复邀请
        response = self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello again",
                "publickey": "publickey1"
            }
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invite already exists", response.json()["detail"])
    
    def test_get_chat_invites(self):
        # 创建邀请
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        # 测试获取邀请
        response = self.client.get("/get-invite?nickname=user2")
        self.assertEqual(response.status_code, 200)
        
        invites = response.json()["invite_message_lst"]
        self.assertEqual(len(invites), 1)
        self.assertEqual(invites[0]["src_nickname"], "user1")
        self.assertIn("timestamp", invites[0])
        self.assertEqual(invites[0]["message"], "Hello, want to chat?")
        self.assertEqual(invites[0]["publickey"], "publickey1")
    
    def test_get_invite_state(self):
        # 创建邀请
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        # 测试获取邀请状态
        response = self.client.get("/invite-state?nickname=user1")
        self.assertEqual(response.status_code, 200)
        
        states = response.json()["state_lst"]

        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["state_code"], 0)
    
    def test_choose_chat_invite(self):
        # 创建邀请
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        # 接受邀请
        response = self.client.post(
            "/choose",
            json={
                "choice": 0,
                "src_nickname": "user1",
                "publickey": "publickey2",
                "dst_nickname": "user2"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"error_code": 0, "message": "Choice processed successfully"})
        
        # 检查聊天记录是否创建
        db = TestingSessionLocal()
        chat = db.query(Chat).filter(
            (Chat.src_identity_id == 1) & (Chat.dst_identity_id == 2)
        ).first()
        
        self.assertIsNotNone(chat)
        db.close()
    
    def test_send_chat_message(self):
        # 创建邀请并接受
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        self.client.post(
            "/choose",
            json={
                "choice": 0,
                "src_nickname": "user1",
                "publickey": "publickey2",
                "dst_nickname": "user2"
            }
        )
        
        # 发送消息
        response = self.client.post(
            "/send",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "This is a test message"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"error_code": 0, "message": "Message sent successfully"})
    
    def test_receive_chat_messages(self):
        # 创建邀请并接受
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        self.client.post(
            "/choose",
            json={
                "choice": 0,
                "src_nickname": "user1",
                "publickey": "publickey2",
                "dst_nickname": "user2"
            }
        )
        
        # 发送消息
        self.client.post(
            "/send",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "This is a test message"
            }
        )
        
        # 查收消息
        response = self.client.get("/receive?nickname=user1")
        self.assertEqual(response.status_code, 200)
        
        messages = response.json()["message_lst"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["src_nickname"], "user2")
        self.assertEqual(messages[0]["last_message"], "This is a test message")
    
    def test_get_chat_messages_with_target(self):
        # 创建邀请并接受
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        self.client.post(
            "/choose",
            json={
                "choice": 0,
                "src_nickname": "user1",
                "publickey": "publickey2",
                "dst_nickname": "user2"
            }
        )
        
        # 发送消息
        self.client.post(
            "/send",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "This is a test message"
            }
        )
        
        # 查看与指定人的私聊信息
        response = self.client.get("/user2?nickname=user1")
        self.assertEqual(response.status_code, 200)
        
        messages = response.json()["message_lst"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["message"], "This is a test message")
        self.assertEqual(messages[0]["owner"], 0)
    
    def test_get_target_publickey(self):
        # 创建邀请并接受
        self.client.post(
            "/invite",
            json={
                "src_nickname": "user1",
                "dst_nickname": "user2",
                "message": "Hello, want to chat?",
                "publickey": "publickey1"
            }
        )
        
        self.client.post(
            "/choose",
            json={
                "choice": 0,
                "src_nickname": "user1",
                "publickey": "publickey2",
                "dst_nickname": "user2"
            }
        )
        
        # 查看公钥
        response = self.client.get("/publickey/user2?nickname=user1")
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.json(), {
            "error_code": 0,
            "msg": "Success",
            "publickey": "publickey2"
        })
    
    def test_recommend_people(self):
        self.chat1 = Chat(src_identity_id=self.user1.id, dst_identity_id=self.user2.id, last_update=time.time()-3600)
        self.chat2 = Chat(src_identity_id=self.user1.id, dst_identity_id=self.user3.id, last_update=time.time())
        self.db.add_all([self.chat1, self.chat2])
        self.db.commit()
        
        # 添加测试邀请记录
        self.invitation1 = ChatInvitation(src_identity_id=self.user1.id, dst_identity_id=self.user4.id)
        self.db.add(self.invitation1)
        self.db.commit()
        
        # 添加测试帖子
        self.post1 = APost(content="Test post", like_set=["user2", "user3"])
        self.db.add(self.post1)
        self.db.commit()

        # 测试推荐逻辑
        response = self.client.get("/recommend?nickname=user1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 验证返回的推荐列表长度是否符合配置
        self.assertEqual(len(data["recommend_lst"]), 2)
        
        # 验证推荐列表中不包含排除的用户
        exclude_users = ["user1", "user4"]
        for user in data["recommend_lst"]:
            self.assertNotIn(user, exclude_users)
        
        # 验证推荐列表中包含与用户1有聊天记录的用户
        self.assertIn("user2", data["recommend_lst"])
        self.assertIn("user3", data["recommend_lst"])

if __name__ == '__main__':
    unittest.main()