"""
修改后的FastAPI路由，保留API但使用新的图像检测器实现
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import tempfile
import os
import shutil
from pathlib import Path
import time

# 导入新的图像检测器
from .image_detector import get_detector, ImageDetector

router = APIRouter(
    prefix="/violence-detection",
    tags=["violence-detection"],
    responses={404: {"description": "Not found"}},
)

# 保留结果缓存
result_cache = {}

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
HARMONY_IMG_PATH = BASE_DIR.parent / "media" / "harmony.png"
UPLOAD_DIR = BASE_DIR.parent / "media" / "uploads"

@router.get("/")
async def violence_detection_status():
    return {"status": "active", "service": "Violence Image Detection API"}

def get_detector_with_path():
    """获取使用自定义和谐图片的检测器"""
    detector = get_detector()
    detector.harmony_img_path = HARMONY_IMG_PATH
    return detector

@router.post("/detect/")
async def detect_violence(
    file: UploadFile = File(...),
    cache: bool = Form(True),
    replace_if_violent: bool = Form(True),
    detector: ImageDetector = Depends(get_detector_with_path) 
):
    """
    检测图像中的暴力内容

    Args:
        file (UploadFile): 上传的图像文件
        cache (bool, optional): 是否启用结果缓存, 默认为True
        replace_if_violent (bool, optional): 如果检测到暴力内容是否替换,默认为True
        
    Returns:
        Dict: 检测结果
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只接受图像文件")
    
    # 读取文件内容
    image_content = await file.read()
    
    # 检查缓存
    if cache:
        cache_key = str(hash(image_content))
        if cache_key in result_cache:
            result_cache[cache_key]["timestamp"] = time.time()
            return result_cache[cache_key]["result"]
    
    try:
        # 如果需要替换，创建保存路径
        save_path = None
        if replace_if_violent:
            save_path = UPLOAD_DIR / file.filename
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # 使用检测器处理图像
        result = detector.detect_image_bytes(
            image_content,
            filename=file.filename,
            replace_path=save_path if replace_if_violent else None
        )
        
        # 添加到缓存
        if cache:
            result_cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            
            _cleanup_cache()
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像处理错误: {str(e)}")
    finally:
        await file.seek(0)

@router.post("/process-uploaded-image/")
async def process_uploaded_image(
    image_path: str = Form(...),
    replace_if_violent: bool = Form(True),
    detector: ImageDetector = Depends(get_detector_with_path)
):
    """
    处理已上传的图片，检测是否包含暴力内容并可选替换
    
    Args:
        image_path (str): 图片路径（相对于上传目录）
        replace_if_violent (bool, optional): 如果检测到暴力内容是否替换,默认为True
        
    Returns:
        Dict: 处理结果
    """
    full_path = UPLOAD_DIR / image_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"图片不存在: {image_path}")
        
    try:
        # 使用检测器处理图像
        result = detector.detect_image_file(
            full_path,
            replace_if_violent=replace_if_violent
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片处理错误: {str(e)}")

@router.post("/batch-detect/")
async def batch_detect_violence(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    replace_if_violent: bool = Form(True),
    detector: ImageDetector = Depends(get_detector_with_path)
):
    """
    批量检测多个上传图像
    
    Args:
        files (List[UploadFile]): 上传的图像文件列表
        background_tasks (BackgroundTasks, optional): 后台任务
        replace_if_violent (bool, optional): 如果检测到暴力内容是否替换,默认为True
        
    Returns:
        Dict: 检测结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="未提供图像文件")
    
    # 最大批处理大小
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="一次最多处理20张图像")
    
    results = []
    violent_count = 0
    
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"文件 '{file.filename}' 不是图像")
            
            # 如果需要替换，创建保存路径
            save_path = None
            if replace_if_violent:
                save_path = UPLOAD_DIR / file.filename
            
            # 使用检测器处理图像
            result = detector.detect_image_upload(
                file,
                save_path=save_path,
                replace_if_violent=replace_if_violent
            )
            
            results.append(result)
            if result.get("is_violent", False):
                violent_count += 1
        
        return {
            "results": results, 
            "total": len(results),
            "violent_count": violent_count,
            "violent_percentage": violent_count / len(results) * 100 if results else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理错误: {str(e)}")

def _cleanup_cache():
    """清理过期的缓存项"""
    global result_cache
    current_time = time.time()
    expire_time = 3600  # 1小时过期
    
    expired_keys = [
        k for k, v in result_cache.items() 
        if current_time - v["timestamp"] > expire_time
    ]
    
    for key in expired_keys:
        del result_cache[key]