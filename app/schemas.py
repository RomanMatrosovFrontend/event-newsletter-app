from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    categories: List[str] = []

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    categories: Optional[List[str]] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EventBase(BaseModel):
    mark: Optional[str] = None
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    text: Optional[str] = None
    photo: Optional[str] = None
    dates: List[str]
    languages: List[str]
    age_restriction: Optional[str] = None
    city: Optional[str] = None
    url: str

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    mark: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    text: Optional[str] = None
    photo: Optional[str] = None
    dates: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    age_restriction: Optional[str] = None
    city: Optional[str] = None
    url: Optional[str] = None

class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscribeRequest(BaseModel):
    email: EmailStr
    categories: List[str]

class SubscribeResponse(BaseModel):
    status: str
    message: Optional[str] = None


class ScheduleBase(BaseModel):
    name: str
    description: Optional[str] = None
    user_ids: Optional[List[int]] = None
    schedule_type: str  # 'cron' | 'date'
    cron_expression: Optional[str] = None
    specific_date: Optional[datetime] = None
    is_active: bool = True

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    user_ids: Optional[List[int]] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    specific_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class Schedule(ScheduleBase):
    id: int
    last_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NewsletterLogBase(BaseModel):
    sent_at: Optional[datetime] = None
    total_users: Optional[int] = None
    successful_sends: Optional[int] = None
    failed_sends: Optional[int] = None
    duration_seconds: Optional[float] = None
    schedule_id: Optional[int] = None

class NewsletterLogCreate(NewsletterLogBase):
    pass

class NewsletterLog(NewsletterLogBase):
    id: int

    class Config:
        from_attributes = True

class AdminUserCreate(BaseModel):
    username: str
    password: str

class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_username: Optional[str] = None  
    new_password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    
class Message(BaseModel):
    message: str
