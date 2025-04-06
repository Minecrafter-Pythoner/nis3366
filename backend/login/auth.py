from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas
from .database import get_db

# Security constants
SECRET_KEY = "apri1_f0o1$"  # In production, use a proper secret key generator and store securely
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify password using the same hashing method as login.py"""
    from .login import hash_password
    return hash_password(plain_password, salt) == hashed_password

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user and return user object if valid"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password, user.salt):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.account == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.account == username).first()
    if user is None:
        raise credentials_exception
    all_nickname = db.query(models.AnonymousIdentity.nickname).filter(models.AnonymousIdentity.user_id == user.id).all()
    return user, [nickname for (nickname,) in all_nickname]

def get_user_by_username(db: Session, username: str):
    """
    Retrieve a user from the database by username.
    
    Args:
        db (Session): The database session
        username (str): The username to search for
        
    Returns:
        User: The user object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.account == username).first()