from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    
    openai_api_key: str
    serpapi_api_key: str
    database_url: str = "sqlite:///./seo_engine.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

