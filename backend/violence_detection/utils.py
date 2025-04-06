"""
实用工具函数模块
"""

import os
import torch
import numpy as np
from PIL import Image
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Union, Optional

def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory (Union[str, Path]): 目录路径
    
    Returns:
        Path: 目录路径对象
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def get_default_device() -> torch.device:
    """
    获取默认设备（CUDA或CPU）
    
    Returns:
        torch.device: 默认运行设备
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def save_upload_file_temp(upload_file) -> Path:
    """
    保存上传文件到临时文件并返回路径
    
    Args:
        upload_file: FastAPI上传文件对象
        
    Returns:
        Path: 临时文件路径
    """
    try:
        suffix = Path(upload_file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            shutil.copyfileobj(upload_file.file, temp)
            temp_path = Path(temp.name)
    finally:
        upload_file.file.seek(0)  # 重置文件指针
    
    return temp_path

def is_valid_image(file_path: Union[str, Path]) -> bool:
    """
    检查文件是否为有效图像
    
    Args:
        file_path (Union[str, Path]): 文件路径
        
    Returns:
        bool: 是否为有效图像
    """
    try:
        img = Image.open(file_path)
        img.verify()  # 验证图像
        return True
    except Exception:
        return False

def cleanup_temp_files(file_paths: List[Path]) -> None:
    """
    清理临时文件
    
    Args:
        file_paths (List[Path]): 要清理的文件路径列表
    """
    for path in file_paths:
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            print(f"清理临时文件时出错: {e}")