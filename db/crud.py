import logging
from typing import Dict, Any

import redis as redis
from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError
from sqlalchemy import and_, or_, select, text, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from services.auth import create_hashed_user_password
from db.models import User, Post
from db.schemas import UserCreate, PostCreate, PostUpdate, UserInDB
from services.validators import clearbit_new_user_score_checker, hunter_user_email_checker

logger = logging.getLogger('app.db.crud')

redis = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True, db=0)


async def add_new_user_in_db(db: Session, obj_in: UserCreate, request: Request) -> User:
    clearbit_user_score = await clearbit_new_user_score_checker(user_data=obj_in, request=request)
    hunter_status_score = await hunter_user_email_checker(user_data=obj_in)
    user_in_db = user_uniqueness_check(db=db, user_data=obj_in)

    if not user_in_db and clearbit_user_score != 'high' and not hunter_status_score:
        new_data = obj_in.dict()
        new_data.pop('password')
        db_obj = User(**new_data)
        db_obj.hashed_password = create_hashed_user_password(obj_in.password)
        try:
            db.add(db_obj)
            db.commit()
            return db_obj
        except SQLAlchemyError as err:
            logger.exception(err)
    elif clearbit_user_score == 'high':
        print('Please enter the captcha and confirm your email')
    elif hunter_status_score:
        raise HTTPException(status_code=400, detail='Email is invalid')

    if user_in_db.username == obj_in.username:
        raise HTTPException(status_code=400, detail='Username already exists')

    if user_in_db.email == obj_in.email:
        raise HTTPException(status_code=400, detail='Email already exists')


def user_uniqueness_check(db: Session, user_data: UserCreate):
    try:
        user_query = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
        user_db_request = db.execute(user_query)
        return user_db_request.scalar()
    except SQLAlchemyError as err:
        logger.exception(err)


def fetch_user_from_db(db: Session, data):
    try:
        return db.query(User).where(User.username == data.username).first()
    except SQLAlchemyError as err:
        logger.exception(err)


def add_new_post_in_db(db: Session, obj_in: PostCreate, user: User) -> Post:
    obj_in = obj_in.dict()
    obj_in['author'] = user.id
    db_obj = Post(**obj_in)
    try:
        db.add(db_obj)
        db.commit()
        return db_obj
    except SQLAlchemyError as err:
        logger.exception(err)


def update_post(db: Session, post_id: int, obj_in: PostUpdate | Dict[str, Any]) -> Post:
    db_obj = db.query(Post).filter(Post.id == post_id).first()
    obj_data = jsonable_encoder(db_obj)

    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)

    for field in obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    except SQLAlchemyError as err:
        logger.exception(err)

    try:
        if redis.hgetall(post_id):
            redis.hset(post_id, mapping=update_data)
    except RedisError as err:
        logger.error(err)

    return db_obj


def remove_post_from_db(db: Session, post_id: int) -> JSONResponse:
    try:
        obj = delete(Post).where(Post.id == post_id)
        db.execute(obj)
        db.commit()
    except SQLAlchemyError as err:
        logger.exception(err)

    try:
        redis.delete(post_id)
    except RedisError as err:
        logger.exception(err)

    return JSONResponse(status_code=200, content={'Message': 'Post deleted'})


def fetch_one_post(db: Session, post_id: int) -> Post:
    try:
        query = text(f"""
                    SELECT posts.id as post_id, posts.title as title, posts.description, posts.author,
                    (SELECT COUNT(id) FROM dislikes WHERE post_id ={post_id}) as dislikes,
                    (SELECT count(id) FROM likes WHERE post_id={post_id}) as likes
                    from posts
                    where posts.id = {post_id}
                    group by posts.id""")
        statement = db.execute(query)
        post_values = [row for row in statement]
        if post_values:
            pid, title, desc, author, dislikes, likes = post_values[0]
            post = {"id": pid,
                    'title': title,
                    'description': desc,
                    'author': author,
                    'likes': likes,
                    'dislikes': dislikes}
            return post
    except SQLAlchemyError as err:
        logger.exception(err)


def check_post_author(db: Session, post_id: int, user: UserInDB) -> bool:
    """Проверка текущего юзера на авторство поста для лайка/дизлайка"""
    owner = db.query(Post).filter(and_(Post.author == user.id, Post.id == post_id)).first()
    if owner:
        return False
    else:
        return True
