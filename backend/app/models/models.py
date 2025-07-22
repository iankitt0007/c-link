from pydantic import BaseModel, EmailStr, constr
from enum import Enum

# Role enum
class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

# Pydantic models for API validation
class UserSignup(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

class UserSignin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    role: Role
    created_at: str
    email_confirmed: bool
    last_sign_in: str = None

class UserRoleUpdate(BaseModel):
    role: Role

# Response models
class AuthResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str = None
    user: UserProfile

class MessageResponse(BaseModel):
    message: str

class UsersListResponse(BaseModel):
    users: list[UserProfile]
    count: int