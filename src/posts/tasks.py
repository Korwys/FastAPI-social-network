import logging

from celery import shared_task
from sqlalchemy import and_
from starlette.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from posts.models import Likes, Dislikes
from config.db import SessionLocal as db
from config.base import settings
from config.base import manager

redis = manager.redis

logger = logging.getLogger('app.posts.tasks')


@shared_task(bind=True)
def update_redis(self) -> None:
    """Таска создается в случае если редис упал и запись лайков идет напрямую в бд.
    Когда редис поднимется, кэш будет очищен."""
    try:
        redis.flushdb()
    except RedisError as err:
        raise self.retry(exc=err, max_retries=5, countdown=5)


@shared_task(name='update_db')
def update_db() -> None:
    """Запускается раз в сутки и синхронизирует данные по лайкам/дизлайкам с основной бд"""
    all_keys = get_all_keys_from_cache()
    posts_for_update = get_posts_for_update(all_keys=all_keys)
    update_post_with_like(posts_for_update=posts_for_update)
    update_post_dislike(posts_for_update=posts_for_update)
    logger.info('DB UPDATED')


def get_all_keys_from_cache() -> list:
    """Возвращает список всех ключей из кэша"""
    status = None
    redis_curs = 0
    all_kyes_from_cache = []
    while status is None:
        redis_list = redis.scan(redis_curs)
        if redis_list[0] != 0:
            all_kyes_from_cache += redis_list[1]
            redis_curs = redis_list[0]
        else:
            all_kyes_from_cache += redis_list[1]
            status = True
    if len(all_kyes_from_cache) == 0:
        return JSONResponse(status_code=201, content={'msg': 'No posts in cache'})
    else:
        return all_kyes_from_cache


def get_posts_for_update(all_keys: list) -> dict:
    """Возвращает словарь. Ключи - айдишники тех постов, что нужно обновить в БД.
    Логика обновления - если текущий TLL записи в кэше больше разницы (текущий - дневной),
    то пост добавляется для обновления."""
    posts_for_update = {}
    for item in all_keys:
        timer = redis.ttl(item)
        if timer > settings.TTL - settings.DAY_SECONDS:
            request_post = redis.hgetall(item)
            check_for_like_users = request_post['like_user'].split(':')
            check_for_dislike_users = request_post['dislike_user'].split(':')

            if len(check_for_like_users) == 1 and not check_for_like_users[0].isdigit():
                check_for_like_users.remove("")

            if len(check_for_dislike_users) == 1 and not check_for_dislike_users[0].isdigit():
                check_for_dislike_users.remove("")

            posts_for_update[item] = {'like_user': list(map(int, check_for_like_users)),
                                      'dislike_user': list(map(int, check_for_dislike_users))}
        else:
            continue
    return posts_for_update


def update_post_with_like(posts_for_update: dict) -> None:
    """Вычисляет пересечение user.id  поста межу кэшем и бд.
    Добавляет в бд тех кто есть в кэше, но нет в бд, удаляет тех кто есть в бд, но нет в кэше"""
    for post_id in posts_for_update:
        db_likes = db.query(Likes).where(Likes.post_id == post_id).all()
        list_of_likes_users_from_db = [i.user for i in db_likes]
        like_list_for_delete = list(set(list_of_likes_users_from_db) - set(posts_for_update[post_id]['like_user']))
        like_list_for_add = list(set(posts_for_update[post_id]['like_user']) - set(list_of_likes_users_from_db))
        try:
            if len(like_list_for_delete) != 0:
                db.query(Likes).where(
                    and_(Likes.user.in_(like_list_for_delete), Likes.post_id == int(post_id))).delete()
                db.commit()

            if len(like_list_for_add) != 0:
                db.execute(
                    Likes.__table__.insert(),
                    [{"post_id": int(post_id), "user": user} for user in like_list_for_add]
                )
                db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)


def update_post_dislike(posts_for_update: dict) -> None:
    """Вычисляет пересечение user.id  поста межу кэшем и бд.
    Добавляет в бд тех кто есть в кэше, но нет в бд, удаляет тех кто есть в бд, но нет в кэше"""
    for post_id in posts_for_update:
        db_dislikes = db.query(Dislikes).where(Dislikes.post_id == post_id).all()
        list_of_dislikes_users_from_db = [i.user for i in db_dislikes]
        dislike_list_for_delete = list(
            set(list_of_dislikes_users_from_db) - set(posts_for_update[post_id]['dislike_user']))
        dislike_list_for_add = list(
            set(posts_for_update[post_id]['dislike_user']) - set(list_of_dislikes_users_from_db))
        try:
            if len(dislike_list_for_delete) != 0:
                db.query(Dislikes).where(
                    and_(Dislikes.user.in_(dislike_list_for_delete), Dislikes.post_id == int(post_id))).delete()
                db.commit()

            if len(dislike_list_for_add) != 0:
                db.execute(
                    Dislikes.__table__.insert(),
                    [{"post_id": post_id, "user": user} for user in dislike_list_for_add]
                )
                db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)
