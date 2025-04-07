# test_text_filter.py
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import logging

# 配置日志级别，减少不必要的输出
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# 导入WordsChecker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from backend.wordscheck.checker import WordsChecker

class TestTextFilter(unittest.TestCase):
    """测试文本过滤的三级过滤机制"""
    
    def setUp(self):
        """测试前准备工作"""
        # 创建WordsChecker实例，启用大模型验证
        self.checker = WordsChecker(
            base_url="http://localhost:8080",  
            use_llm=True,
            deepseek_api_key="sk-ac1d011dbd6c48f58f6b2c70ba7d798e"
        )
        
        # 添加一些测试用的黑名单词
        self.checker.blacklist = ["黑名单词汇", "违禁", "色情"]
        
        # 替换备用关键词列表
        self.checker.backup_keywords = ["敏感", "负面", "违规"]
    
    def test_blacklist_filter(self):
        """测试第一级过滤：黑名单过滤"""
        # 包含黑名单词汇的内容
        content = "这段内容包含黑名单词汇，应该被拦截"
        result = self.checker.check_content(content)
        self.assertFalse(result, "黑名单过滤失败，未能检测出包含黑名单词汇的内容")
        
        # 不包含黑名单词汇的内容
        content = "这是一段正常的内容"
        # 确保不会直接调用本地服务和大模型
        with patch.object(self.checker, '_basic_keyword_check', return_value=True):
            with patch.object(self.checker, '_check_with_llm', return_value=(True, "内容合规")):
                result = self.checker.check_content(content)
                self.assertTrue(result, "正常内容被错误拦截")
    
    @patch('requests.post')
    def test_local_service_filter(self, mock_post):
        """测试第二级过滤：本地敏感词服务"""
        # 模拟本地服务响应 - 检测到敏感词
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "msg": "检测成功",
            "word_list": [{"keyword": "敏感词", "category": "违规", "position": "1-3"}]
        }
        mock_post.return_value = mock_response
        
        # 确保黑名单检查通过但本地服务检测失败
        content = "不包含黑名单但包含本地服务能检测的敏感内容"
        result = self.checker.check_content(content)
        self.assertFalse(result, "本地服务过滤失败，未能检测出敏感内容")
        
        # 模拟本地服务响应 - 未检测到敏感词
        mock_response.json.return_value = {
            "code": "0",
            "msg": "检测成功",
            "word_list": []
        }
        
        # 确保黑名单和本地服务都通过，但不会调用大模型
        with patch.object(self.checker, '_check_with_llm', return_value=(True, "内容合规")):
            result = self.checker.check_content(content)
            self.assertTrue(result, "正常内容被本地服务错误拦截")
    
    @patch('requests.post')
    def test_deepseek_filter(self, mock_post):
        """测试第三级过滤：DeepSeek大模型验证"""
        # 模拟本地服务响应 - 未检测到敏感词
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "msg": "检测成功",
            "word_list": []
        }
        mock_post.return_value = mock_response
        
        # 模拟大模型检测到不合规内容
        with patch.object(self.checker, '_check_with_llm', return_value=(False, "内容暗示违规行为")):
            content = "这段内容很隐晦，本地服务检测不出，但大模型能够理解其潜在违规意图"
            result = self.checker.check_content(content)
            self.assertFalse(result, "大模型过滤失败，未能检测出隐晦的违规内容")
        
        # 模拟大模型检测通过
        with patch.object(self.checker, '_check_with_llm', return_value=(True, "内容合规")):
            content = "这是一段完全正常的内容"
            result = self.checker.check_content(content)
            self.assertTrue(result, "正常内容被大模型错误拦截")
    
    @patch('requests.post')
    def test_service_fallback(self, mock_post):
        """测试服务不可用时的降级策略"""
        # 模拟本地服务不可用
        mock_post.side_effect = Exception("Connection error")
        
        # 确保会降级到基础关键词检查
        content = "这段内容包含敏感信息"
        result = self.checker.check_content(content)
        self.assertFalse(result, "本地服务不可用时，降级检测失败")
        
        # 不包含备用关键词的内容
        content = "这是一段正常内容"
        with patch.object(self.checker, '_check_with_llm', return_value=(True, "内容合规")):
            result = self.checker.check_content(content)
            self.assertTrue(result, "正常内容在服务降级后被错误拦截")
    
    def test_complete_filter_flow(self):
        """测试完整的三级过滤流程"""
        test_cases = [
            {"content": "包含黑名单词汇的内容", "expected": False, "description": "黑名单过滤"},
            {"content": "这是一段正常内容", "expected": True, "description": "正常内容"}
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                # 对于正常内容，模拟本地服务和大模型都通过
                if case["expected"]:
                    with patch('requests.post') as mock_post:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "code": "0", "msg": "检测成功", "word_list": []
                        }
                        mock_post.return_value = mock_response
                        
                        with patch.object(self.checker, '_check_with_llm', return_value=(True, "内容合规")):
                            result = self.checker.check_content(case["content"])
                            self.assertEqual(result, case["expected"], 
                                            f"{case['description']} 测试失败")
                else:
                    # 对于应该被拦截的内容，直接测试
                    result = self.checker.check_content(case["content"])
                    self.assertEqual(result, case["expected"], 
                                    f"{case['description']} 测试失败")

    def test_async_text_check(self):
        """测试异步文本检查功能"""
        # 由于异步测试需要特殊处理，这里只进行简单的接口测试
        async def run_async_test():
            # 模拟本地服务
            with patch('requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "code": "0", "msg": "检测成功", "word_list": []
                }
                mock_post.return_value = mock_response
                
                # 模拟大模型
                with patch.object(self.checker, '_check_with_llm_async', 
                                 return_value=(True, "内容合规")):
                    result, filtered_text, word_list = await self.checker.check_text("测试内容")
                    return result
        
        # 使用同步方式运行异步测试
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_async_test())
        
        self.assertTrue(result, "异步检查功能测试失败")


if __name__ == "__main__":
    print("\n===== 开始测试文本过滤的三级过滤机制 =====\n")
    unittest.main(verbosity=2)
