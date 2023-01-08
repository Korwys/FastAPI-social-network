import json
import logging.config

import uvicorn
from fastapi import FastAPI

from api import users, posts, likes_dislikes
from db import models
from db.config import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

config_file = open('./services/logging_config.json')
logging.config.dictConfig(json.load(config_file))

app.include_router(users.router, tags=['users'], prefix='/api/users')
app.include_router(posts.router, tags=['posts'], prefix='/api/posts')
app.include_router(likes_dislikes.router, tags=['likes/dislikes'])

if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=8000)
