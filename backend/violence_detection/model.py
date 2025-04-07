"""
暴力图像分类模型定义
基于PyTorch Lightning实现
"""

import torch
from torch import nn
from torchvision import models
from pytorch_lightning import LightningModule
from torchmetrics import Accuracy
from typing import Dict, Any, Optional

class ViolenceClassifier(LightningModule):
    """暴力图像分类器，基于预训练的ResNet18"""
    
    def __init__(self, num_classes=2, learning_rate=1e-3):
        super().__init__()
        # 加载预训练的ResNet18，与训练代码保持一致
        self.model = models.resnet18()
        
        # 替换最后的全连接层，保持简单结构与训练代码一致
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, num_classes)
        
        # 配置超参数
        self.learning_rate = learning_rate
        self.loss_fn = nn.CrossEntropyLoss()
        self.accuracy = Accuracy(task="multiclass", num_classes=2)
    
    def forward(self, x):
        """前向传播函数"""
        return self.model(x)
    
    def configure_optimizers(self):
        """配置优化器"""
        optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.learning_rate
        )
        return optimizer
    
    def training_step(self, batch, batch_idx):
        """训练步骤"""
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        self.log('train_loss', loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        """验证步骤"""
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        acc = self.accuracy(logits, y)
        self.log('val_loss', loss)
        self.log('val_acc', acc)
        return loss
    
    def test_step(self, batch, batch_idx):
        """测试步骤"""
        x, y = batch
        logits = self(x)
        acc = self.accuracy(logits, y)
        self.log('test_acc', acc)
        return acc

def load_model_from_checkpoint(checkpoint_path: str, device: Optional[torch.device] = None) -> ViolenceClassifier:
    """
    从检查点加载模型
    
    Args:
        checkpoint_path (str): 模型检查点路径
        device (torch.device, optional): 运行设备，默认为None (自动选择)
        
    Returns:
        ViolenceClassifier: 加载好权重的模型
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 创建模型实例
    model = ViolenceClassifier()
    
    # 加载检查点
    try:
        # 尝试加载Lightning模型
        checkpoint = torch.load(checkpoint_path, map_location=device)
        
        # 处理Lightning检查点
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            model.load_state_dict(checkpoint["state_dict"])
        else:
            model.load_state_dict(checkpoint)
            
        print(f"成功从 {checkpoint_path} 加载模型")
    except Exception as e:
        print(f"加载模型时出错: {e}")
        raise
    
    # 将模型移至指定设备
    model = model.to(device)
    # 设置为评估模式
    model.eval()
    
    return model

class ViolencePredictor:
    """暴力图像预测器，用于推理阶段"""
    
    def __init__(self, checkpoint_path: str, device: Optional[torch.device] = None):
        """
        初始化预测器
        
        Args:
            checkpoint_path (str): 模型检查点路径
            device (torch.device, optional): 运行设备
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        # 加载模型
        self.model = load_model_from_checkpoint(checkpoint_path, self.device)
        self.model.eval()  # 确保模型处于评估模式
    
    def predict(self, img_tensor: torch.Tensor) -> int:
        """
        预测单张图像是否包含暴力内容
        
        Args:
            img_tensor (torch.Tensor): 形状为 [1, C, H, W] 的图像张量
            
        Returns:
            int: 分类结果 (0:非暴力, 1:暴力)
        """
        # 确保输入是正确的形状
        if len(img_tensor.shape) == 3:
            img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度
            
        # 将图像移至正确的设备
        img_tensor = img_tensor.to(self.device)
        
        # 进行预测
        with torch.no_grad():
            logits = self.model(img_tensor)
            prediction = logits.argmax(dim=1).item()
            
        return prediction
    
    def predict_batch(self, img_tensors: torch.Tensor) -> list:
        """
        预测批量图像
        
        Args:
            img_tensors (torch.Tensor): 形状为 [B, C, H, W] 的图像张量
            
        Returns:
            list: 分类结果列表 (0:非暴力, 1:暴力)
        """
        # 将图像移至正确的设备
        img_tensors = img_tensors.to(self.device)
        
        # 进行预测
        with torch.no_grad():
            logits = self.model(img_tensors)
            predictions = logits.argmax(dim=1).tolist()
            
        return predictions