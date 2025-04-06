"""
FastAPI中间件模块，用于内容检查
"""

import re
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import io
from PIL import Image
from typing import List, Dict, Any, Set, Optional
import json
import os

from .classify import get_classifier

class ContentFilterMiddleware(BaseHTTPMiddleware):
    """内容过滤中间件，检查敏感词和图像内容"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        sensitive_words_file: Optional[str] = None,
        bypass_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        
        self.sensitive_words: Set[str] = self._load_sensitive_words(sensitive_words_file)
        
        self.bypass_paths = bypass_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/health",
            "/violence-detection"
        ]
        
    def _load_sensitive_words(self, file_path: Optional[str] = None) -> Set[str]:
        from pathlib import Path
        
        words = {"暴力", "色情", "赌博", "毒品", "政治敏感"}
        
        default_path = Path(os.path.dirname(os.path.abspath(__file__))) / "sensitive_words.txt"
        file_path = file_path or default_path
        
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word and not word.startswith('#'):
                            words.add(word)
                print(f"已加载敏感词 {len(words)} 个")
            except Exception as e:
                print(f"加载敏感词文件出错: {e}")
        else:
            print(f"敏感词文件不存在: {file_path}，将使用默认敏感词")
        return words
        
    async def censor_text(self, content: str) -> str:
        if not content or not isinstance(content, str):
            return content
            
        for word in self.sensitive_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            content = pattern.sub('**', content)
            
        return content
        
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if any(path.startswith(bypass) for bypass in self.bypass_paths):
            return await call_next(request)
            
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            
            if "multipart/form-data" in content_type:
                try:
                    form = await request.form()
                    files = []
                    
                    for key, value in form.items():
                        if hasattr(value, "content_type") and value.content_type.startswith("image/"):
                            is_appropriate = await self._check_image_content(value)
                            if not is_appropriate:
                                return JSONResponse(
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    content={"detail": "上传的图片包含不允许的内容"}
                                )
                            
                    return await call_next(request)
                except Exception as e:
                    print(f"处理表单数据时出错: {e}")
            
            elif "application/json" in content_type:
                try:
                    body = await request.body()
                    
                    if body:
                        json_data = json.loads(body)
                        
                        filtered_data = await self._filter_json_recursively(json_data)
                        
                        async def _receive():
                            return {"type": "http.request", "body": json.dumps(filtered_data).encode()}
                        
                        original_receive = request.receive
                        
                        request.receive = _receive
                        
                except Exception as e:
                    print(f"处理JSON数据时出错: {e}")
        
        return await call_next(request)
    
    async def _filter_json_recursively(self, data: Any) -> Any:
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = await self._filter_json_recursively(value)
            return result
        elif isinstance(data, list):
            return [await self._filter_json_recursively(item) for item in data]
        elif isinstance(data, str):
            return await self.censor_text(data)
        else:
            return data
    
    async def _check_image_content(self, file) -> bool:
        """检查图像是否包含不当内容，True为合规，False为不合规"""
        try:
            content = await file.read()
            image = Image.open(io.BytesIO(content)).convert('RGB')
            
            classifier = get_classifier()
            
            preprocessed_image = classifier.transforms(image)
            tensor = preprocessed_image.unsqueeze(0)
            
            predictions = classifier.classify(tensor)
            
            await file.seek(0)
            
            is_violent = any(pred == 1 for pred in predictions)
            
            return not is_violent
            
        except Exception as e:
            print(f"图像检查失败: {e}")
            await file.seek(0)
            return False