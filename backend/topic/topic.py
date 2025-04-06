from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Depends, Path, Query, APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
import uuid
import os
import asyncio
import aiofiles
import time
import base64
from typing import List, Optional, Tuple
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor

from ..login.models import User
from .model import TotalTopic, Tag, APost, MyImageModel
from ..login.auth import get_current_active_user
from ..config import DEBUG
from ..violence_detection.image_detector import check_image_violent, get_detector, ImageDetector
from ..wordscheck.checker import words_checker
from ..login.database import engine, SessionLocal, Base
from pydantic import BaseModel

Base.metadata.create_all(bind=engine)
# 数据库依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_used = [get_db]

# 文件存储配置
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 创建异步上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时检查敏感词检测服务状态
    words_checker.check_service_status()
    yield

app = FastAPI(lifespan=lifespan)

def check_func(content: str, img_lst) -> bool:
    # 直接调用敏感词检测模块中的检查函数
    return words_checker.check_content(content, img_lst)

# 获取图像检测器
def get_image_detector(request: Request = None):
    """获取图像检测器，首先尝试从app.state获取，如果失败则获取全局实例"""
    if request and hasattr(request.app.state, "image_detector"):
        return request.app.state.image_detector
    
    # 获取全局检测器实例
    return get_detector()

# 更新check_content函数以包含图像检测
def check_content(content: str, img_lst: List, uuid_str):
    db = next(db_used[0]())
    target_post = db.query(APost).filter(APost.uuid == uuid_str).first()
    if target_post is None:
        return
    
    # 检查图像内容是否合规
    images_safe = True
    
    # 获取帖子关联的图片路径
    post_images = db.query(MyImageModel).filter(MyImageModel.post_uuid == uuid_str).all()
    
    # 检测图片是否包含暴力内容
    if post_images:
        # 获取图像检测器
        bg = time.time()
        detector = get_detector()
        
        # 批量检测图片
        image_paths = [img.image_path for img in post_images]
        detection_results = detector.batch_detect_files(
            image_paths,
            replace_if_violent=True 
        )
        
        if detection_results.get("violent_count", 0) > 0:
            images_safe = False
            print(f"帖子 {uuid_str} 包含 {detection_results['violent_count']} 张违规图片")
        end = time.time()
        print(f"图片检测耗时: {end - bg}秒")
    
    # 检查帖子内容是否合规,待补充
    bg = time.time()
    content_safe = check_func(content, img_lst)
    end = time.time()
    print(f"文本检测耗时: {end - bg}秒")

    target_post.visible_state = int(not (content_safe and images_safe))
    db.commit()

def return_error_message(e):
    if DEBUG:
        return str(e)
    else:
        return "Internal Server Error"

# 增强版异步文件保存函数，包含内容检测
async def async_save_image(file: UploadFile, post_uuid: str = None, request: Request = None) -> Tuple[str, bool]:
    file_path = None
    try:
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1]
        file_uuid = str(uuid.uuid4())
        file_path = f"{UPLOAD_DIR}/{file_uuid}{file_ext}"
        
        # 异步写入文件
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        
        # 检测图片内容
        # 获取检测器
        detector = get_image_detector(request)
        
        # 直接检测保存的图片
        result = check_image_violent(
            file_path, 
            replace_path=file_path if post_uuid else None  # 仅在关联帖子时替换
        )
        is_violent = result.get("is_violent", False)
        
        # 如果为暴力内容且已替换
        if is_violent and result.get("replaced", False):
            print(f"图片 {file_path} 包含违规内容，已替换为和谐图片")
        
        # 重置文件指针
        await file.seek(0)
        
        # 返回路径和内容检测结果
        return file_path, is_violent
    except Exception as e:
        # 清理可能存在的半写入文件
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise e

@app.post("/create")
async def create_post(
    request: Request,
    background_tasks: BackgroundTasks,
    nickname: str = Form(...),
    title: str = Form(...),
    tag: List[str] = Form(...),
    content: str = Form(...),
    pic_lst: List[UploadFile] = File(None),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    
):
    if pic_lst is None:
        pic_lst = []
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # 开启事务
        db.begin()
        # 标签批量处理
        tag_objects = []
        existing_tags = db.query(Tag).filter(Tag.tag.in_(tag)).all()
        existing_tag_names = {t.tag for t in existing_tags}
        new_tags = [Tag(tag=name) for name in tag if name not in existing_tag_names]
        print(f"add new tags: {[i.tag for i in new_tags]}")
        # if new_tags:
        #     breakpoint()
        #     db.bulk_save_objects(new_tags)
        #     db.commit()  # 确保获取新生成的tag ID
        
        tag_objects = existing_tags + new_tags
        # 创建主题
        new_topic = TotalTopic(
            author_name=nickname,
            topic_title=title,
            create_time=time.time(),
            update_time=time.time(),
            tags = tag_objects
        )
        db.add(new_topic)
        db.flush()

        # 创建主帖子
        new_post = APost(
            author_name=nickname,
            content=content,
            topic=new_topic,
            back_to=0,
            create_time=time.time(),
            visible_state = -1  # 待审核状态
        )
        db.add(new_post)
        db.flush()
        
        # 添加内容审核后台任务
        background_tasks.add_task(check_content, content, pic_lst, new_post.uuid)
        
        # 并行处理图片上传和检测
        save_tasks = []
        for img in pic_lst:
            task = async_save_image(img, str(new_post.uuid), request)
            save_tasks.append(task)
        
        results = await asyncio.gather(*save_tasks)
        
        # 解析结果
        image_paths = []
        violent_images = []
        
        for img, (path, is_violent) in zip(pic_lst, results):
            image_paths.append(path)
            if is_violent:
                violent_images.append(path)
        
        # 批量创建图片记录
        image_objects = [
            MyImageModel(
                title=img.filename,
                image_path=path,
                post_uuid=new_post.uuid
            ) for img, path in zip(pic_lst, image_paths)
        ]
        db.bulk_save_objects(image_objects)
        
        if violent_images:
            print(f"帖子 {new_post.uuid} 包含 {len(violent_images)} 张违规图片")
            
        db.commit()
        return {
            "error_code": 0,
            "msg": "success",
            "uuid": str(new_topic.uuid),
            "has_sensitive_images": len(violent_images) > 0
        }

    except Exception as e:
        db.rollback()
        # 清理已保存的文件
        if 'image_paths' in locals():
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
        return {
            "error_code": 1,
            "msg": f"创建失败: {return_error_message(e)}",
            "uuid": "0"
        }


async def validate_parent_post(db: Session, topic_uuid: str, floor_number: int) -> Optional[APost]:
    """验证父帖子的层数是否存在"""
    if floor_number == 0:
        return None
    
    # 查找指定主题中对应层数的帖子
    parent_post = db.query(APost).filter(
        APost.parent_topic_uuid == topic_uuid,
        APost.back_to == 0,  # 只查找直接回复主题的帖子
    ).order_by(APost.create_time).offset(floor_number - 1).first()
    
    if not parent_post:
        raise HTTPException(status_code=400, detail="回复的楼层不存在")
    return parent_post

@app.post("/{post_id}/reply")
async def create_reply(
    request: Request,
    background_tasks: BackgroundTasks,
    post_id: str = Path(..., title="话题UUID"),
    author: str = Form(...),
    content: str = Form(...),
    pic_lst: List[UploadFile] = File(None),
    reply_to: int = Form(0),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if pic_lst is None:
        pic_lst = []
    if author not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # 转换UUID格式
        topic_uuid = uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的话题UUID格式")

    try:
        db.begin()
        
        # 验证话题是否存在
        topic = db.query(TotalTopic).filter(TotalTopic.uuid == topic_uuid).first()
        if not topic:
            raise HTTPException(status_code=404, detail="指定的话题不存在")

        # 验证父帖子
        # parent_post = await validate_parent_post(db, topic_uuid, reply_to)
        
        # 创建新回复
        new_reply = APost(
            uuid=uuid.uuid4(),
            author_name=author,
            content=content,
            parent_topic_uuid=topic_uuid,
            back_to=reply_to,
            create_time=time.time(),
            visible_state = -1  # 待审核状态
        )
        db.add(new_reply)
        db.flush()
        
        # 添加内容审核后台任务
        background_tasks.add_task(check_content, content, pic_lst, new_reply.uuid)
        
        # 处理图片上传和检测
        saved_images = []
        violent_images = []
        
        for image in pic_lst:
            try:
                # 异步保存图片和检测内容
                file_path, is_violent = await async_save_image(image, str(new_reply.uuid), request)
                saved_images.append(file_path)
                
                if is_violent:
                    violent_images.append(file_path)
                
                # 创建图片记录
                img_record = MyImageModel(
                    title=image.filename,
                    image_path=file_path,
                    post_uuid=new_reply.uuid
                )
                db.add(img_record)
            except Exception as e:
                # 回滚已保存文件
                for path in saved_images:
                    if os.path.exists(path):
                        os.remove(path)
                raise HTTPException(500, f"图片保存失败: {return_error_message(e)}")
        
        # 如果有违规图片，可以进行额外处理
        if violent_images:
            print(f"回复 {new_reply.uuid} 包含 {len(violent_images)} 张违规图片")
            # 可以在这里添加额外处理逻辑，例如直接设置帖子为待审核状态
        
        # 更新话题更新时间
        topic.update_time = time.time()
        
        db.commit()
        return {
            "error_code": 0,
            "msg": "回复成功",
            "has_sensitive_images": len(violent_images) > 0
        }

    except HTTPException as he:
        db.rollback()
        return {
            "error_code": 1,
            "msg": he.detail
        }
    except Exception as e:
        db.rollback()
        return {
            "error_code": 1,
            "msg": f"回复失败: {return_error_message(e)}"
        }


@app.get("/{topic_uuid_str}/{base_floor}")
async def get_floors(
    topic_uuid_str: str = Path(..., title="话题UUID"),
    base_floor: int = Path(..., ge=1, title="起始楼层"),
    nickname: str = Query(..., title="请求者昵称"),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # 验证UUID有效性
        topic_uuid = uuid.UUID(topic_uuid_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法UUID格式")

    # 获取主题信息
    topic = db.query(TotalTopic).filter(TotalTopic.uuid == topic_uuid).first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")

    # 计算分页参数
    page_size = 20

    # 获取总楼层数
    total_floors = db.query(APost).filter(
        APost.parent_topic_uuid == topic_uuid, APost.visible_state == 0
    ).count()

    # NOTE: let base_floor be a index from 0
    base_floor -= 1
    # 检查请求是否越界
    if base_floor >= total_floors:
        return {"floors": []}

    # 获取主楼层（分页查询）
    main_posts = db.query(APost).filter(
        APost.parent_topic_uuid == topic_uuid, APost.visible_state == 0
    ).order_by(APost.create_time.asc()).offset(base_floor).limit(page_size).all()
    response_data = []
    for ind, post in enumerate(main_posts):
        # 转换图片数据
        pic_data = []
        for img in post.images:
            try:
                with open(img.image_path, "rb") as f:
                    pic_data.append(base64.b64encode(f.read()).decode())
            except Exception as e:
                print(f"图片加载失败: {return_error_message(e)}")

        # 判断点赞状态
        like_set = post.like_set
        is_liked = 1 if nickname in like_set else 0

        # 构建楼层信息
        floor_info = {
            "nickname": post.author_name,
            "content": post.content,
            "create_time": post.create_time,
            "back_to": post.back_to,
            "pic_lst": pic_data,
            "like_num": post.like_num,
            "is_liked": is_liked,
            "index": ind+ base_floor + 1,
        }
        response_data.append(floor_info)
    topic.view_times+=1
    db.commit()
    return {"floors": response_data}


def construct_response(topics: List[TotalTopic], show_viewtime:bool=False):
    # 构建响应数据
    formatted_posts = []
    for topic in topics:
        # 提取标签字符串列表
        tag_list = [tag.tag for tag in topic.tags]
        
        formatted_post = {
            "uuid": str(topic.uuid),
            "nickname": topic.author_name,
            "title": topic.topic_title,
            "update_time": topic.update_time,
            "tag_lst": tag_list,
        }
        if show_viewtime:
            formatted_post["view_times"] = topic.view_times
        formatted_posts.append(formatted_post)

    return {"posts": formatted_posts}

@app.get("/", response_model=dict)
async def get_recent_posts(
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    
    # 获取最新20个主题（按最后更新时间排序）
    topics = db.query(TotalTopic).options(
        joinedload(TotalTopic.tags)  # 预加载标签数据
    ).order_by(
        TotalTopic.update_time.desc()
    ).limit(20).all()

    # 构建响应数据
    return construct_response(topics)

@app.get("/hot")
async def get_hot_posts(
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 获取最新20个主题（按最后更新时间排序）
    topics = db.query(TotalTopic).options(
        joinedload(TotalTopic.tags)  # 预加载标签数据
    ).order_by(
        TotalTopic.view_times.desc()
    ).limit(20).all()

    return construct_response(topics, show_viewtime=True)


class CancelLikeRequest(BaseModel):
    nickname: str
    uuid: str  # 话题的UUID
    floor: int  # 楼层数

@app.post("/cancel-like")
async def cancel_like(request: CancelLikeRequest,
                      user: Tuple[User, List[str]] = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    if request.nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # 根据话题UUID和楼层找到对应的APost
        apost = db.query(APost).filter(
        APost.parent_topic_uuid == uuid.UUID(request.uuid), APost.visible_state == 0
        ).order_by(APost.create_time.asc()).offset(request.floor-1).first()
        
        if not apost:
            raise HTTPException(status_code=404, detail="Post not found")
        like_set = set(apost.like_set)
        # 从like_set中移除用户（原子操作）
        if request.nickname in like_set:
            like_set.remove(request.nickname)
            apost.like_num  = len(like_set)
            apost.like_set = list(like_set)
            db.commit()
            return {"error_code": 0, "msg": "Success"}
        else:
            return {"error_code": 1, "msg": "User not in like set"}
    except Exception as e:
        db.rollback()
        return {"error_code": 2, "msg": return_error_message(e)}
    finally:
        db.close()

@app.post("/like")
async def like(request: CancelLikeRequest, 
               user: Tuple[User, List[str]] = Depends(get_current_active_user),
               db: Session = Depends(get_db)):
    if request.nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # 根据话题UUID和楼层找到对应的APost
        apost = db.query(APost).filter(
        APost.parent_topic_uuid == uuid.UUID(request.uuid), APost.visible_state == 0
        ).order_by(APost.create_time.asc()).offset(request.floor-1).first()
        
        if not apost:
            raise HTTPException(status_code=404, detail="Post not found")
        like_set = set(apost.like_set)
        if request.nickname not in like_set:
            like_set.add(request.nickname)
            apost.like_num  = len(like_set)
            apost.like_set = list(like_set)
            db.commit()
            return {"error_code": 0, "msg": "Success"}
        else:
            return {"error_code": 1, "msg": "User not in like set"}
    except Exception as e:
        db.rollback()
        print(f"Error in like: {return_error_message(e)}")
        return {"error_code": 2, "msg": return_error_message(e)}
    finally:
        db.close()

@app.get("/notice")
async def get_notice(
    nickname : str,
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    posts = db.query(APost).filter(
            APost.author_name == nickname
        ).order_by(
            APost.create_time.desc()
        ).limit(20).all() 
    response_data = []
    for ind, post in enumerate(posts):
        # 构建楼层信息
        floor_info = {
            "timestamp": post.create_time,
            "title" : db.query(TotalTopic).filter(TotalTopic.uuid == post.parent_topic_uuid).first().topic_title,
            "passed": post.visible_state
        }
        response_data.append(floor_info)
    return {"floors": response_data}


topic_route = APIRouter()


@topic_route.get("/searchtag")
async def search_tag(tag: str, user: Tuple[User, List[str]] = Depends(get_current_active_user), db: Session = Depends(get_db)):
    topics = db.query(TotalTopic).options(
        joinedload(TotalTopic.tags)  # 预加载标签数据
    ).filter(TotalTopic.tags.any(Tag.tag == tag)).order_by(
        TotalTopic.update_time.desc()
    ).limit(20).all()

    return construct_response(topics)

@topic_route.get("/search")
async def search(keyword: str, user: Tuple[User, List[str]] = Depends(get_current_active_user), db: Session = Depends(get_db)):
    topics = db.query(TotalTopic).options(
        joinedload(TotalTopic.tags)
    ).filter(TotalTopic.topic_title.like(f'%{keyword}%')).order_by(
        TotalTopic.update_time.desc()
    ).limit(20).all()

    return construct_response(topics)
