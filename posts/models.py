from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from config.db import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    author = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    like = relationship("Likes", backref="post", passive_deletes=True)
    dislike = relationship("Dislikes", backref="post", passive_deletes=True)


class Dislikes(Base):
    __tablename__ = "dislikes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)


class Likes(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
