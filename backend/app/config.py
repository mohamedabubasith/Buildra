from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite:///./buildra.db"
    tickets_dir: str = "/tickets"
    docs_dir: str = "/docs"
    opendevin_url: str = "http://localhost:3001"
    encryption_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

TICKETS_DIR = Path(settings.tickets_dir)
DOCS_DIR = Path(settings.docs_dir)

TICKETS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
