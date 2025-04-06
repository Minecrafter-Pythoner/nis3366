from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    account = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    salt = Column(String)
    
    # Add column to store the last used identity ID
    last_used_identity_id = Column(Integer, ForeignKey("anonymous_identities.id"), nullable=True)
    
    # Add relationship to anonymous identities
    identities = relationship("AnonymousIdentity", back_populates="user", 
                             foreign_keys="[AnonymousIdentity.user_id]")
    
    # Add relationship to last used identity
    last_used_identity = relationship("AnonymousIdentity", 
                                     foreign_keys="[User.last_used_identity_id]")

class SecurityQuestion(Base):
    __tablename__ = "security_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String(255), unique=True)

class UserQuestion(Base):
    __tablename__ = "user_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("security_questions.id"))
    answer_hash = Column(String(255))
    salt = Column(String(32))
    
    question = relationship("SecurityQuestion")
    user = relationship("User")

class AnonymousIdentity(Base):
    __tablename__ = "anonymous_identities"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nickname = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="identities", foreign_keys="[AnonymousIdentity.user_id]")
