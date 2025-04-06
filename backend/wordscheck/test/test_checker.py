# test_deepseek.py
import sys
import os
import json
import logging

# 配置详细日志，显示模型调用过程
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 导入WordsChecker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from backend.wordscheck.checker import WordsChecker

# 添加一个自定义测试函数，直接测试DeepSeek API
def test_deepseek_api_directly():
    """直接测试DeepSeek API，按照官方文档示例"""
    try:
        from openai import OpenAI
        
        print("\n===== 直接测试DeepSeek API =====")
        api_key = "sk-ac1d011dbd6c48f58f6b2c70ba7d798e"
        
        # 创建客户端
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # 测试请求
        print("发送请求到DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个敏感内容审核专家，负责判断文本是否包含不良信息。"},
                {"role": "user", "content": "请判断这段内容是否合规：'这是一段测试文本'"}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        # 打印响应内容
        print("\n===== DeepSeek API 响应 =====")
        print(f"响应ID: {response.id}")
        print(f"模型: {response.model}")
        print(f"完整响应文本: {response.choices[0].message.content}")
        
        return True
    except Exception as e:
        print(f"DeepSeek API 测试失败: {str(e)}")
        print(f"详细错误: {str(sys.exc_info())}")
        return False

def test_checker_with_deepseek():
    """测试WordsChecker类与DeepSeek的集成"""
    # 创建WordsChecker实例
    checker = WordsChecker(
        base_url="http://localhost:8080",  # 本地服务地址
        use_llm=True,
        deepseek_api_key="sk-ac1d011dbd6c48f58f6b2c70ba7d798e"  # 直接指定API密钥
    )
    
    # 输出初始化信息
    print("\n===== WordsChecker 设置 =====")
    print(f"DeepSeek API密钥: {checker.deepseek_api_key[:5]}...{checker.deepseek_api_key[-4:]}")
    print(f"大模型启用: {checker.use_llm}")
    print(f"大模型可用: {checker.llm_available}")
    
    # 测试文本
    test_texts = [
        "这是一段正常的文本，不含任何敏感内容",
        "这段话暗示了某些不良倾向，可能会被AI判定为敏感"
    ]
    
    # 禁用本地服务，确保直接使用大模型
    checker.service_available = False
    print(f"本地服务可用: {checker.service_available}")
    
    # 测试各个文本
    for i, text in enumerate(test_texts):
        print(f"\n\n{'='*50}")
        print(f"测试 {i+1}")
        print(f"测试文本: {text}")
        print(f"{'='*50}")
        
        # 直接调用内部方法测试大模型
        is_clean, reason = checker._check_with_llm(text)
        
        # 输出结果
        print(f"\n大模型判定结果:")
        print(f"- 是否合规: {'是' if is_clean else '否'}")
        print(f"- 理由: {reason}")

if __name__ == "__main__":
    # 先直接测试API
    api_works = test_deepseek_api_directly()
    
    # 如果API正常工作，继续测试checker
    if api_works:
        print("\n\nAPI测试成功，继续测试WordsChecker...")
        test_checker_with_deepseek()
    else:
        print("\n\nAPI测试失败，请检查OpenAI SDK版本和API密钥")
        print("推荐运行: pip install --upgrade openai")
