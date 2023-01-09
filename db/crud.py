import logging
from typing import Dict, Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError, IntegrityError

from services.auth import create_hashed_user_password
from db.models import User, Post, Likes, Dislikes
from db.schemas import UserCreate, PostCreate, PostUpdate, UserInDB

logger = logging.getLogger('app.db.crud')


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


def add_new_post_in_db(db: Session, obj_in: PostCreate, user) -> Post:
	obj_in = obj_in.dict()
	obj_in['author'] = user.id
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
			db.delete(post)
			db.commit()
			return post
		except SQLAlchemyError as err:
			logger.exception(err)
	else:
		raise HTTPException(status_code=400, detail=f"Пост с таким Id отсутсвует или нет прав на удаление")


def fetch_one_post(db: Session, post_id: int) -> Post:
	try:
		post = db.query(Post).filter(Post.id == post_id).first()
		if post:
			return post
		else:
			raise HTTPException(status_code=400, detail=f"Пост с таким Id отсутсвует")
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
	if like and like.user == user.id:
		try:
			db.delete(like)
			db.commit()
		except SQLAlchemyError as err:
			logger.exception(err)
	else:
		obj_in = {"post_id": post_id, "user": user.id}
		db_obj = model(**obj_in)
		try:
			db.add(db_obj)
			db.commit()
		except SQLAlchemyError as err:
			logger.exception(err)
