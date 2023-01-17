import json
import logging.config

import uvicorn
from fastapi import FastAPI

from api import users, posts
from db import models
from db.config import engine

models.Base.metadata.create_all(bind=engine)

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
]
app = FastAPI(openapi_tags=tags_metadata)

config_file = open('./services/logging_config.json')
logging.config.dictConfig(json.load(config_file))

app.include_router(users.router, tags=['users'], prefix='/api/users')
app.include_router(posts.router, tags=['posts'], prefix='/api/posts')

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
