import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import time
import io
import os
import base64
import argparse
import sys
from unittest.mock import patch, MagicMock

from .topic import app, get_db, db_used, get_current_active_user
from .model import Base, TotalTopic, APost

py_dir = os.path.dirname(os.path.abspath(__file__))

# 添加命令行参数
parser = argparse.ArgumentParser(description='运行论坛API测试')
parser.add_argument('--filter', action='store_true', help='是否启用敏感词过滤测试')
args, unknown = parser.parse_known_args()
# 移除已解析的参数，避免与unittest的参数冲突
sys.argv = [sys.argv[0]] + unknown

# 如果启用了过滤测试，导入相关模块
if args.filter:
    from ..wordscheck.checker import words_checker

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class TestForumAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 创建测试数据库表
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = TestingSessionLocal()
        # 定义依赖项覆盖
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        def override_get_current_active_user():
            return None, ["test_user","reply_user","viewer","test"]

        # 正确覆盖原应用的数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user
        db_used[0] = override_get_db
        
        # 如果启用了过滤测试，打印信息
        if args.filter:
            print("初始化敏感词过滤测试环境...")
            # 使用现有的黑名单，不自动添加测试词
            print("使用现有黑名单进行测试")

    @classmethod
    def tearDownClass(cls):
        # 清理测试数据库
        Base.metadata.drop_all(bind=engine)
        try:
            os.remove("./test.db")
        except:
            pass

    def test_full_flow(self):
        ###########################
        # 1. 创建主帖子
        ###########################
        # 生成测试图片
        with open(f"{py_dir}/unittest_img/sjtulogo.png","rb") as f:
            test_image = f.read()
        test_image = io.BytesIO(test_image)
        test_image.name = "test.jpg"
        
        # 发送创建请求
        t1 = time.time()
        response = self.client.post(
            "/create",
            data={
                "nickname": "test_user",
                "title": "Test Topic",
                "tag": ["tech", "python"],
                "content": "Test content"
            },
            files={"pic_lst": ("test.jpg", test_image, "image/jpeg")}
        )
        print(f"create topic cost: {time.time() - t1:.4f} s")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertEqual(create_data["error_code"], 0)
        topic_uuid = uuid.UUID(create_data["uuid"])
        self.assertIsInstance(topic_uuid, uuid.UUID)
        
        ###########################
        # 2. 回复主帖子
        ###########################
        # 等待1秒确保时间戳不同
        time.sleep(1)
        
        # 生成回复图片
        with open(f"{py_dir}/unittest_img/sjtubanner.png","rb") as f:
            reply_image = f.read()
        reply_image = io.BytesIO(reply_image)
        reply_image.name = "reply.png"
        
        # 发送回复请求
        t1 = time.time()
        reply_response = self.client.post(
            f"/{str(topic_uuid)}/reply",
            data={
                "author": "reply_user",
                "content": "Test reply",
                "reply_to": "0"
            },
            files={"pic_lst": ("reply.png", reply_image, "image/png")}
        )
        print(f"reply topic cost: {time.time() - t1:.4f} s")
        
        # 验证回复成功
        self.assertEqual(reply_response.status_code, 200)
        self.assertEqual(reply_response.json()["error_code"], 0)
        
        ###########################
        # 3. 获取楼层信息
        ###########################
        time.sleep(1)
        get_response = self.client.get(
            f"/{str(topic_uuid)}/1",
            params={"nickname": "viewer"}
        )
        
        # 验证响应结构
        self.assertEqual(get_response.status_code, 200)
        floors_data = get_response.json()
        
        # 验证基础结构
        self.assertIn("floors", floors_data)
        self.assertEqual(len(floors_data["floors"]), 2)
        
        # 验证主楼层信息
        main_floor = floors_data["floors"][0]
        self.assertEqual(main_floor["nickname"], "test_user")
        self.assertEqual(main_floor["content"], "Test content")
        self.assertEqual(main_floor["back_to"], 0, msg=f"{main_floor=}")
        self.assertEqual(main_floor["index"], 1, msg=f"{floors_data=}")
        self.assertEqual(len(main_floor["pic_lst"]), 1)
        self.assertEqual(main_floor["pic_lst"][0], base64.b64encode(test_image.getvalue()).decode())
        self.assertEqual(main_floor["like_num"], 0)
        self.assertEqual(main_floor["is_liked"], 0)
        
        # 验证回复楼层
        reply = floors_data["floors"][1]
        self.assertEqual(reply["nickname"], "reply_user")
        self.assertEqual(reply["content"], "Test reply")
        self.assertEqual(len(reply["pic_lst"]), 1)
        self.assertEqual(reply["pic_lst"][0], base64.b64encode(reply_image.getvalue()).decode())
        self.assertEqual(reply["like_num"], 0)
        
        # 验证时间戳顺序
        self.assertLess(main_floor["create_time"], reply["create_time"])

        ###########################
        # 4. 验证热门帖子
        ###########################
        hot_response = self.client.get("/hot")
        hot_posts = hot_response.json()["posts"]
        self.assertEqual(len(hot_posts), 1)
        self.assertEqual(hot_posts[0]["title"], "Test Topic")
        self.assertEqual(hot_posts[0]["view_times"], 1)

        ###########################
        # 5. 验证点赞功能
        ###########################
        # 点赞主楼层
        like_response = self.client.post(
            "/like",
            json={"nickname": "viewer", "uuid": str(topic_uuid), "floor": 1}
        )
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(like_response.json()["error_code"], 0, msg=f"{like_response.json()=}")

        # 验证点赞成功

        get_response = self.client.get(f"/{str(topic_uuid)}/1", params={"nickname": "viewer"})
        floors_data = get_response.json()
        main_floor = floors_data["floors"][0]
        self.assertEqual(main_floor["like_num"], 1)
        self.assertEqual(main_floor["is_liked"], 1, msg=f"{floors_data=}")
        # 点赞回复楼层
        like_response = self.client.post(
            "/like",
            json={"nickname": "viewer", "uuid": str(topic_uuid), "floor": 2}
        )
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(like_response.json()["error_code"], 0)
        get_response = self.client.get(f"/{str(topic_uuid)}/1", params={"nickname": "viewer"})
        floors_data = get_response.json()
        reply = floors_data["floors"][1]
        self.assertEqual(reply["like_num"], 1)
        self.assertEqual(reply["is_liked"], 1)

        ###########################
        # 6. 验证取消点赞功能
        ###########################
        # 取消点赞主楼层
        cancel_like_response = self.client.post(
            "/cancel-like",
            json={"nickname": "viewer", "uuid": str(topic_uuid), "floor": 1}
        )
        self.assertEqual(cancel_like_response.status_code, 200)
        self.assertEqual(cancel_like_response.json()["error_code"], 0, msg=f"{cancel_like_response.json()=}")

        # 验证取消点赞成功
        get_response = self.client.get(f"/{str(topic_uuid)}/1", params={"nickname": "viewer"})
        floors_data = get_response.json()
        main_floor = floors_data["floors"][0]
        self.assertEqual(main_floor["like_num"], 0)
        self.assertEqual(main_floor["is_liked"], 0)
        # 取消点赞回复楼层
        cancel_like_response = self.client.post(
            "/cancel-like",
            json={"nickname": "viewer", "uuid": str(topic_uuid), "floor": 2}
        )
        self.assertEqual(cancel_like_response.status_code, 200)
        self.assertEqual(cancel_like_response.json()["error_code"], 0)

        ###########################
        # 7. 测试notice功能
        ###########################
        # 测试通知
        response = self.client.get("/notice", params={"nickname": "reply_user"})
        notice_lst = response.json()["floors"]
        self.assertEqual(len(notice_lst), 1)
        self.assertEqual(notice_lst[0]["passed"], 0)


        
    def test_invalid_uuid(self):
        # 测试无效UUID的情况
        invalid_uuid = "invalid-uuid-123"
        
        # 获取请求
        response = self.client.get(
            f"/{invalid_uuid}/1",
            params={"nickname": "test"}
        )
        
        # 验证错误响应
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertEqual(error_data["detail"], "非法UUID格式")

    def test_post_order(self):
        # 创建测试数据
        topic1 = TotalTopic(
            author_name="user1",
            topic_title="Old Post",
            update_time=time.time()
        )
        topic2 = TotalTopic(
            author_name="user2",
            topic_title="New Post",
            update_time=time.time()+100
        )
        self.db.add_all([topic1, topic2])
        self.db.commit()

        # 验证排序
        response = self.client.get("/")
        posts = response.json()["posts"]
        self.assertEqual(posts[0]["title"], "New Post", msg=f"{posts=}")
        self.assertEqual(posts[1]["title"], "Old Post")
    
    @unittest.skipIf(not args.filter, "敏感词过滤测试已关闭")
    def z_test_content_filter_blacklist(self):
        """测试黑名单敏感词过滤功能"""
        print("\n===== 开始敏感词过滤测试 =====")
        
        # 生成测试图片
        test_image = io.BytesIO(b"fake image data")
        test_image.name = "test.jpg"
        
        # 发送创建包含敏感词的帖子请求
        print("测试发布包含黑名单敏感词的帖子...")
        response = self.client.post(
            "/create",
            data={
                "nickname": "test_user",
                "title": "敏感内容测试",
                "tag": ["test"],
                "content": "上海交通大学"  # 包含黑名单敏感词
            },
            files={"pic_lst": ("test.jpg", test_image, "image/jpeg")}
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertEqual(create_data["error_code"], 0)
        topic_uuid = uuid.UUID(create_data["uuid"])
        
        # 等待后台任务完成
        print("等待敏感词检测完成...")
        time.sleep(2)
        
        # 查询帖子状态
        db = TestingSessionLocal()
        post = db.query(APost).filter(APost.parent_topic_uuid == topic_uuid).first()
        db.close()
        
        # 验证帖子被标记为不合规 (visible_state=1)
        self.assertIsNotNone(post, "未找到创建的帖子")
        self.assertEqual(post.visible_state, 1, 
                       f"敏感帖子未被正确标记为不合规: visible_state={post.visible_state}")
        print("敏感词黑名单过滤测试通过！")
    
    @unittest.skipIf(not args.filter, "敏感词过滤测试已关闭")
    @patch('requests.post')
    def z_test_content_filter_service(self, mock_post):
        """测试敏感词服务过滤功能"""
        # 模拟敏感词服务的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "msg": "检测成功",
            "return_str": "这个帖子包含**内容，应该被过滤",
            "word_list": [{
                "keyword": "违规",
                "category": "违禁",
                "position": "7-8",
                "level": "高"
            }]
        }
        mock_post.return_value = mock_response
        
        # 生成测试图片
        test_image = io.BytesIO(b"fake image data")
        test_image.name = "test.jpg"
        
        # 发送创建帖子请求
        print("测试发布需要敏感词服务检测的帖子...")
        response = self.client.post(
            "/create",
            data={
                "nickname": "test_user",
                "title": "内容检测测试",
                "tag": ["test"],
                "content": "我操你妈了个逼"  # 包含敏感词服务会检测到的内容
            },
            files={"pic_lst": ("test.jpg", test_image, "image/jpeg")}
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertEqual(create_data["error_code"], 0)
        topic_uuid = uuid.UUID(create_data["uuid"])
        
        # 等待后台任务完成
        print("等待敏感词检测完成...")
        time.sleep(2)
        
        # 查询帖子状态
        db = TestingSessionLocal()
        post = db.query(APost).filter(APost.parent_topic_uuid == topic_uuid).first()
        db.close()
        
        # 验证帖子被标记为不合规 (visible_state=1)
        self.assertIsNotNone(post, "未找到创建的帖子")
        self.assertEqual(post.visible_state, 1, 
                       f"敏感帖子未被正确标记为不合规: visible_state={post.visible_state}")
        print("敏感词服务检测测试通过！")

    @unittest.skipIf(not args.filter, "敏感词过滤测试已关闭")
    def z_test_content_filter_normal(self):
        """测试正常内容通过过滤"""
        # 生成测试图片
        test_image = io.BytesIO(b"fake image data")
        test_image.name = "test.jpg"
        
        # 发送创建正常帖子请求
        print("测试发布正常内容帖子...")
        response = self.client.post(
            "/create",
            data={
                "nickname": "test_user",
                "title": "正常内容测试",
                "tag": ["test"],
                "content": "这是一个正常的帖子，内容健康，不包含任何敏感词"
            },
            files={"pic_lst": ("test.jpg", test_image, "image/jpeg")}
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertEqual(create_data["error_code"], 0)
        topic_uuid = uuid.UUID(create_data["uuid"])
        
        # 等待后台任务完成
        print("等待内容检测完成...")
        time.sleep(2)
        
        # 查询帖子状态
        db = TestingSessionLocal()
        post = db.query(APost).filter(APost.parent_topic_uuid == topic_uuid).first()
        db.close()
        
        # 验证帖子被标记为合规 (visible_state=0)
        self.assertIsNotNone(post, "未找到创建的帖子")
        self.assertEqual(post.visible_state, 0, 
                       f"正常帖子被错误标记为不合规: visible_state={post.visible_state}")
        print("正常内容过滤测试通过！")


if __name__ == '__main__':
    unittest.main()