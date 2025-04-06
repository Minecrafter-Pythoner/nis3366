from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column, backref
from sqlalchemy.sql import func
from ..login.models import AnonymousIdentity, Base 
# ---------------------------
# SQLAlchemy 模型定义 (数据库层)
# ---------------------------

class StatusChoice(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class ChatInvitation(Base):
    __tablename__ = "chat_invitation"

    id = Column(Integer, primary_key=True)
    src_identity_id = mapped_column(Integer, ForeignKey("anonymous_identities.id"))
    dst_identity_id = mapped_column(Integer, ForeignKey("anonymous_identities.id"))
    message = Column(Text)
    publickey = Column(Text, default="")
    dst_publickey = Column(Text, default="")
    status = Column(String(10), default=StatusChoice.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    src_identity = relationship("AnonymousIdentity", foreign_keys=[src_identity_id], backref=backref("sent_invitations"))
    dst_identity = relationship("AnonymousIdentity", foreign_keys=[dst_identity_id], backref=backref("received_invitations"))

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message = Column(Text)
    owner_id = mapped_column(Integer, ForeignKey("anonymous_identities.id"))

    owner = relationship("AnonymousIdentity", foreign_keys=[owner_id], backref=backref("messages"))

# 多对多关联表
chat_message_association = Table(
    "chat_message_association",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chat.id")),
    Column("message_id", Integer, ForeignKey("message.id"))
)

class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    src_identity_id = mapped_column(Integer, ForeignKey("anonymous_identities.id"))
    dst_identity_id = mapped_column(Integer, ForeignKey("anonymous_identities.id"))
    last_update = Column(Float)

    src_identity = relationship("AnonymousIdentity", foreign_keys=[src_identity_id], backref=backref("src_chats"))
    dst_identity = relationship("AnonymousIdentity", foreign_keys=[dst_identity_id], backref=backref("dst_chats"))
    messages = relationship("Message", secondary=chat_message_association, backref=backref("chats"))

# ---------------------------
# Pydantic 模型定义 (接口层)
# ---------------------------

class ChatInvitationBase(BaseModel):
    src_identity_id: int
    dst_identity_id: int
    message: str
    publickey: str = ""
    dst_publickey: str = ""
    status: StatusChoice = StatusChoice.PENDING

class ChatInvitationCreate(ChatInvitationBase):
    pass

class ChatInvitationUpdate(BaseModel):
    status: StatusChoice

class ChatInvitationResponse(ChatInvitationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    message: str
    owner_id: int

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ChatBase(BaseModel):
    src_identity_id: int
    dst_identity_id: int
    last_update: float

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True