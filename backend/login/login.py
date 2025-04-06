from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, captcha, security_questions, identity
from .security_questions import generate_salt, hash_password
from .database import SessionLocal, engine
from .auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_user_by_username, REFRESH_TOKEN_EXPIRE_DAYS, ALGORITHM, SECRET_KEY
from jose import JWTError, jwt

models.Base.metadata.create_all(bind=engine)

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/get-captcha", response_model=schemas.CaptchaResponse)
async def get_captcha():
    return captcha.generate_captcha()

@router.post("/register", response_model=schemas.LoginResponse)
async def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    # Validate CAPTCHA first
    if not captcha.validate_captcha(user.captcha_id, user.captcha_code):
        return {"error_code": 2, "message": "Invalid or expired CAPTCHA"}
    
    # Rest of registration logic
    existing_user = db.query(models.User).filter(models.User.account == user.username).first()
    if existing_user:
        return {"error_code": 1, "message": "Username already taken"}
    
    salt = generate_salt()
    hashed_password = hash_password(user.password, salt)
    
    db_user = models.User(
        account=user.username,
        hashed_password=hashed_password,
        salt=salt
    )
    
    db.add(db_user)
    db.commit()
    
    return {"error_code": 0, "message": "Registration successful"}

@router.post("/login", response_model=schemas.LoginResponse)
async def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    if not captcha.validate_captcha(user.captcha_id, user.captcha_code):
        return {"error_code": 3, "message": "Invalid or expired CAPTCHA"}
    # Find the user by account name
    db_user = db.query(models.User).filter(models.User.account == user.account_name).first()
    
    if not db_user:
        return {"error_code": 2, "message": "User not found"}
    
    hashed_input = hash_password(user.password_hash, db_user.salt)
    if hashed_input != db_user.hashed_password:
        return {"error_code": 1}
    last_used_identity = db_user.last_used_identity.nickname
    return {"error_code": 0, "message": "Login successful", "last_used_identity": last_used_identity}

@router.post("/get-security-questions", response_model=schemas.SecurityQuestionResponse)
async def get_security_questions(request: schemas.SecurityQuestionRequest, db: Session = Depends(get_db)):
    questions = security_questions.get_user_questions(db, request.username)
    if not questions:
        raise HTTPException(status_code=404, detail="User not found")
    return {"questions": questions}

@router.post("/verify-security-answer")
async def verify_security_answer(request: schemas.VerifySecurityAnswer, db: Session = Depends(get_db)):
    is_valid = security_questions.verify_answer(db, request.username, request.question_id, request.answer)
    return {"valid": is_valid}

@router.get("/get-random-security-questions")
async def get_random_security_questions(db: Session = Depends(get_db)):
    selected_questions = security_questions.get_random_questions(count=3)
    return selected_questions

@router.post("/verify-reset", response_model=schemas.VerifyResetResponse)
async def verify_and_reset(
    request: schemas.VerifyResetRequest, 
    db: Session = Depends(get_db)
):
    # Verify security answers
    if not security_questions.verify_reset_answers(db, request.username, request.security_answers):
        return {
            "success": False,
            "message": "Invalid security answers"
        }
    
    if not security_questions.validate_password(request.new_password):
        return {
            "success": False,
            "message": "Password must be at least 8 characters with uppercase and numbers"
        }
    # Reset password
    if not security_questions.reset_password(db, request.username, request.new_password):
        return {
            "success": False,
            "message": "Failed to reset password"
        }
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }

# Optional: Get all identities for a user
@router.get("/show-identities")
async def get_identities(username: str, db: Session = Depends(get_db)):
    """Get all identities for a user"""
    identities = identity.get_user_identities(db, username)
    return {"identities": identities}

@router.post("/token", response_model=schemas.TokenPair)
async def login_for_access_token(
    request: schemas.GetTokenRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with short expiry
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.account, "type": "access"}, 
        expires_delta=access_token_expires
    )
    
    # Create refresh token with longer expiry
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        data={"sub": user.account, "type": "refresh"},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access": access_token,
        "refresh": refresh_token,
        "token_type": "bearer"
    }

@router.post("/token/refresh", response_model=schemas.AccessToken)
async def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        # Decode and validate the refresh token
        payload = jwt.decode(
            request.refresh, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Check token type and expiration
        username = payload.get("sub")
        token_type = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the user still exists
        user = get_user_by_username(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username, "type": "access"},
            expires_delta=access_token_expires
        )
        
        # Return only the new access token
        return {"access": access_token}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/create-identity", response_model=schemas.CreateIdentityResponse)
async def create_identity(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new anonymous identity for the authenticated user"""
    # Now using the authenticated user's username instead of trusting request data
    result = identity.create_identity(db, current_user.account)
    return result

# Update identity deletion endpoint to require authentication
@router.delete("/delete-identity", response_model=schemas.DeleteIdentityResponse)
async def delete_identity(
    request: schemas.DeleteIdentityRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an anonymous identity for the authenticated user"""
    # Verify that the username in the request matches the authenticated user
    if request.username != current_user.account:
        return {"error_code": 7, "msg": "Unauthorized operation"}
    
    result = identity.delete_identity(db, current_user.account, request.nickname)
    return result

@router.post("/update-identity", response_model=schemas.UpdateIdentityResponse)
async def update_identity(
    request: schemas.UpdateIdentityRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the user's current active identity"""
    # Ensure the user can only update their own identity
    if request.username != current_user.account:
        return {"error_code": 1, "message": "Unauthorized operation"}
    
    # Update the current identity
    result = identity.update_current_identity(db, current_user.account, request.identity)
    return result

# Optional: Add an endpoint to get the current identity
@router.get("/current-identity")
async def get_current_identity(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the user's current active identity"""
    nickname = identity.get_current_identity(db, current_user.id)
    return {"nickname": nickname}

@router.post("/create-first-identity/", response_model=schemas.CreateFirstIdentityResponse)
async def create_first_identity(
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create first identity for a new user"""
    
    # Create the first identity
    result = identity.create_first_identity(db, username)
    return result