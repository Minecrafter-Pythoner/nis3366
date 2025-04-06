from sqlalchemy.orm import Session
from . import models, schemas
import random
import hashlib
import secrets
import string

from typing import List

SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What is the name of your first school?",
    "What is your favorite food?",
    "What was the make of your first car?",
    "What was the name of your childhood best friend?",
    "What was the name of your first employer?",
    "What is the name of the street you grew up on?"
]

def generate_salt(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()

# Predefined security questions
DEFAULT_SECURITY_QUESTIONS = [
    "What was your first pet's name?",
    "In what city were you born?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
    "What was your childhood nickname?",
    "What is the name of your favorite childhood friend?",
]

def hash_answer(answer: str, salt: str) -> str:
    """Hash security answer with salt"""
    return hashlib.sha256((answer + salt).encode()).hexdigest()

def get_random_questions(count: int = 3) -> list:
    """Get random security questions"""
    return {"questions": random.sample(SECURITY_QUESTIONS, min(count, len(SECURITY_QUESTIONS)))}

def get_user_questions(db: Session, username: str) -> list:
    """Get security questions for a user"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return []
    
    # Check if user already has questions set
    user_questions = db.query(models.UserQuestion).filter(
        models.UserQuestion.user_id == user.id
    ).all()
    
    if user_questions:
        # Return the user's specific questions
        return [q.question.question_text for q in user_questions[:3]]
    else:
        # Return fresh random questions
        return [get_random_questions(3)["questions"]]

def verify_answer(db: Session, username: str, question_id: int, answer: str) -> bool:
    """Verify security answer"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return False
    
    user_question = db.query(models.UserQuestion).filter(
        models.UserQuestion.user_id == user.id,
        models.UserQuestion.question_id == question_id
    ).first()
    
    if not user_question:
        return False
    
    hashed_input = hash_answer(answer, user_question.salt)
    return hashed_input == user_question.answer_hash

def verify_reset_answers(db: Session, username: str, answers: List[str]) -> bool:
    """Verify all security answers for password reset"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return False
    
    user_questions = db.query(models.UserQuestion).filter(
        models.UserQuestion.user_id == user.id
    ).all()
    
    if len(user_questions) != len(answers):
        return False
    
    # Verify each answer
    for i, question in enumerate(user_questions):
        if not verify_answer(db, username, question.question_id, answers[i]):
            return False
    
    return True

def reset_password(db: Session, username: str, new_password: str) -> bool:
    """Reset user password"""
    user = db.query(models.User).filter(models.User.account == username).first()
    if not user:
        return False
    
    salt = generate_salt()
    hashed_password = hash_password(new_password, salt)
    
    user.hashed_password = hashed_password
    user.salt = salt
    db.commit()
    return True

def validate_password(password: str) -> bool:
    """Basic password validation"""
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True
