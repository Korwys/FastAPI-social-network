import logging
from typing import Dict, Any

from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError
from sqlalchemy import and_, text, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from posts.models import Post, Likes, Dislikes
from posts.schemas import PostCreate, PostUpdate
from users.models import User
from users.schemas import UserInDB
from config.base import manager

redis = manager.redis
logger = logging.getLogger('app.db.crud')


def add_new_post_in_db(db: Session, obj_in: PostCreate, user: User) -> Post:
    """Добавляет запись о новом посте"""
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
    """Апдейтит запись в бд у указанного поста. Если пост есть в кэше, то апдейтит данные и там"""
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
    """Удаляет запись из бд и кэша"""
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


def fetch_one_post(db: Session, post_id: int) -> dict | JSONResponse:
    """Забирает и возвращает пост из бд по указанному айди"""
    post_values = select_common_post_data(post_id=post_id, db=db)
    like_user = select_all_users_with_likes(post_id=post_id, db=db)
    dislike_user = select_all_users_with_dislikes(post_id=post_id, db=db)

    if post_values:
        pid, title, desc, author, dislikes, likes = list(post_values)
        post = {"id": pid,
                'title': title,
                'description': desc,
                'author': author,
                'likes': likes,
                'dislikes': dislikes,
                'like_user': like_user,
                'dislike_user': dislike_user}
        return post
    else:
        return JSONResponse(status_code=200, content={'Message': 'Post not exist'})


def check_post_author(db: Session, post_id: int, user: UserInDB) -> bool:
    """Проверка текущего юзера на авторство поста для лайка/дизлайка"""
    owner = db.query(Post).filter(and_(Post.author == user.id, Post.id == post_id)).first()
    if owner:
        return True
    else:
        return False


def select_all_users_with_likes(post_id: int, db: Session) -> str:
    """Возращает строку состоящую из айдишников юзеров, которые поставили лайки,
    если таковых нет, то вернет пустую строку"""
    list_of_users = db.query(Likes.user).filter(Likes.post_id == post_id).all()
    ended_list = []
    for user_id in list_of_users:
        ended_list.append(str(user_id[0]))
    if len(ended_list) > 0:
        return ':'.join(ended_list)
    else:
        return ''


def select_all_users_with_dislikes(post_id: int, db: Session) -> str:
    """Возращает строку состоящую из айдишников юзеров, которые поставили дизлайки,
    если таковых нет, то вернет пустую строку"""
    list_of_users = db.query(Dislikes.user).filter(Dislikes.post_id == post_id).all()
    ended_list = []
    for user_id in list_of_users:
        ended_list.append(str(user_id[0]))
    if len(ended_list) > 0:
        return ':'.join(ended_list)
    else:
        return ''


def select_common_post_data(post_id: int, db: Session) -> list:
    """Возвращает объединенные данные по посту со всех таблиц (Post,Likes,Dislikes)"""
    query = text(f"""
            SELECT posts.id as post_id, posts.title as title, posts.description, posts.author,
            (SELECT COUNT(id) FROM dislikes WHERE post_id ={post_id}) as dislikes,
            (SELECT count(id) FROM likes WHERE post_id={post_id}) as likes
            from posts
            where posts.id = {post_id}
            group by posts.id""")
    statement = db.execute(query)
    for i in statement:
        return i


def change_emotions_in_db(post_id: int, db: Session, user: UserInDB, model: Likes | Dislikes) -> JSONResponse:
    """ При падении редиса добавляет/удаляет данные напрямую в бд о лайках/дизлайках.
    Возвращает код 201 и  количество лайков/дизлайков после изменения"""
    db_emotions = db.query(model).where(model.post_id == post_id).all()
    list_of_emotions_users_from_db = [i.user for i in db_emotions]
    if user.id not in list_of_emotions_users_from_db:
        obj_in = {'post_id': post_id, 'user': user.id}
        db_obj = model(**obj_in)
        try:
            db.add(db_obj)
            db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)
        emotions_value = db.query(model).filter(model.post_id == post_id).count()
        return JSONResponse(status_code=201, content={model.__tablename__: emotions_value})
    else:
        try:
            obj = delete(model).where(and_(model.post_id == post_id, model.user == user.id))
            db.execute(obj)
            db.commit()
        except SQLAlchemyError as err:
            logger.exception(err)
        em_value = db.query(model).filter(model.post_id == post_id).count()
        return JSONResponse(status_code=201, content={model.__tablename__: em_value})
