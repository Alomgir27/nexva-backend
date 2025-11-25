import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nexva - AI Chatbot API"
    VERSION: str = "1.0"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = "postgresql://admin:admin123@localhost:5432/products_db"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    CORS_ORIGINS: list = ["*"]
    
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")
    USE_R2_STORAGE: bool = os.getenv("USE_R2_STORAGE", "false").lower() == "true"
    
    class Config:
        case_sensitive = True

settings = Settings()

