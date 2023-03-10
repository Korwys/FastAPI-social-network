import pathlib
import redis

from pydantic import BaseSettings, Field


class AppSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/social.db"
    REDIS_PORT: int = '6379'
    HUNTER_URL: str = "https://api.hunter.io/v2/email-verifier"
    HUNTER_API_KEY: str = Field(..., env='HUNTER_API_KEY')
    CLEARBIT_URL: str = "https://risk.clearbit.com/v1/calculate"
    CLEARBIT_API_KEY: str = Field(..., env='CLEARBIT_API_KEY')
    SECRET: str = Field(..., env='SECRET')
    ALGORITHM: str = "HS256"
    ACCESS: int = 30

    TTL: int = 168  # Дефолтное значение в редисе (1 неделя)
    DAY_SECONDS: int = 86400

    CELERY_BROKER_URL: str = "redis://redis-celery:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis-celery:6379/1"
    CELERY_BEAT_SCHEDULE: dict = {
        "update_db": {
            "task": "update_db",
            "schedule": 86400.0,  # Указано в секундах (1 день)
        },
    }


settings = AppSettings()


class ConnectionManager:
    redis = redis.Redis(host='redis-cache', port=6380, charset="utf-8", decode_responses=True, db=0)


manager = ConnectionManager()
