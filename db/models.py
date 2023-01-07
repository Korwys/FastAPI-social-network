from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .config import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True)
	email = Column(String, unique=True, index=True)
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
	post_owner = Column(Integer, ForeignKey('posts.author'))
	dislike_author = Column(Integer, ForeignKey('users.id'), unique=True)


class Likes(Base):
	__tablename__ = "likes"

	id = Column(Integer, primary_key=True, index=True)
	post_id = Column(Integer, ForeignKey('posts.id'))
	post_owner = Column(Integer, ForeignKey('posts.author'))
	like_author = Column(Integer, ForeignKey('users.id'), unique=True)
