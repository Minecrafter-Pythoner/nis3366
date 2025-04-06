"""
基于图像命名规则计算评估指标的脚本
测试集命名规则：0开头表示非暴力图像，1开头表示暴力图像
增加ROC曲线绘制功能
"""

import os
import sys
import time
from pathlib import Path
import torch
import torchvision.transforms as transforms
from torchvision import models
from torch import nn
from PIL import Image
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.metrics import roc_curve, auc
import json
import matplotlib.pyplot as plt
import numpy as np


# 设置日志输出
def log(message):
    """输出日志到控制台"""
    print(message)


# 模型定义
class ViolenceClassifier(nn.Module):
    """暴力图像分类器，基于预训练的ResNet18"""
    
    def __init__(self, num_classes=2):
        super().__init__()
        # 加载预训练的ResNet18
        self.model = models.resnet18(pretrained=True)
        
        # 替换最后的全连接层
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, num_classes)
    
    def forward(self, x):
        """前向传播函数"""
        return self.model(x)


def load_model(checkpoint_path):
    """加载模型"""
    log(f"加载模型检查点: {checkpoint_path}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"使用设备: {device}")
    
    # 创建模型
    model = ViolenceClassifier()
    
    # 加载权重
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            model.load_state_dict(checkpoint["state_dict"])
        else:
            model.load_state_dict(checkpoint)
        
        log("模型加载成功")
    except Exception as e:
        log(f"加载模型出错: {e}")
        sys.exit(1)
    
    # 将模型移到设备并设置为评估模式
    model = model.to(device)
    model.eval()
    
    return model, device


def predict_image(model, image_path, device, transform):
    """预测单张图像，返回预测标签和置信度"""
    try:
        # 加载图像
        img = Image.open(image_path).convert('RGB')
        
        # 预处理
        tensor = transform(img).unsqueeze(0).to(device)
        
        # 预测
        with torch.no_grad():
            outputs = model(tensor)
            # 获取softmax概率
            probs = torch.nn.functional.softmax(outputs, dim=1)
            # 获取暴力类别的概率
            violence_prob = probs[0][1].item()
            # 获取预测类别
            prediction = outputs.argmax(dim=1).item()
        
        return prediction, violence_prob
    except Exception as e:
        log(f"处理图像 {image_path} 出错: {e}")
        return None, None


def get_label_from_filename(filename):
    """从文件名获取标签，0开头为非暴力(0)，1开头为暴力(1)"""
    if filename.startswith("0"):
        return 0
    elif filename.startswith("1"):
        return 1
    else:
        return None  # 不符合命名规则


def calculate_metrics(y_true, y_pred, y_scores=None):
    """计算评估指标"""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        log("无有效预测结果或标签数量不匹配")
        return {}
    
    # 计算指标
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # 计算混淆矩阵
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    result = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp)
        }
    }
    
    # 如果提供了分数，计算ROC数据
    if y_scores is not None:
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        result["roc"] = {
            "auc": float(roc_auc),
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": thresholds.tolist()
        }
    
    return result


def plot_roc_curve(metrics, output_file="roc_curve.png"):
    """绘制ROC曲线"""
    if "roc" not in metrics:
        log("缺少ROC数据，无法绘制曲线")
        return
    
    roc_data = metrics["roc"]
    fpr = roc_data["fpr"]
    tpr = roc_data["tpr"]
    auc_value = roc_data["auc"]
    
    plt.figure(figsize=(10, 8))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC曲线 (AUC = {auc_value:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('假正例率 (False Positive Rate)')
    plt.ylabel('真正例率 (True Positive Rate)')
    plt.title('ROC曲线 - 暴力图像检测')
    plt.legend(loc="lower right")
    
    # 保存图像
    plt.savefig(output_file, dpi=300)
    log(f"ROC曲线已保存到: {output_file}")
    
    # 关闭图形，释放内存
    plt.close()


def main():
    """主函数"""
    log("=== 图像命名评估脚本开始运行 ===")
    log(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 配置参数
    test_dir = Path("C:/Users/28214/Desktop/nis3366web/backend/media/uploads")
    checkpoint_path = Path("checkpoints/resnet18_pretrain_test-epoch=31-val_loss=0.04.ckpt")
    output_json = "evaluation_metrics.json"
    output_roc = "roc_curve.png"
    
    # 检查路径
    if not test_dir.exists():
        log(f"测试目录不存在: {test_dir}")
        return
    
    if not checkpoint_path.exists():
        log(f"检查点文件不存在: {checkpoint_path}")
        return
    
    # 加载模型
    model, device = load_model(checkpoint_path)
    
    # 设置图像变换
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    
    # 收集图像文件
    log("收集图像文件...")
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    log(f"找到 {len(image_files)} 张图像文件")
    
    if not image_files:
        log("没有找到图像文件")
        return
    
    # 进行预测
    log("开始处理图像...")
    y_true = []  # 真实标签
    y_pred = []  # 预测标签
    y_scores = []  # 预测分数（用于ROC曲线）
    
    for img_path in image_files:
        # 从文件名获取真实标签
        true_label = get_label_from_filename(img_path.name)
        
        if true_label is None:
            log(f"跳过不符合命名规则的图像: {img_path.name}")
            continue
        
        # 预测图像
        pred_label, pred_score = predict_image(model, img_path, device, transform)
        
        if pred_label is not None and pred_score is not None:
            y_true.append(true_label)
            y_pred.append(pred_label)
            y_scores.append(pred_score)  # 保存暴力类别的概率
            
            # 输出进度
            if len(y_pred) % 10 == 0:
                log(f"已处理 {len(y_pred)} 张图像...")
    
    # 计算指标
    log(f"处理完成，共有效处理 {len(y_pred)} 张图像")
    metrics = calculate_metrics(y_true, y_pred, y_scores)
    
    # 输出指标
    log("\n=== 评估指标 ===")
    log(f"准确率 (Accuracy): {metrics.get('accuracy', 'N/A'):.4f}")
    log(f"精确率 (Precision): {metrics.get('precision', 'N/A'):.4f}")
    log(f"召回率 (Recall): {metrics.get('recall', 'N/A'):.4f}")
    log(f"F1分数: {metrics.get('f1_score', 'N/A'):.4f}")
    
    if 'roc' in metrics:
        log(f"ROC曲线下面积 (AUC): {metrics['roc']['auc']:.4f}")
    
    if 'confusion_matrix' in metrics:
        cm = metrics['confusion_matrix']
        log("\n混淆矩阵:")
        log(f"真阳性 (TP): {cm.get('true_positive', 'N/A')}")
        log(f"假阳性 (FP): {cm.get('false_positive', 'N/A')}")
        log(f"真阴性 (TN): {cm.get('true_negative', 'N/A')}")
        log(f"假阴性 (FN): {cm.get('false_negative', 'N/A')}")
    
    # 绘制ROC曲线
    plot_roc_curve(metrics, output_roc)
    
    # 保存指标到文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)
    
    log(f"评估指标已保存到: {output_json}")
    log("评估完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"程序运行出错: {e}")
        import traceback
        print(traceback.format_exc())