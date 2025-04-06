from pydantic import BaseModel
from typing import Optional, List, Dict

class UserLogin(BaseModel):
    account_name: str
    password_hash: str
    captcha_code: str
    captcha_id: str

class UserRegister(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    error_code: int
    message: Optional[str] = None
    last_used_identity: Optional[str] = None

class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str

class UserRegister(BaseModel):
    username: str
    password: str
    captcha_code: str
    captcha_id: str

class SecurityQuestionRequest(BaseModel):
    username: str

class SecurityQuestionResponse(BaseModel):
    questions: List[str]

class VerifySecurityAnswer(BaseModel):
    username: str
    question_id: int
    answer: str

class SetSecurityQuestions(BaseModel):
    username: str
    questions: List[Dict[str, str]]  # [{question_id: int, answer: str}, ...]

class VerifyResetRequest(BaseModel):
    username: str
    security_answers: List[str]
    new_password: str

class VerifyResetResponse(BaseModel):
    success: bool
    message: Optional[str] = None

# Identity schemas
class CreateIdentityRequest(BaseModel):
    username: str

class CreateIdentityResponse(BaseModel):
    error_code: int
    nickname: Optional[str] = None
    message: Optional[str] = None

class DeleteIdentityRequest(BaseModel):
    username: str
    nickname: str

class DeleteIdentityResponse(BaseModel):
    error_code: int
    msg: str

class TokenPair(BaseModel):
    access: str
    refresh: str
    token_type: str

class AccessToken(BaseModel):
    access: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UpdateIdentityRequest(BaseModel):
    username: str
    identity: str  # The nickname to switch to

class UpdateIdentityResponse(BaseModel):
    error_code: int
    message: Optional[str] = None

class CreateFirstIdentityRequest(BaseModel):
    username: str

class CreateFirstIdentityResponse(BaseModel):
    error_code: int
    message: Optional[str] = None
    nickname: Optional[str] = None

class GetTokenRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh: str

error_codes = {
    0: "Success",
    1: "Username already exists",
    2: "User not found",
    3: "Incorrect password",
    4: "Invalid CAPTCHA",
    5: "CAPTCHA expired",
    6: "Maximum identities reached",  # for identity limit
    7: "Username/nickname mismatch"   # for delete identity mismatch
}