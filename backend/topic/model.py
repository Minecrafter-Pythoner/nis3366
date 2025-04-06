from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..login.models import AnonymousIdentity, Base 

# 数据库配置
# DATABASE_URL = "sqlite:///./topic.db"
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# 主题与标签的多对多关联表（保持不变）
topic_tag_association = Table(
    'topic_tag_association', Base.metadata,
    Column('topic_uuid', UUID(as_uuid=True), ForeignKey('totaltopic.uuid')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

class MyImageModel(Base):
    __tablename__ = "myimagemodel"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    image_path = Column(String(255), unique=True)  # 添加唯一约束
    post_uuid = Column(
        UUID(as_uuid=True), 
        ForeignKey('apost.uuid'), 
        nullable=False,
        index=True  # 添加索引
    )
    post = relationship("APost", back_populates="images")

class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String(10), unique=True)
    topics = relationship("TotalTopic", secondary=topic_tag_association, back_populates="tags")

class TotalTopic(Base):
    __tablename__ = "totaltopic"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_name = Column(String(100))
    topic_title = Column(String(100))
    create_time = Column(Float)
    update_time = Column(Float)
    view_times = Column(Integer, default=0)
    posts = relationship("APost", back_populates="topic", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=topic_tag_association, back_populates="topics")

class APost(Base):
    __tablename__ = "apost"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_name = Column(String(100), index=True)
    back_to = Column(Integer)
    content = Column(String)
    create_time = Column(Float, index=True)
    visible_state = Column(Integer, default=-1) # -1 means wait for checking, 1 means check failed and 0 means check passed
    parent_topic_uuid = Column(
        UUID(as_uuid=True), 
        ForeignKey('totaltopic.uuid'),
        index=True  # 添加索引
    )
    topic = relationship("TotalTopic", back_populates="posts")
    like_num = Column(Integer, default=0)
    # 修改为一对多关系（一个帖子多个图片）
    images = relationship("MyImageModel", back_populates="post", cascade="all, delete-orphan")
    like_set = Column(JSON, default=lambda: [])  # 修改为JSON类型，默认空列表

