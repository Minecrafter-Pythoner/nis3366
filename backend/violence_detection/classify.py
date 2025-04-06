"""
暴力图像内容分类模块
"""

import os
import torch
import torchvision.transforms as transforms
from PIL import Image
from typing import List, Tuple, Union, Optional
import numpy as np
from pathlib import Path

from .model import ViolenceClassifier, load_model_from_checkpoint

class ViolenceClass:
    
    def __init__(self, checkpoint_path: str, batch_size: int = 16):
        """
        初始化分类器
        
        Args:
            checkpoint_path (str): 模型检查点路径
            batch_size (int, optional): 批处理大小. 默认为16
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        
        self.transforms = transforms.Compose([
            transforms.ToTensor(),
        ])
        
        self._load_model(checkpoint_path)
    
    def _load_model(self, checkpoint_path: str) -> None:
        """
        加载预训练模型
        
        Args:
            checkpoint_path (str): 模型检查点路径
        """
        try:
            self.model = load_model_from_checkpoint(checkpoint_path, self.device)
            self.model.eval()  # 确保模型处于评估模式
            print(f"模型已加载到 {self.device} 设备上")
        except Exception as e:
            raise RuntimeError(f"无法加载模型: {e}")
    
    def classify(self, tensor: torch.Tensor) -> List[int]:
        """
        对图像张量进行分类
        
        Args:
            tensor (torch.Tensor): 预处理后的图像张量，形状为[batch_size, 3, 224, 224]
            
        Returns:
            List[int]: 分类结果列表 (0: 非暴力, 1: 暴力)
        """

        self.model.eval()

        tensor = tensor.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensor)
            predictions = outputs.argmax(dim=1)
        
        return predictions.cpu().tolist()
    
    def classify_single_image(self, image: Union[str, Image.Image]) -> int:
        """
        对单张图像进行分类
        
        Args:
            image (Union[str, Image.Image]): 图像路径或PIL图像对象
            
        Returns:
            int: 分类结果 (0: 非暴力, 1: 暴力)
        """
        # 预处理图像
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise TypeError("图像必须是PIL.Image对象或图像路径字符串")
            
        tensor = self.transforms(image).unsqueeze(0)  
        result = self.classify(tensor)
        return result[0]
    
    def batch_classify(self, image_list: List[Union[str, Image.Image]]) -> List[int]:
        """
        对图像列表进行批量分类
        
        Args:
            image_list (List[Union[str, Image.Image]]): 图像路径或PIL图像对象列表
            
        Returns:
            List[int]: 分类结果列表 (0: 非暴力, 1: 暴力)
        """
        results = []

        for i in range(0, len(image_list), self.batch_size):
            batch = image_list[i:i + self.batch_size]

            tensors = []
            for img in batch:
                if isinstance(img, str):
                    img = Image.open(img).convert('RGB')
                elif not isinstance(img, Image.Image):
                    raise TypeError("图像必须是PIL.Image对象或图像路径字符串")
                
                tensors.append(self.transforms(img))

            batch_tensor = torch.stack(tensors)
            batch_results = self.classify(batch_tensor)
            results.extend(batch_results)
            
        return results

_classifier = None

def get_classifier(checkpoint_path: str = None, batch_size: int = 16) -> ViolenceClass:
    """
    获取分类器单例实例
    
    Args:
        checkpoint_path (str, optional): 模型检查点路径（仅在首次调用时需要）
        batch_size (int, optional): 批处理大小. 默认为16
    
    Returns:
        ViolenceClass: 分类器实例
    """
    global _classifier
    
    if _classifier is None:
        if checkpoint_path is None:
            violence_detection_dir = Path(__file__).parent
            default_checkpoint = violence_detection_dir / "checkpoints" / "resnet18_pretrain_test-epoch=31-val_loss=0.04.ckpt"
            
            if default_checkpoint.exists():
                checkpoint_path = str(default_checkpoint)
            else:
                raise ValueError("未指定模型检查点路径，且未找到默认检查点")
        
        _classifier = ViolenceClass(checkpoint_path, batch_size)
    
    return _classifier