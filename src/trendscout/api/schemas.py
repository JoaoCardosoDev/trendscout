from typing import Optional, Any, Dict, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Base User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Task Schemas
class TaskBase(BaseModel):
    agent_type: str = Field(..., pattern="^(trend_analyzer|content_generator|scheduler)$")
    input_data: Dict[str, Any]

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed)$")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TaskInDB(TaskBase):
    id: int
    task_id: str
    status: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

# Response Schemas
class Message(BaseModel):
    message: str

class TaskList(BaseModel):
    tasks: List[TaskInDB]
    total: int

class UserList(BaseModel):
    users: List[UserInDB]
    total: int
