import os
import secrets

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost/page_analyzer"
    )
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    MAX_URL_LENGTH: int = 255
    MAX_TEXT_LENGTH: int = 200
