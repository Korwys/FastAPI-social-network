import datetime
import logging

import redis as redis
from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from db.crud import fetch_one_post
from db.models import Likes
from db.schemas import UserInDB

redis = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True, db=0)

logger = logging.getLogger('app.services.cache')


def fetch_post_from_cache(db: Session, post_id: int) -> dict | JSONResponse:
    """Возвращает запись поста из кэша, а в случае ее отсутствия берет ее из бд, добавляет в кэш(назначает ttl 720 часов)
     и возвращает. Если поста по указанному айдишнику нет, то вернет код 400 с описанием ошибки"""
    response = redis.hgetall(post_id)
    if response:
        return response
    else:
        post_from_db = fetch_one_post(db=db, post_id=post_id)
        if post_from_db:
            post_from_db['like_user'] = ''
            post_from_db['dislike_user'] = ''
            try:
                redis.hset(post_from_db['id'], mapping=post_from_db)
                ttl = datetime.timedelta(hours=720)
                redis.expire(post_from_db['id'], time=ttl)
            except RedisError as err:
                logger.error(err)

            return post_from_db
        else:
            return JSONResponse(status_code=400, content={'msg': 'Post not exist'})


def fetch_posts_from_cache(quantity: int, db: Session) -> dict:
    """Возвращает список постов из кэша"""
    posts_for_response = []
    for i in range(1, quantity + 1):
        post = fetch_post_from_cache(db=db, post_id=i)
        if type(post) != dict:
            continue
        else:
            posts_for_response.append(post)
    return posts_for_response


def change_count_of_users_emotions(db: Session, user: UserInDB, post_id: int, table: str, users: str) -> JSONResponse:
    """Инкрементирует или декрементирует счетчик лайков в основном кэше"""
    new_req = redis.hgetall(post_id)
    if not new_req:
        single_post = fetch_one_post(db=db, post_id=post_id)
        if not single_post:
            raise HTTPException(status_code=400, detail='Post not exists')

        likes_users = db.query(Likes).filter(Likes.post_id == post_id).all()
        dislikes_users = db.query(Likes).filter(Likes.post_id == post_id).all()
        dis_users = [str(i.id) for i in dislikes_users]
        like_users = [str(i.id) for i in likes_users]
        single_post['dislike_user'] = ':'.join(dis_users)
        single_post['like_user'] = ':'.join(like_users)

        redis.hset(post_id, mapping=single_post)

        ttl = datetime.timedelta(hours=720)
        redis.expire(post_id, time=ttl)

    request_after_update = redis.hget(post_id, users)
    users_list = request_after_update.split(':')
    if str(user.id) in users_list:
        users_list.remove(str(user.id))
        table_data = ':'.join(users_list)
        redis.hincrby(post_id, table, -1)
        redis.hset(post_id, users, table_data)
        return JSONResponse(status_code=201, content={'msg': 'Change your emotion'})
    else:
        users_list.append(str(user.id))
        table_data_users = ':'.join(users_list)
        redis.hincrby(post_id, table, 1)
        redis.hset(post_id, users, table_data_users)
        return JSONResponse(status_code=201, content={'msg': 'Change your emotion'})
