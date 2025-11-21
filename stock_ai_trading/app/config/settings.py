"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Stock AI Trading System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/stock_trading"
    DATABASE_ECHO: bool = False
    
    # Database Connection (for migrations)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "stock_trading"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Tushare Configuration
    TUSHARE_TOKEN: Optional[str] = None
    
    # Stock Data API
    STOCK_API_KEY: Optional[str] = None
    STOCK_API_BASE_URL: str = "https://api.example.com"
    
    # Trading Configuration
    MAX_POSITION_SIZE: float = 100000.0  # Maximum position size in CNY
    RISK_TOLERANCE: float = 0.02  # 2% risk tolerance
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 允许额外的字段

# Global settings instance
settings = Settings()