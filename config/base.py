import pathlib
from pydantic import BaseSettings


class AppSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/social.db"
    REDIS_PORT: int = '6379'
    HUNTER_URL: str = "https://api.hunter.io/v2/email-verifier"
    HUNTER_API_KEY: str = "f721334b041135353462ce773fe53739a23043ba"
    CLEARBIT_URL: str = "https://risk.clearbit.com/v1/calculate"
    CLEARBIT_API_KEY: str = "sk_cf919e93d26cf9ab668c62f379af6d9b"
    SECRET: str = "d021e6e23e40df657eb4454203e1ca"
    ALGORITHM: str = "HS256"
    ACCESS: int = 30

    CELERY_BROKER_URL: str = "redis://127.0.0.1:6380/1"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6380/1"

    TTL: int = 168  # Дефолтное значение в редисе (1 неделя)
    DAY_SECONDS: int = 86400

    CELERY_BEAT_SCHEDULE: dict = {
        "update_db": {
            "task": "update_db",
            "schedule": 86400.0,  # Указано в секундах (1 день)
        },
    }


settings = AppSettings()
