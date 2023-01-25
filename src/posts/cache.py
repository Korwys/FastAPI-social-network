import datetime
import logging

from fastapi import HTTPException
from redis.exceptions import RedisError, ConnectionError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from posts.models import Likes, Dislikes
from posts.services import fetch_one_post, change_emotions_in_db
from config.base import settings
from users.schemas import UserInDB
from config.base import manager

redis = manager.redis
logger = logging.getLogger('app.services.cache')


def fetch_post_from_cache(db: Session, post_id: int) -> dict | JSONResponse:
    """Возвращает запись поста из кэша, а в случае ее отсутствия берет ее из бд, добавляет в кэш(назначает ttl 168 часов)
     и возвращает. Если поста по указанному айдишнику нет, то вернет код 400 с описанием ошибки
     Если кэш недоступен, то вернет пост из бд."""
    try:
        response = redis.hgetall(post_id)
        if response:
            return response
        else:
            post_from_db = fetch_one_post(db=db, post_id=post_id)
            if isinstance(post_from_db, dict):
                redis.hset(post_from_db['id'], mapping=post_from_db)
                ttl = datetime.timedelta(hours=settings.TTL)
                redis.expire(post_from_db['id'], time=ttl)
                return post_from_db
            else:
                return JSONResponse(status_code=200, content={'Message': 'Post not exist'})
    except ConnectionError as err:
        logger.error(err)
        return fetch_one_post(db=db, post_id=post_id)


def fetch_posts_from_cache(quantity: int, db: Session) -> list:
    """Возвращает список постов из кэша"""
    posts_for_response = []
    for i in range(1, quantity + 1):
        post = fetch_post_from_cache(db=db, post_id=i)
        try:
            if 'id' not in post.keys():
                continue
        except AttributeError as err:
            continue
        else:
            posts_for_response.append(post)
    return posts_for_response


def change_count_of_users_emotions(db: Session, user: UserInDB, post_id: int, users: str,
                                   model: Likes | Dislikes) -> JSONResponse:
    """Инкрементирует/декрементирует счетчик лайков в кэше.
     Если поста нет в кэше то берет данные из бд"""
    try:
        new_req = redis.hgetall(post_id)
        if not new_req:
            single_post = fetch_one_post(db=db, post_id=post_id)
            if not single_post:
                raise HTTPException(status_code=400, detail='Post not exists')

            redis.hset(post_id, mapping=single_post)
            ttl = datetime.timedelta(hours=720)
            redis.expire(post_id, time=ttl)

        request_after_update = redis.hget(post_id, users)
        users_list = request_after_update.split(':')
        table = model.__tablename__
        if str(user.id) in users_list:
            users_list.remove(str(user.id))
            table_data = ':'.join(users_list)
            redis.hincrby(post_id, table, -1)
            redis.hset(post_id, users, table_data)
            return JSONResponse(status_code=201, content={table: redis.hget(post_id, table)})
        else:
            users_list.append(str(user.id))
            if "" in users_list:
                users_list.remove("")
            table_data_users = ':'.join(users_list)
            redis.hincrby(post_id, table, 1)
            redis.hset(post_id, users, table_data_users)
            return JSONResponse(status_code=201, content={table: redis.hget(post_id, table)})
    except RedisError as err:
        logger.error(err)
        return change_emotions_in_db(post_id=post_id, db=db, user=user, model=model)
