from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Tuple
import os, json, random
import numpy as np

from . import models, schemas
from ..login.models import AnonymousIdentity, User
from ..login.auth import get_current_active_user
from ..login.database import engine, SessionLocal, get_db, Base
from ..topic.model import APost
from pydantic import BaseModel

Base.metadata.create_all(bind=engine)

app = FastAPI()

py_dir = os.path.dirname(__file__)

with open(f"{py_dir}/config.json", "r") as file:
    config_dic = json.load(file)

noise_scale = config_dic['sensitivity']/config_dic["epsilion"]

def add_noise(query_result):
    noise = np.random.laplace(0, noise_scale)
    return query_result + noise

# 辅助函数：获取身份ID
def get_identity_id(db: Session, nickname: str):
    identity = db.query(models.AnonymousIdentity).filter_by(nickname=nickname).first()
    if not identity:
        breakpoint()
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity.id

# 辅助函数：获取身份公钥
def get_publickey(db: Session, nickname: str):
    identity = db.query(models.AnonymousIdentity).filter_by(nickname=nickname).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity.publickey

@app.get("/recommend")
def recommend_people(
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    identity_id = get_identity_id(db, nickname)

    # construct exclude_ide set
    exclude_id = {identity_id}
    chat_invitations = db.query(models.ChatInvitation).filter(
        (models.ChatInvitation.src_identity_id == identity_id) |
        (models.ChatInvitation.dst_identity_id == identity_id)
    ).all()
    for chat_invitation in chat_invitations:
        tar_indentityi = chat_invitation.src_identity_id if chat_invitation.dst_identity_id == identity_id else chat_invitation.dst_identity_id
        exclude_id.add(tar_indentityi)

    recommend_dic:dict[str, int] = {}
    # add chat values
    chats = db.query(models.Chat).filter(
        (models.Chat.src_identity_id == identity_id) | (models.Chat.dst_identity_id == identity_id)
    ).order_by(models.Chat.last_update.desc()).limit(20).all()
    for chati in chats:
        tar_indentityi = chati.src_identity_id if chati.dst_identity_id == identity_id else chati.dst_identity_id
        all_chati = db.query(models.Chat).filter(
            (models.Chat.src_identity_id == identity_id) | (models.Chat.dst_identity_id == identity_id)
        ).order_by(models.Chat.last_update.desc()).limit(20).all()
        for chatj in all_chati:
            tar_indentityj = chatj.src_identity_id if chatj.dst_identity_id == identity_id else chatj.dst_identity_id
            if tar_indentityj in exclude_id:
                continue
            if tar_indentityj not in recommend_dic:
                recommend_dic[tar_indentityj] = config_dic["same_friend_val"]
            else:
                recommend_dic[tar_indentityj] += config_dic["same_friend_val"]
    # TODO: add posts values
    posts = db.query(APost).filter(APost.like_set.like(f'%{nickname}%')).all()
    for posti in posts:
        for likei in posti.like_set:
            likei_id = db.query(AnonymousIdentity).filter(AnonymousIdentity.nickname == likei).first().id
            if likei_id in exclude_id:
                continue
            if likei_id not in recommend_dic:
                recommend_dic[likei_id ] = config_dic["same_like_val"]
            else:
                recommend_dic[likei_id ] += config_dic["same_like_val"]
    

    recommend_dic = {k: add_noise(v) for k,v in recommend_dic.items()}

    recommend_lst = sorted(recommend_dic.items(), key=lambda x: x[1], reverse=True)
    res_set = {db.query(AnonymousIdentity).filter(AnonymousIdentity.id == i[0]).first().nickname for i in recommend_lst}
    if len(res_set) < config_dic["max_recommend"]:
        all_identity = list(db.query(AnonymousIdentity).all()[: 4*config_dic["max_recommend"]])
        random.shuffle(all_identity)
        for identityi in all_identity:
            if identityi.id not in exclude_id:
                res_set.add(identityi.nickname)
                if len(res_set)== config_dic["max_recommend"]:
                    break
    return {"error_code": 0, "recommend_lst": list(res_set)}
    

# 1. 申请私聊
@app.post("/invite", response_model=schemas.InviteResponse)
def create_chat_invite(
    invite_data: schemas.InviteRequest,
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if invite_data.src_nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    src_nickname = invite_data.src_nickname
    dst_nickname = invite_data.dst_nickname
    
    # 检查是否已经存在未处理的邀请
    existing_invite = db.query(models.ChatInvitation).filter(
        models.ChatInvitation.src_identity_id == get_identity_id(db, src_nickname),
        models.ChatInvitation.dst_identity_id == get_identity_id(db, dst_nickname),
        models.ChatInvitation.status == "pending"
    ).first()
    
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invite already exists")
    
    # 创建新的邀请
    new_invite = models.ChatInvitation(
        src_identity_id=get_identity_id(db, src_nickname),
        dst_identity_id=get_identity_id(db, dst_nickname),
        message=invite_data.message,
        publickey=invite_data.publickey
    )
    
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    return {"error_code": 0, "message": "Invite sent successfully"}

# 2. 获取申请消息
@app.get("/get-invite", response_model=schemas.GetInviteResponse)
def get_chat_invites(
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    identity_id = get_identity_id(db, nickname)
    
    # 获取所有未处理的邀请（最多20个）
    invites = db.query(models.ChatInvitation).filter(
        models.ChatInvitation.dst_identity_id == identity_id,
        models.ChatInvitation.status == "pending"
    ).order_by(models.ChatInvitation.created_at.desc()).limit(20).all()
    
    invite_list = []
    for invite in invites:
        src_identity = db.query(models.AnonymousIdentity).filter(models.AnonymousIdentity.id == invite.src_identity_id).first()
        invite_list.append({
            "src_nickname": src_identity.nickname,
            "timestamp": invite.created_at.timestamp(),
            "message": invite.message,
            "publickey": invite.publickey
        })
    
    return {"invite_message_lst": invite_list}

# 3. 获取邀请情况
@app.get("/invite-state", response_model=schemas.InviteStateResponse)
def get_invite_state(
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    identity_id = get_identity_id(db, nickname)
    
    # 获取所有由该用户发送的邀请（最多20个）
    invites = db.query(models.ChatInvitation).filter(
        models.ChatInvitation.src_identity_id == identity_id
    ).order_by(models.ChatInvitation.created_at.desc()).limit(20).all()
    
    state_list = []
    for invite in invites:
        dst_identity = db.get(models.AnonymousIdentity, invite.dst_identity_id)
        state_code = 0  # 默认未响应
        publickey = None
        
        if invite.status == "accepted":
            state_code = 1
            publickey = invite.dst_publickey
        elif invite.status == "declined":
            state_code = 2
        
        state_list.append({
            "state_code": state_code,
            "publickey": publickey
        })
    
    return {"state_lst": state_list}

# 4. 决定是否接受私聊邀请
@app.post("/choose", response_model=schemas.ChooseResponse)
def choose_chat_invite(
    choice_data: schemas.ChooseRequest,
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if choice_data.dst_nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    src_nickname = choice_data.src_nickname
    dst_nickname = choice_data.dst_nickname
    choice = choice_data.choice
    
    src_identity_id = get_identity_id(db, src_nickname)
    dst_identity_id = get_identity_id(db, dst_nickname)
    
    # 查找对应的邀请
    invite = db.query(models.ChatInvitation).filter(
        models.ChatInvitation.src_identity_id == src_identity_id,
        models.ChatInvitation.dst_identity_id == dst_identity_id,
        models.ChatInvitation.status == "pending"
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    # 更新邀请状态
    if choice == 0:  # 接受
        invite.status = "accepted"
        invite.dst_publickey = choice_data.publickey
        # 创建聊天记录
        new_chat = models.Chat(
            src_identity_id=src_identity_id,
            dst_identity_id=dst_identity_id,
            last_update=datetime.now().timestamp()
        )
        db.add(new_chat)
    else:  # 拒绝
        invite.status = "declined"
    
    db.commit()
    
    return {"error_code": 0, "message": "Choice processed successfully"}

# 5. 发送私聊信息
@app.post("/send", response_model=schemas.SendResponse)
def send_chat_message(
    message_data: schemas.MessageRequest,
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if message_data.src_nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    src_nickname = message_data.src_nickname
    dst_nickname = message_data.dst_nickname
    
    src_identity_id = get_identity_id(db, src_nickname)
    dst_identity_id = get_identity_id(db, dst_nickname)
    
    # 检查是否存在聊天记录
    chat = db.query(models.Chat).filter(
        (models.Chat.src_identity_id == src_identity_id) & (models.Chat.dst_identity_id == dst_identity_id) |
        (models.Chat.src_identity_id == dst_identity_id) & (models.Chat.dst_identity_id == src_identity_id)
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 创建新消息
    new_message = models.Message(
        message=message_data.message,
        owner_id=src_identity_id
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # 将消息关联到聊天
    chat.messages.append(new_message)
    chat.last_update = datetime.now().timestamp()
    db.commit()
    
    return {"error_code": 0, "message": "Message sent successfully"}

# 6. 查收私聊信息
@app.get("/receive", response_model=schemas.ReceiveResponse)
def receive_chat_messages(
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    identity_id = get_identity_id(db, nickname)
    
    # 获取所有与该用户相关的聊天
    chats = db.query(models.Chat).filter(
        (models.Chat.src_identity_id == identity_id) | (models.Chat.dst_identity_id == identity_id)
    ).order_by(models.Chat.last_update.desc()).limit(20).all()
    
    message_list = []
    for chat in chats:
        # 获取对方的昵称
        if chat.src_identity_id == identity_id:
            other_identity = db.get(models.AnonymousIdentity, chat.dst_identity_id)
        else:
            other_identity = db.get(models.AnonymousIdentity, chat.src_identity_id)
        
        # 获取最后一条消息
        last_message = chat.messages[-1] if chat.messages else None
        
        message_list.append({
            "src_nickname": other_identity.nickname,
            "last_message": last_message.message if last_message else "",
            "timestamp": last_message.created_at.timestamp() if last_message else 0
        })
    
    return {"message_lst": message_list}

# 7. 查看与指定人的私聊信息
@app.get("/{target_nickname}", response_model=schemas.ChatMessagesResponse)
def get_chat_messages_with_target(
    target_nickname: str,
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    src_identity_id = get_identity_id(db, nickname)
    target_identity_id = get_identity_id(db, target_nickname)
    
    # 查找聊天记录
    chat = db.query(models.Chat).filter(
        ((models.Chat.src_identity_id == src_identity_id) & (models.Chat.dst_identity_id == target_identity_id)) |
        ((models.Chat.src_identity_id == target_identity_id) & (models.Chat.dst_identity_id == src_identity_id))
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 获取最近20条消息
    messages = chat.messages[-20:]
    
    message_list = []
    for msg in reversed(messages):  # 反转以按时间顺序排列
        owner = db.query(models.AnonymousIdentity).filter(models.AnonymousIdentity.id == msg.owner_id).first()
        message_list.append({
            "message": msg.message,
            "timestamp": msg.created_at.timestamp(),
            "owner": 0 if msg.owner_id == src_identity_id else 1
        })
    
    return {"message_lst": message_list}

# 8. 查看与指定人的私聊中对方的公钥
@app.get("/publickey/{target_nickname}", response_model=schemas.PublicKeyResponse)
def get_target_publickey(
    target_nickname: str,
    nickname: str = Query(...),
    user: Tuple[User, List[str]] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if nickname not in user[1]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    my_identity_id = get_identity_id(db, nickname)
    target_identity_id = get_identity_id(db, target_nickname)
    
    # 检查是否存在聊天记录
    chat = db.query(models.ChatInvitation).filter(
        ((models.ChatInvitation.src_identity_id == my_identity_id) & (models.ChatInvitation.dst_identity_id == target_identity_id)) |
        ((models.ChatInvitation.src_identity_id == target_identity_id) & (models.ChatInvitation.dst_identity_id == my_identity_id))
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 获取对方的公钥
    target_pk = chat.dst_publickey if chat.src_identity_id == my_identity_id else chat.publickey
    return {
        "error_code": 0,
        "msg": "Success",
        "publickey": target_pk
    }

