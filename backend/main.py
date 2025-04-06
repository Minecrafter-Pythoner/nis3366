import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path
from .chat import chat  
from .topic import topic  
from .violence_detection.image_detector import get_detector, ImageDetector  
from .login.login import router as login_router  
from .login.models import Base as LoginBase
from .login.database import engine as login_engine
from .topic.topic import app as topic_app, topic_route
from .config import DEBUG  
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建数据库表
LoginBase.metadata.create_all(bind=login_engine)

detector = get_detector()
logging.info(f"图像检测器初始化完成，使用设备: {detector.classifier.device}")

app = FastAPI(
    title="FastAPI Backend",
    description="",
    version="0.0.0"
)

# 静态文件目录配置
media_dir = Path("media")
media_dir.mkdir(exist_ok=True)
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

# CORS 中间件配置
if DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 路由挂载
app.include_router(login_router, prefix="/api")
app.mount("/api/posts", topic_app)
app.include_router(topic_route, prefix="/api")
app.mount("/api/chat", chat.app) 

# 定义全局变量存储进程对象
word_check_process = None

@app.on_event("startup")
async def startup_event():
    global word_check_process
    
    # 现有代码
    topic_app.state.image_detector = detector
    logging.info("已将图像检测器添加到topic_app状态")
    
    # 启动敏感词检测服务
    try:
        # 获取wordscheck可执行文件路径
        base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        wordscheck_path = base_dir / "wordscheck" / "svc" / "wordscheck"
        
        # Windows下可能需要使用.exe扩展名
        if sys.platform == "win32":
            wordscheck_path = base_dir / "wordscheck" / "svc" / "wordscheck_win.exe"
        
        # 确保文件存在且可执行
        if not os.path.exists(wordscheck_path):
            logging.error(f"敏感词检测服务可执行文件不存在: {wordscheck_path}")
            return
            
        # 设置工作目录
        working_dir = os.path.dirname(wordscheck_path)
        
        # 启动进程
        logging.info(f"正在启动敏感词检测服务: {wordscheck_path}")
        word_check_process = subprocess.Popen(
            str(wordscheck_path),
            cwd=working_dir,
            # stdin=subprocess.PIPE, 
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            shell=False,
            # 使进程在主进程退出时自动退出
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        
        logging.info(f"敏感词检测服务已启动，PID: {word_check_process.pid}")
        
        # 等待服务启动完成
        import time
        time.sleep(2)
        
        # 检查进程是否正常运行
        if word_check_process.poll() is not None:
            logging.error(f"敏感词检测服务启动失败，退出码: {word_check_process.returncode}")
        else:
            logging.info("敏感词检测服务正常运行中")
            
    except Exception as e:
        logging.error(f"启动敏感词检测服务时发生错误: {str(e)}")

@app.get("/")
async def read_root():
    return {
        "status": "online",
        "message": "Welcome to FastAPI Backend",
        "version": "0.0.0",
    }

@app.get("/api/test")
def read_main():
    return {"message": "Hello World from main app"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "image_detector": "active",
        "image_detector_device": str(detector.classifier.device)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)