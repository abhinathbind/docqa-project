from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "DocQA"
    DEBUG: bool = False

    # MongoDB
    MONGODB_URL: str = "mongodb://mongo:27017"
    MONGODB_DB: str = "docqa"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    WHISPER_MODEL: str = "whisper-1"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    
    ALLOWED_ORIGINS: List[str] = [ "http://localhost:3000", 
      "http://localhost:80", "https://docqa-project.netlify.app"]
    

    # File upload
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIR: str = "/tmp/uploads"

    class Config:
        env_file = ".env"

settings = Settings()
