from pydantic import BaseModel
from typing import List, Optional

# 申请私聊请求
class InviteRequest(BaseModel):
    src_nickname: str
    dst_nickname: str
    message: str
    publickey: str

# 申请私聊响应
class InviteResponse(BaseModel):
    error_code: int
    message: str

# 获取申请消息响应
class GetInviteResponse(BaseModel):
    invite_message_lst: List[dict]

# 获取邀请情况响应
class InviteStateResponse(BaseModel):
    state_lst: List[dict]

# 决定是否接受私聊邀请请求
class ChooseRequest(BaseModel):
    choice: int
    src_nickname: str
    publickey: Optional[str] = None
    dst_nickname: str

# 决定是否接受私聊邀请响应
class ChooseResponse(BaseModel):
    error_code: int
    message: str

# 发送私聊信息请求
class MessageRequest(BaseModel):
    src_nickname: str
    dst_nickname: str
    message: str

# 发送私聊信息响应
class SendResponse(BaseModel):
    error_code: int
    message: str

# 查收私聊信息响应
class ReceiveResponse(BaseModel):
    message_lst: List[dict]

# 查看与指定人的私聊信息响应
class ChatMessagesResponse(BaseModel):
    message_lst: List[dict]

# 查看与指定人的私聊中对方的公钥响应
class PublicKeyResponse(BaseModel):
    error_code: int
    msg: str
    publickey: str