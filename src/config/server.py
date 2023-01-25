from fastapi import FastAPI

from config.celery_utils import create_celery


def create_app() -> FastAPI:
    app = FastAPI()
    app.celery_app = create_celery()
    return app
