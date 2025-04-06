import string
import secrets
import random
from sqlalchemy.orm import Session
from . import models

def generate_unique_nickname(db: Session, length=10) -> str:
    """Generate a unique random nickname"""
    # Define character sets for different parts of the nickname
    adjectives = [
        "swift", "bold", "wise", "calm", "brave", "kind", "tiny", "mega", 
        "super", "cool", "smart", "quiet", "loud", "crazy", "happy", "sunny"
    ]
    
    nouns = [
        "wolf", "bear", "tiger", "eagle", "hawk", "fox", "deer", "lion", 
        "panda", "koala", "otter", "raven", "owl", "ninja", "wizard", "ranger"
    ]
    
    # Generate a nickname with format: adjective + noun + random number
    while True:
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        number = ''.join(random.choices(string.digits, k=3))
        
        nickname = f"{adjective}{noun}{number}"
        
        # Check if nickname already exists
        existing = db.query(models.AnonymousIdentity).filter(
            models.AnonymousIdentity.nickname == nickname
        ).first()
        
        if not existing:
            return nickname

def get_user_identity_count(db: Session, user_id: int) -> int:
    """Get the number of identities a user currently has"""
    return db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.user_id == user_id
    ).count()

def create_identity(db: Session, username: str) -> dict:
    """Create a new anonymous identity for a user"""
    # Find the user
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return {"error_code": 2, "message": "User not found"}
    
    # Check if user already has 5 identities
    identity_count = get_user_identity_count(db, user.id)
    if identity_count >= 5:
        return {"error_code": 1, "message": "Maximum identities reached (5)"}
    
    # Generate a unique nickname
    nickname = generate_unique_nickname(db)
    
    # Create new identity
    new_identity = models.AnonymousIdentity(
        nickname=nickname,
        user_id=user.id
    )
    
    db.add(new_identity)
    db.commit()
    
    return {"error_code": 0, "nickname": nickname}

def get_user_identities(db: Session, username: str) -> list:
    """Get all identities for a user"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return []
    
    identities = db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.user_id == user.id
    ).all()
    
    return [identity.nickname for identity in identities]

def delete_identity(db: Session, username: str, nickname: str) -> dict:
    """Delete a specific anonymous identity for a user"""
    # Find the user
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return {"error_code": 2, "msg": "User not found"}
    
    # Find the identity
    identity = db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.nickname == nickname,
        models.AnonymousIdentity.user_id == user.id
    ).first()
    
    if not identity:
        return {"error_code": 1, "msg": "Username/nickname mismatch or nickname doesn't exist"}
    
    # Delete the identity
    db.delete(identity)
    db.commit()
    
    return {"error_code": 0, "msg": "Identity deleted successfully"}

def verify_identity_ownership(db: Session, username: str, nickname: str) -> bool:
    """Verify if an identity belongs to a user"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return False
    
    identity = db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.nickname == nickname,
        models.AnonymousIdentity.user_id == user.id
    ).first()
    
    return identity is not None

def update_current_identity(db: Session, username: str, nickname: str) -> dict:
    """Update the user's current identity"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return {"error_code": 2, "message": "User not found"}
    
    identity = db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.nickname == nickname,
        models.AnonymousIdentity.user_id == user.id
    ).first()
    
    if not identity:
        return {"error_code": 1, "message": "Identity does not belong to this user"}
    
    # Update the user's last used identity
    user.last_used_identity_id = identity.id
    db.commit()
    
    return {"error_code": 0, "message": "Successfully switched to identity: " + nickname}

def get_current_identity(db: Session, user_id: int) -> str:
    """Get the current identity nickname for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.last_used_identity_id:
        return None
    
    identity = db.query(models.AnonymousIdentity).filter(
        models.AnonymousIdentity.id == user.last_used_identity_id
    ).first()
    
    return identity.nickname if identity else None

def create_first_identity(db: Session, username: str) -> dict:
    """Create first identity for a new user"""
    # Find the user
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return {"error_code": 2, "message": "User not found"}
    
    # Check if user already has identities
    identity_count = get_user_identity_count(db, user.id)
    if identity_count > 0:
        return {"error_code": 1, "message": "User already has identities"}
    
    # Generate a unique nickname
    nickname = generate_unique_nickname(db)
    
    # Create new identity
    new_identity = models.AnonymousIdentity(
        nickname=nickname,
        user_id=user.id
    )
    
    db.add(new_identity)
    db.flush()  # This makes the database assign an ID without committing the transaction
    
    # Set this as the user's last used identity
    user.last_used_identity_id = new_identity.id
    
    db.commit()
    
    return {"error_code": 0, "message": "First identity created successfully", "nickname": nickname}