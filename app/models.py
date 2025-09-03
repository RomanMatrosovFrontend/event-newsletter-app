from sqlalchemy import Column, Integer, String, JSON, Text, DateTime, Table, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import Base

# Таблица для связи многие-ко-многим пользователей и категорий
user_categories = Table(
    'user_categories',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('category', String, primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_subscribed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    mark = Column(String, nullable=True)
    category = Column(String, nullable=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    dates = Column(JSON)
    languages = Column(JSON)
    age_restriction = Column(String, nullable=True)
    city = Column(String, nullable=True)
    url = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NewsletterLog(Base):
    __tablename__ = "newsletter_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    total_users = Column(Integer)
    successful_sends = Column(Integer)
    failed_sends = Column(Integer)
    duration_seconds = Column(Float)
    
    schedule_id = Column(Integer, ForeignKey('newsletter_schedules.id'), nullable=True)
    schedule = relationship("NewsletterSchedule", back_populates="logs")
    
class NewsletterSchedule(Base):
    __tablename__ = "newsletter_schedules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_ids = Column(JSON, nullable=True)  # ID пользователей или null для всех
    schedule_config = Column(JSON, nullable=False, default={})  # Всё расписание здесь
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    admin_timezone = Column(String, nullable=True, default="UTC")
    logs = relationship("NewsletterLog", back_populates="schedule")



class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
