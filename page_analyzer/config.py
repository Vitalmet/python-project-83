import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost/page_analyzer"
    )
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    MAX_URL_LENGTH: int = 255
    MAX_TEXT_LENGTH: int = 200

    def __init__(self) -> None:
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY must be set in environment variables. "
                "Add SECRET_KEY to your .env file."
            )
