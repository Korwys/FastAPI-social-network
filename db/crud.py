import logging
from typing import Dict, Any

import redis as redis
from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session1
from sqlalchemy.exc import SQLAlchemyError

from services.auth import create_hashed_user_password
from db.models import User, Post
from db.schemas import UserCreate, PostCreate, PostUpdate, UserInDB
from services.validators import clearbit_new_user_score_checker, hunter_user_email_checker

logger = logging.getLogger('app.db.crud')

redis = redis.Redis(host='localhost', port=6379, db=0)


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
    user_query = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    user_db_request = db.execute(user_query)
    return user_db_request.scalar()


def fetch_user_from_db(db: Session, data):
    try:
        return db.query(User).where(User.username == data.username).first()
    except SQLAlchemyError as err:
        logger.exception(err)


def add_new_post_in_db(db: Session, obj_in: PostCreate, user) -> Post:
    obj_in = obj_in.dict()
    obj_in['author'] = user.id
    obj_in['likes'] = 0
    obj_in['dislikes'] = 0
    db_obj = Post(**obj_in)
    try:
        db.add(db_obj)
        db.commit()
        return db_obj
    except SQLAlchemyError as err:
        logger.exception(err)


def update_post(db: Session, db_obj: Post, obj_in: PostUpdate | Dict[str, Any]) -> Post:
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
        return db_obj
    except SQLAlchemyError as err:
        logger.exception(err)


def remove_post_from_db(db: Session, post_id: int, user: UserInDB) -> Post:
    post = fetch_one_post(db, post_id)

    if post and post.author == user.id:
        try:
            redis.delete(post_id)
        except RedisError as err:
            logger.exception(err)

        try:
            db.delete(post)
            db.commit()
            return post
        except SQLAlchemyError as err:
            logger.exception(err)
    else:
        raise HTTPException(status_code=400,
                            detail=f"Post with ID-{post_id} does not exist OR You don't have permissions on delete")


def fetch_one_post(db: Session, post_id: int) -> Post:
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            return post
        else:
            raise HTTPException(status_code=400, detail=f"Post with ID-{post_id} does not exist")
    except SQLAlchemyError as err:
        logger.exception(err)


def fetch_all_posts_from_db(db: Session, skip: int, limit: int) -> list[Post]:
    try:
        posts = db.query(Post).order_by(Post.id).offset(skip).limit(limit).all()
        return posts
    except SQLAlchemyError as err:
        logger.exception(err)


def change_likes_or_dislikes(db: Session, post_id: int, user: UserInDB, model) -> None:
    """Добавляет либо удаляет поставленные лайки/дизлайки.
    Повторный запрос от одного и того же пользователя удаляет ранее проставленный лайк/дизлайк"""

    like = db.query(model).filter(and_(model.post_id == post_id, model.user == user.id)).first()
    if like:
        routing_redis_cache_changes(key=post_id, status='Dec', table=model.__tablename__)
        try:
            db.delete(like)
            db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)
    else:
        routing_redis_cache_changes(key=post_id, status='Inc', table=model.__tablename__)
        obj_in = {"post_id": post_id, "user": user.id}
        db_obj = model(**obj_in)
        try:
            db.add(db_obj)
            db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)


def check_post_author(db: Session, post_id: int, user: UserInDB) -> bool:
    """Проверка текущего юзера на авторство поста для лайка/дизлайка"""
    owner = db.query(Post).filter(and_(Post.author == user.id, Post.id == post_id)).first()
    if owner:
        return False
    else:
        return True


def routing_redis_cache_changes(key: int, status=None, table=None) -> None:
    """Роутинг логики изменения количества лайков/дизлаков в зависимости от действия юзера
    При повторном обращении к эндпоинту лайк/дизлайк либо добавляется при его отсутствии, в противном случае удаляется"""

    if table == 'likes' and status == 'Inc':
        change_likes_or_dislikes_in_redis_cache(key, table, status)
    elif table == 'likes' and status == 'Dec':
        change_likes_or_dislikes_in_redis_cache(key, table, status)

    if table == 'dislikes' and status == 'Inc':
        change_likes_or_dislikes_in_redis_cache(key, table, status)
    elif table == 'dislikes' and status == 'Dec':
        change_likes_or_dislikes_in_redis_cache(key, table, status)


def change_likes_or_dislikes_in_redis_cache(key: int, table: str, status: str) -> None:
    try:
        response = redis.hgetall(key)
        if response and status == 'Inc':
            redis.hincrby(key, table, 1)
        elif response and status == 'Dec':
            redis.hincrby(key, table, -1)
        else:
            redis.hset(key, mapping={'likes': 0, 'dislikes': 0})
            redis.hset(key, table, 1)
    except RedisError as err:
        logger.exception(err)
