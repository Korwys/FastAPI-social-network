import logging
from typing import Dict, Any

import redis as redis
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from services.auth import create_hashed_user_password
from db.models import User, Post
from db.schemas import UserCreate, PostCreate, PostUpdate, UserInDB

logger = logging.getLogger('app.db.crud')

redis = redis.Redis(host='localhost', port=6379, db=0)


def add_new_user_in_db(db: Session, obj_in: UserCreate) -> User:
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


def fetch_user_from_db(db: Session, data):
	return db.query(User).where(User.username == data.username)


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
			logger.error(msg=err)

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
	like = db.query(model).filter(and_(model.post_id == post_id, model.user == user.id)).first()
	if like:
		redis_cache_change_values(key=post_id, status='Dec', table=model.__tablename__)
		try:
			db.delete(like)
			db.commit()
		except SQLAlchemyError as err:
			logger.exception(err)
	else:
		redis_cache_change_values(key=post_id, status='Inc', table=model.__tablename__)
		obj_in = {"post_id": post_id, "user": user.id}
		db_obj = model(**obj_in)
		try:
			db.add(db_obj)
			db.commit()
		except SQLAlchemyError as err:
			logger.exception(err)


def check_post_author(db: Session, post_id: int, user: UserInDB) -> bool:
	owner = db.query(Post).filter(and_(Post.author == user.id, Post.id == post_id)).first()
	if owner:
		return False
	else:
		return True


def redis_cache_change_values(key: int, status=None, table=None) -> None:
	if table == 'likes' and status == 'Inc':
		increment_likes_or_dislikes_in_redis_cache(key, table, status)
	elif table == 'likes' and status == 'Dec':
		decrement_likes_or_dislikes_in_redis_cache(key, table, status)

	if table == 'dislikes' and status == 'Inc':
		increment_likes_or_dislikes_in_redis_cache(key, table, status)
	elif table == 'dislikes' and status == 'Dec':
		decrement_likes_or_dislikes_in_redis_cache(key, table, status)


def decrement_likes_or_dislikes_in_redis_cache(key: int, table: str, status: str) -> None:
	try:
		response = redis.hgetall(key)
		if response and status == 'Inc':
			cache_value = redis.hget(key, table.encode())
			new_value = int(cache_value.decode()) + 1
			redis.hset(key, table, new_value)
		elif response and status == 'Dec':
			cache_value = redis.hget(key, table.encode())
			if int(cache_value.decode()) > 0:
				new_value = int(cache_value.decode()) - 1
				redis.hset(key, table, new_value)
			else:
				redis.hset(key, table, 0)
		else:
			redis.hset(key, mapping={'likes': 0, 'dislikes': 0})
	except Exception as err:
		logger.exception(err)


def increment_likes_or_dislikes_in_redis_cache(key: int, table: str, status: str) -> None:
	try:
		response = redis.hgetall(key)
		if response and status == 'Inc':
			cache_value = redis.hget(key, table.encode())
			new_value = int(cache_value.decode()) + 1
			redis.hset(key, table, new_value)
		elif response and status == 'Dec':
			cache_value = redis.hget(key, table.encode())
			if int(cache_value.decode()) > 0:
				new_value = int(cache_value.decode()) - 1
				redis.hset(key, table, new_value)
			else:
				redis.hset(key, table, 0)
		else:
			redis.hset(key, mapping={'likes': 0, 'dislikes': 0})
			redis.hset(key, table, 1)
	except Exception as err:
		logger.exception(err)
