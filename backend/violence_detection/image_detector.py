"""
图像检测函数模块
提供简单的接口用于图像内容筛选
"""

import os
import io
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Union, List, Optional, Tuple, BinaryIO
from PIL import Image
import torch
import logging

from .classify import get_classifier, ViolenceClass

# 配置日志
logger = logging.getLogger(__name__)

class ImageDetector:
    """图像检测器类，包装暴力内容检测功能"""
    
    def __init__(self, harmony_img_path: Optional[Path] = None):
        """
        初始化图像检测器
        
        Args:
            harmony_img_path: 和谐图片路径，用于替换违规图片
        """
        self.classifier = get_classifier()
        
        # 设置和谐图片路径
        base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.harmony_img_path = harmony_img_path or (base_dir.parent / "media" / "harmony.png")
        
        # 确保和谐图片存在
        if not self.harmony_img_path.exists():
            logger.warning(f"和谐图片不存在: {self.harmony_img_path}")
        else:
            logger.info(f"使用和谐图片: {self.harmony_img_path}")
    
    def detect_image_file(self, 
                        file_path: Union[str, Path], 
                        replace_if_violent: bool = True) -> Dict[str, Any]:
        """
        检测图像文件
        
        Args:
            file_path: 图像文件路径
            replace_if_violent: 如果检测到暴力内容是否替换
            
        Returns:
            Dict: 检测结果
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        try:
            # 打开并转换图像
            image = Image.open(file_path).convert('RGB')
            
            # 执行分类
            prediction = self.classifier.classify_single_image(image)
            is_violent = prediction == 1
            
            # 获取置信度
            tensor = self.classifier.transforms(image).unsqueeze(0)
            with torch.no_grad():
                outputs = self.classifier.model(tensor.to(self.classifier.device))
                confidences = torch.softmax(outputs, dim=1).cpu().numpy()
            
            # 检测到暴力内容且需要替换
            replaced = False
            if is_violent and replace_if_violent and self.harmony_img_path.exists():
                # 备份原图（可选）
                # backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                # shutil.copy2(file_path, backup_path)
                
                # 替换为和谐图片
                shutil.copy2(self.harmony_img_path, file_path)
                replaced = True
                logger.info(f"已将暴力图片替换为和谐图片: {file_path}")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 返回结果
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "is_violent": is_violent,
                "confidence": float(confidences[0][prediction]),
                "processing_time_ms": int(processing_time * 1000),
                "replaced": replaced
            }
            
        except Exception as e:
            logger.error(f"图像检测错误: {str(e)}")
            return {
                "filename": file_path.name if hasattr(file_path, 'name') else str(file_path),
                "path": str(file_path),
                "error": str(e),
                "is_violent": False,  # 默认为安全
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def detect_image_bytes(self, 
                         image_bytes: bytes,
                         filename: str = "image.jpg",
                         replace_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        检测图像字节数据
        
        Args:
            image_bytes: 图像字节数据
            filename: 图像文件名
            replace_path: 如检测到暴力内容需要替换的路径，None表示不替换
            
        Returns:
            Dict: 检测结果
        """
        start_time = time.time()
        
        try:
            # 读取图像
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # 执行分类
            prediction = self.classifier.classify_single_image(image)
            is_violent = prediction == 1
            
            # 获取置信度
            tensor = self.classifier.transforms(image).unsqueeze(0)
            with torch.no_grad():
                outputs = self.classifier.model(tensor.to(self.classifier.device))
                confidences = torch.softmax(outputs, dim=1).cpu().numpy()
            
            # 检测到暴力内容且需要替换
            replaced = False
            if is_violent and replace_path and self.harmony_img_path.exists():
                shutil.copy2(self.harmony_img_path, replace_path)
                replaced = True
                logger.info(f"已将暴力图片替换为和谐图片: {replace_path}")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 返回结果
            return {
                "filename": filename,
                "is_violent": is_violent,
                "confidence": float(confidences[0][prediction]),
                "processing_time_ms": int(processing_time * 1000),
                "replaced": replaced
            }
            
        except Exception as e:
            logger.error(f"图像字节检测错误: {str(e)}")
            return {
                "filename": filename,
                "error": str(e),
                "is_violent": False,  # 默认为安全
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def detect_image_upload(self, 
                         upload_file, 
                         save_path: Optional[Path] = None,
                         replace_if_violent: bool = True) -> Dict[str, Any]:
        """
        检测上传的图像文件
        
        Args:
            upload_file: FastAPI上传文件对象
            save_path: 保存路径，None表示不保存
            replace_if_violent: 如果检测到暴力内容是否替换
            
        Returns:
            Dict: 检测结果
        """
        start_time = time.time()
        
        if not upload_file.content_type.startswith("image/"):
            return {
                "filename": upload_file.filename,
                "error": "非图像文件",
                "is_violent": False,
                "processing_time_ms": 0
            }
        
        try:
            # 读取图像内容
            image_content = upload_file.file.read()
            image = Image.open(io.BytesIO(image_content)).convert('RGB')
            
            # 执行分类
            prediction = self.classifier.classify_single_image(image)
            is_violent = prediction == 1
            
            # 获取置信度
            tensor = self.classifier.transforms(image).unsqueeze(0)
            with torch.no_grad():
                outputs = self.classifier.model(tensor.to(self.classifier.device))
                confidences = torch.softmax(outputs, dim=1).cpu().numpy()
            
            # 检测到暴力内容且需要保存和替换
            replaced = False
            saved = False
            if save_path:
                # 确保目录存在
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                if is_violent and replace_if_violent and self.harmony_img_path.exists():
                    # 保存和谐图片
                    shutil.copy2(self.harmony_img_path, save_path)
                    replaced = True
                    saved = True
                    logger.info(f"已保存和谐图片: {save_path}")
                else:
                    # 保存原图
                    with open(save_path, "wb") as f:
                        f.write(image_content)
                    saved = True
                    logger.info(f"已保存原图: {save_path}")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 返回结果
            result = {
                "filename": upload_file.filename,
                "is_violent": is_violent,
                "confidence": float(confidences[0][prediction]),
                "processing_time_ms": int(processing_time * 1000),
                "replaced": replaced,
                "saved": saved
            }
            
            if save_path:
                result["path"] = str(save_path)
            
            return result
            
        except Exception as e:
            logger.error(f"上传图像检测错误: {str(e)}")
            return {
                "filename": upload_file.filename,
                "error": str(e),
                "is_violent": False,  # 默认为安全
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        finally:
            # 重置文件指针
            upload_file.file.seek(0)
    
    def batch_detect_files(self, 
                         file_paths: List[Union[str, Path]],
                         replace_if_violent: bool = True) -> Dict[str, Any]:
        """
        批量检测图像文件
        
        Args:
            file_paths: 图像文件路径列表
            replace_if_violent: 如果检测到暴力内容是否替换
            
        Returns:
            Dict: 检测结果
        """
        if not file_paths:
            return {"results": [], "total": 0}
        
        results = []
        violent_count = 0
        
        for path in file_paths:
            result = self.detect_image_file(path, replace_if_violent)
            results.append(result)
            
            if result.get("is_violent", False):
                violent_count += 1
        
        return {
            "results": results,
            "total": len(results),
            "violent_count": violent_count,
            "violent_percentage": violent_count / len(results) * 100 if results else 0
        }


# 创建单例实例，便于导入
_detector = None

def get_detector():
    """获取图像检测器实例（单例模式）"""
    global _detector
    if _detector is None:
        _detector = ImageDetector()
    return _detector


# 方便直接调用的函数接口
def check_image_violent(
    image_data: Union[bytes, Path, str, BinaryIO],
    filename: Optional[str] = None,
    replace_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    检查图像是否包含暴力内容
    
    Args:
        image_data: 图像数据，可以是字节、文件路径或文件对象
        filename: 文件名（如果提供的是字节或文件对象）
        replace_path: 如检测到暴力内容需要替换的路径
        
    Returns:
        Dict: 检测结果，包含is_violent字段表示是否暴力
    """
    detector = get_detector()
    
    # 处理不同类型的输入
    if isinstance(image_data, (str, Path)):
        # 处理文件路径
        return detector.detect_image_file(
            image_data, 
            replace_if_violent=replace_path is not None
        )
    elif isinstance(image_data, bytes):
        # 处理字节数据
        return detector.detect_image_bytes(
            image_data,
            filename=filename or "image.jpg",
            replace_path=replace_path
        )
    elif hasattr(image_data, 'read'):
        # 处理文件对象
        image_bytes = image_data.read()
        if hasattr(image_data, 'seek'):
            image_data.seek(0)
        return detector.detect_image_bytes(
            image_bytes,
            filename=filename or "image.jpg",
            replace_path=replace_path
        )
    else:
        raise ValueError("不支持的图像数据类型")