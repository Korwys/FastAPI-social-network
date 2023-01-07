import uvicorn
from fastapi import FastAPI

from api import users
from db import models
from db.config import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router, tags=['users'])

if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=8000)
