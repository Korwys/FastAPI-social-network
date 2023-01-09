import logging

from sqlalchemy import Column, ForeignKey, Integer, String, DDL, event, update, text
from sqlalchemy.orm import relationship, validates

from .config import Base

logger = logging.getLogger('app.db.models')


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True, nullable=False)
	email = Column(String, unique=True, nullable=False)
	hashed_password = Column(String)


class Post(Base):
	__tablename__ = "posts"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String, nullable=False)
	description = Column(String, nullable=False)
	likes = Column(Integer, nullable=True)
	dislikes = Column(Integer, nullable=True)
	author = Column(Integer, ForeignKey("users.id"))


class Dislikes(Base):
	__tablename__ = "dislikes"

	id = Column(Integer, primary_key=True, index=True)
	post_id = Column(Integer, ForeignKey('posts.id'))
	user = Column(Integer, ForeignKey('users.id'), unique=True)


class Likes(Base):
	__tablename__ = "likes"

	id = Column(Integer, primary_key=True, index=True)
	post_id = Column(Integer, ForeignKey('posts.id'))
	user = Column(Integer, ForeignKey('users.id'), unique=True)


@event.listens_for(Likes, "after_insert")
def plus_like(mapper, connection, target):
	try:
		post = Post
		connection.execute(update(post).where(Post.id == target.post_id).values(likes=post.likes + 1))
	except Exception as err:
		logger.exception(err)


@event.listens_for(Likes, "before_delete")
def minus_like(mapper, connection, target):
	try:
		post = Post
		connection.execute(update(post).where(Post.id == target.post_id).values(likes=post.likes + 1))
	except Exception as err:
		logger.exception(err)


@event.listens_for(Dislikes, "after_insert")
def plus_dislike(mapper, connection, target):
	try:
		post = Post
		connection.execute(update(post).where(Post.id == target.post_id).values(dislikes=post.dislikes + 1))
	except Exception as err:
		logger.exception(err)


@event.listens_for(Dislikes, "before_delete")
def minus_dislike(mapper, connection, target):
	try:
		post = Post
		connection.execute(update(post).where(Post.id == target.post_id).values(dislikes=post.dislikes + 1))
	except Exception as err:
		logger.exception(err)
