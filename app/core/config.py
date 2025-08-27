import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Postmark configuration
    POSTMARK_API_TOKEN: str = os.getenv("POSTMARK_API_TOKEN", "your-api-token-here")
    POSTMARK_SENDER_EMAIL: str = os.getenv("POSTMARK_SENDER_EMAIL", "noreply@my-events.com")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

settings = Settings()