import requests
import json
import logging
import os
from typing import Dict, List, Tuple, Any, Optional
import time
import asyncio
import threading
import re

# 导入OpenAI SDK，用于调用DeepSeek API
try:
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    print("请安装OpenAI SDK: pip install openai")

logger = logging.getLogger(__name__)


class WordsChecker:
    """敏感词检测服务封装"""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        access_token: str = "",
        deepseek_api_key: str = "sk-ac1d011dbd6c48f58f6b2c70ba7d798e",
        use_llm: bool = True,
    ):
        """
        初始化敏感词检测服务

        参数:
            base_url: 敏感词检测服务地址
            access_token: 接口认证token（如果配置了Header token验证）
            deepseek_api_key: DeepSeek API密钥
            use_llm: 是否启用大模型验证
        """
        self.base_url = base_url
        self.access_token = access_token
        self.check_url = f"{base_url}/wordscheck"
        self.service_available = True
        self._init_backup_keywords()
        self.blacklist = []
        self._load_blacklist()

        # 大模型设置
        self.use_llm = use_llm
        self.deepseek_api_key = deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.llm_client = None
        self.async_llm_client = None
        self.llm_available = False

        # 如果提供了API密钥，初始化LLM客户端
        if self.deepseek_api_key and self.use_llm:
            try:
                self.llm_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                self.async_llm_client = AsyncOpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                self.llm_available = True
                logger.info("DeepSeek大模型客户端初始化成功")
            except Exception as e:
                logger.error(f"DeepSeek大模型客户端初始化失败: {str(e)}")
        elif self.use_llm:
            logger.warning("未提供DeepSeek API密钥，大模型验证将被禁用")

    def _init_backup_keywords(self):
        """初始化备用关键词列表"""
        self.backup_keywords = [
            "色情", "赌博", "毒品", "政治", "违禁", "脏话",
            "操你", "妈的", "傻逼", "艹", "草泥马"
        ]

    def _load_blacklist(self):
        """从blacklist.txt加载黑名单"""
        try:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            blacklist_path = os.path.join(current_dir, "blacklist.txt")

            if os.path.exists(blacklist_path):
                with open(blacklist_path, 'r', encoding='utf-8') as f:
                    # 读取文件内容并按行分割
                    lines = f.read().splitlines()
                    # 过滤空行并去除前后空格
                    self.blacklist = [line.strip() for line in lines if line.strip()]
                logger.info(f"已加载黑名单词条 {len(self.blacklist)} 条")
            else:
                logger.warning(f"黑名单文件不存在: {blacklist_path}")
        except Exception as e:
            logger.error(f"加载黑名单文件失败: {str(e)}")

    def _check_blacklist(self, content: str) -> bool:
        """
        检查内容是否包含黑名单词汇
        
        参数:
            content: 文本内容
            
        返回:
            bool: 是否通过检查 (True表示通过检查，不含黑名单词汇；False表示包含黑名单词汇)
        """
        if not self.blacklist:
            return True

        for word in self.blacklist:
            if word and word in content:
                logger.warning(f"黑名单匹配到敏感词: {word}")
                return False

        return True

    def check_service_status(self) -> bool:
        """
        检查敏感词检测服务是否可用
        
        返回:
            bool: 服务是否可用
        """
        try:
            response = requests.get(self.base_url, timeout=2)
            self.service_available = response.status_code == 200
            return self.service_available
        except Exception as e:
            logger.warning(f"敏感词检测服务状态检查失败: {str(e)}")
            self.service_available = False
            return False

    def _basic_keyword_check(self, content: str) -> bool:
        """
        基础关键词检测，当敏感词服务不可用时使用
        
        参数:
            content: 文本内容
        
        返回:
            bool: 内容是否合规 (True表示合规，False表示不合规)
        """
        # 检查文本是否包含敏感词
        for word in self.backup_keywords:
            if word in content:
                logger.info(f"基础检测发现敏感词: {word}")
                return False

        return True

    def _check_with_llm(self, content: str) -> Tuple[bool, str]:
        """
        使用DeepSeek大模型验证内容是否合规
        
        参数:
            content: 文本内容
            
        返回:
            (is_clean, reason): 是否合规及原因
        """
        if not self.llm_available or not self.llm_client:
            return True, "大模型验证未启用"

        try:
            prompt = f"""请判断以下内容是否包含敏感信息，如政治敏感内容、色情内容、暴力内容、诈骗信息等。
只需返回JSON格式结果，其中包含两个字段：
1. is_clean: 布尔值，内容是否合规，true表示合规，false表示不合规
2. reason: 字符串，简短的理由说明

待检测内容:
"{content}"

请按以下JSON格式回答，不要有任何其他文字：
{{
    "is_clean": true/false,
    "reason": "理由说明"
}}
"""

            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个敏感内容审核专家，负责判断文本是否包含不良信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            # 获取模型回复
            result_text = response.choices[0].message.content.strip()

            # 尝试解析JSON结果
            try:
                # 提取JSON部分（防止模型输出额外文本）
                json_match = re.search(r'({.*})', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group(1))
                else:
                    result_json = json.loads(result_text)

                is_clean = result_json.get("is_clean", True)
                reason = result_json.get("reason", "未提供理由")

                logger.info(f"大模型判定结果: {is_clean}, 理由: {reason}")
                return is_clean, reason

            except json.JSONDecodeError:
                logger.warning(f"无法解析大模型返回的JSON: {result_text}")
                # 在JSON解析失败时，尝试简单文本匹配
                if "不合规" in result_text.lower() or "false" in result_text.lower():
                    return False, "大模型检测到不合规内容（解析失败）"
                else:
                    return True, "大模型未检测到不合规内容（解析失败）"

        except Exception as e:
            error_str = str(e)
            logger.error(f"大模型验证异常: {error_str}")
            
            # 检查是否是内容风险错误
            if "Content Exists Risk" in error_str:
                # 这种情况直接判定为不合规
                logger.warning("DeepSeek API拒绝处理敏感内容，判定为不合规")
                return False, "API拒绝处理敏感内容 (Content Exists Risk)"
            else:
                # 其他错误保持原有逻辑
                return True, f"大模型验证异常: {error_str}"

    async def _check_with_llm_async(self, content: str) -> Tuple[bool, str]:
        """
        使用DeepSeek大模型异步验证内容是否合规
        
        参数:
            content: 文本内容
            
        返回:
            (is_clean, reason): 是否合规及原因
        """
        if not self.llm_available or not self.async_llm_client:
            return True, "大模型验证未启用"

        try:
            prompt = f"""请判断以下内容是否包含敏感信息，如政治敏感内容、色情内容、暴力内容、诈骗信息等。
只需返回JSON格式结果，其中包含两个字段：
1. is_clean: 布尔值，内容是否合规，true表示合规，false表示不合规
2. reason: 字符串，简短的理由说明

待检测内容:
"{content}"

请按以下JSON格式回答，不要有任何其他文字：
{{
    "is_clean": true/false,
    "reason": "理由说明"
}}
"""

            response = await self.async_llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个敏感内容审核专家，负责判断文本是否包含不良信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            # 获取模型回复
            result_text = response.choices[0].message.content.strip()

            # 尝试解析JSON结果
            try:
                # 提取JSON部分（防止模型输出额外文本）
                json_match = re.search(r'({.*})', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group(1))
                else:
                    result_json = json.loads(result_text)

                is_clean = result_json.get("is_clean", True)
                reason = result_json.get("reason", "未提供理由")

                logger.info(f"大模型判定结果: {is_clean}, 理由: {reason}")
                return is_clean, reason

            except json.JSONDecodeError:
                logger.warning(f"无法解析大模型返回的JSON: {result_text}")
                # 在JSON解析失败时，尝试简单文本匹配
                if "不合规" in result_text.lower() or "false" in result_text.lower():
                    return False, "大模型检测到不合规内容（解析失败）"
                else:
                    return True, "大模型未检测到不合规内容（解析失败）"

        except Exception as e:
            logger.error(f"大模型验证异常: {str(e)}")
            return True, f"大模型验证异常: {str(e)}"

    def _extract_text_content(self, content: str) -> str:
        """
        从内容中提取纯文本部分，跳过图像内容
        
        参数:
            content: 原始内容文本
            
        返回:
            str: 提取的纯文本内容
        """
        # 跳过Base64编码的图像
        pattern = r'!\[\]\(data:image\/[^;]+;base64,[^)]+\)'
        text_content = re.sub(pattern, '[图片内容]', content)
        
        # 处理带图片描述的链接格式 ![image](https://...)
        desc_pattern = r'!\[[^\]]*\]\(https?:\/\/[^)]+\)'
        text_content = re.sub(desc_pattern, '[图片链接]', text_content)
        
        # 处理不带图片描述的链接格式 ![](https://...)
        url_pattern = r'!\[\]\(https?:\/\/[^)]+\)'
        text_content = re.sub(url_pattern, '[图片链接]', text_content)
        
        return text_content

    def _is_image_only_content(self, content: str) -> bool:
        """
        检查内容是否只包含图片链接，不包含其他文本
        
        参数:
            content: 原始内容
            
        返回:
            bool: 是否只包含图片
        """
        # 清除所有图片标记
        # 处理Base64图片
        base64_pattern = r'!\[\]\(data:image\/[^;]+;base64,[^)]+\)'
        clean_content = re.sub(base64_pattern, '', content)
        
        # 处理带描述的图片链接
        desc_pattern = r'!\[[^\]]*\]\(https?:\/\/[^)]+\)'
        clean_content = re.sub(desc_pattern, '', clean_content)
        
        # 处理不带描述的图片链接
        url_pattern = r'!\[\]\(https?:\/\/[^)]+\)'
        clean_content = re.sub(url_pattern, '', clean_content)
        
        # 去除空白字符后判断是否为空
        clean_content = clean_content.strip()
        return len(clean_content) == 0

    def check_content(self, content: str, img_lst=None) -> bool:
        """
        检查内容是否合规，与topic.py的check_func接口兼容
        
        参数:
            content: 文本内容
            img_lst: 图片列表 (直接跳过图片内容)
        
        返回:
            bool: 内容是否合规 (True表示合规，False表示不合规)
        """
        # 判断是否只包含图片
        if self._is_image_only_content(content):
            logger.info("内容仅包含图片，跳过文本检测")
            return True
        
        # 提取纯文本内容，跳过图像
        text_content = self._extract_text_content(content)
        logger.info(f"提取到纯文本内容进行检查，跳过图像内容")
        
        # 以下保持原有检查逻辑，但使用提取后的文本内容
        if not self._check_blacklist(text_content):
            logger.info("内容包含黑名单词汇，直接判定为不合规")
            return False
        
        # 如果敏感词服务可用，尝试调用
        service_check_passed = True
        if self.service_available:
            try:
                data = json.dumps({"content": text_content})

                headers = {
                    "Content-Type": "application/json",
                }

                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"

                # 发送请求
                response = requests.post(self.check_url, data=data, headers=headers, timeout=3)

                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"敏感词检测服务请求失败: {response.status_code}")
                    service_check_passed = self._basic_keyword_check(text_content)
                else:
                    # 解析结果
                    result = response.json()

                    if result.get("code") != "0":
                        logger.error(f"敏感词检测服务返回错误: {result.get('msg')}")
                        service_check_passed = self._basic_keyword_check(text_content)
                    else:
                        # 检查是否有敏感词
                        word_list = result.get("word_list", [])
                        service_check_passed = len(word_list) == 0

                        # 记录检测结果
                        if not service_check_passed:
                            categories = set()
                            for word in word_list:
                                if "category" in word and "keyword" in word:
                                    categories.add(f"{word['category']}({word['keyword']})")

                            logger.warning(f"检测到敏感内容: {', '.join(categories)}")

            except requests.exceptions.RequestException:
                # 连接问题，标记服务不可用
                self.service_available = False
                logger.error("敏感词检测服务连接失败，切换到基础检测")
                service_check_passed = self._basic_keyword_check(text_content)
            except Exception as e:
                logger.exception(f"敏感词检测异常: {str(e)}")
                service_check_passed = self._basic_keyword_check(text_content)
        else:
            # 敏感词服务不可用时，使用基础关键词检测
            service_check_passed = self._basic_keyword_check(text_content)

        # 如果前两级检查都通过，并且启用了大模型验证，则进行大模型验证
        if service_check_passed and self.use_llm and self.llm_available:
            logger.info("前置检查通过，启动大模型验证...")
            is_clean, reason = self._check_with_llm(text_content)
            if not is_clean:
                logger.warning(f"大模型检测到不合规内容: {reason}")
                return False

        # 返回最终结果
        return service_check_passed

    async def check_text(self, content: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        异步检测文本内容

        参数:
            content: 待检测文本

        返回:
            (is_clean, filtered_text, words_list):
                - is_clean: 是否无敏感词
                - filtered_text: 过滤后的文本
                - words_list: 检测到的敏感词列表
        """
        # 判断是否只包含图片
        if self._is_image_only_content(content):
            logger.info("内容仅包含图片，跳过文本检测")
            return True, content, []
        
        # 首先进行黑名单检查
        if not self._check_blacklist(content):
            logger.info("内容包含黑名单词汇，直接判定为不合规")
            return False, content, [{"keyword": "黑名单敏感词", "category": "黑名单", "position": "0-0", "level": "高"}]

        try:
            data = json.dumps({"content": content})

            headers = {
                "Content-Type": "application/json",
            }

            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            # 使用requests进行同步请求（在实际使用时建议用aiohttp进行异步请求）
            response = requests.post(self.check_url, data=data, headers=headers)

            if response.status_code != 200:
                logger.error(f"敏感词检测服务请求失败: {response.status_code}")
                # 如果启用了大模型验证，则在服务失败时尝试通过大模型验证
                if self.use_llm and self.llm_available:
                    is_clean, reason = await self._check_with_llm_async(content)
                    if not is_clean:
                        return False, content, [{"keyword": "大模型检测", "category": "AI判定", "position": "0-0", "level": "高", "reason": reason}]
                return True, content, []

            result = response.json()

            # 处理返回结果
            if result.get("code") == "0":  # 检测成功
                filtered_text = result.get("return_str", content)
                word_list = result.get("word_list", [])

                # 如果word_list为空，表示无敏感词
                is_clean = len(word_list) == 0

                # 如果敏感词检测服务判断是干净的，并且启用了大模型验证，则进行大模型验证
                if is_clean and self.use_llm and self.llm_available:
                    llm_clean, reason = await self._check_with_llm_async(content)
                    if not llm_clean:
                        return False, content, [{"keyword": "大模型检测", "category": "AI判定", "position": "0-0", "level": "高", "reason": reason}]

                return is_clean, filtered_text, word_list
            else:
                logger.error(f"敏感词检测服务返回错误: {result.get('msg')}")
                # 如果启用了大模型验证，则在服务错误时尝试通过大模型验证
                if self.use_llm and self.llm_available:
                    is_clean, reason = await self._check_with_llm_async(content)
                    if not is_clean:
                        return False, content, [{"keyword": "大模型检测", "category": "AI判定", "position": "0-0", "level": "高", "reason": reason}]
                return True, content, []

        except Exception as e:
            logger.exception(f"敏感词检测异常: {str(e)}")
            # 如果启用了大模型验证，则在服务异常时尝试通过大模型验证
            if self.use_llm and self.llm_available:
                try:
                    is_clean, reason = await self._check_with_llm_async(content)
                    if not is_clean:
                        return False, content, [{"keyword": "大模型检测", "category": "AI判定", "position": "0-0", "level": "高", "reason": reason}]
                except Exception as llm_e:
                    logger.exception(f"大模型验证也失败: {str(llm_e)}")
            # 服务异常时，默认通过
            return True, content, []

    def get_risk_categories(self, word_list: List[Dict[str, Any]]) -> List[str]:
        """
        获取敏感词的风险类别

        参数:
            word_list: 敏感词列表

        返回:
            风险类别列表
        """
        categories = set()
        for word in word_list:
            if "category" in word:
                categories.add(word["category"])

        return list(categories)

    def reload_blacklist(self):
        """重新加载黑名单"""
        self.blacklist = []
        self._load_blacklist()
        return len(self.blacklist)

    def set_llm_api_key(self, api_key: str):
        """设置DeepSeek API密钥并初始化客户端"""
        self.deepseek_api_key = api_key
        if self.deepseek_api_key and self.use_llm:
            try:
                self.llm_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                self.async_llm_client = AsyncOpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                self.llm_available = True
                logger.info("DeepSeek大模型客户端设置成功")
                return True
            except Exception as e:
                logger.error(f"DeepSeek大模型客户端设置失败: {str(e)}")
                return False
        return False

# 创建全局单例实例，便于直接导入使用
words_checker = WordsChecker(
    # 从环境变量中获取DeepSeek API密钥
    deepseek_api_key=os.environ.get(
        "DEEPSEEK_API_KEY", "sk-ac1d011dbd6c48f58f6b2c70ba7d798e"
    ),
    # 默认启用大模型验证，如果没有API密钥则会自动禁用
    use_llm=True,
)
