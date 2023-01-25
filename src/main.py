import json
import logging.config

import uvicorn

from config.server import create_app
from users.router import user_router
from posts.router import post_router

from config.db import engine, Base


Base.metadata.create_all(bind=engine)


app = create_app()
celery = app.celery_app
celery.conf.imports = ['posts.tasks']

config_file = open('./config/logging_config.json')
logging.config.dictConfig(json.load(config_file))

app.include_router(user_router, tags=['users'], prefix='/api/users')
app.include_router(post_router, tags=['posts'], prefix='/api/posts')

# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=8000)
