import logging

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from config.db import Base

logger = logging.getLogger('app.db.models')


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String)

    post = relationship("Post", backref="user", passive_deletes=True)
    like = relationship('Likes', backref='author', passive_deletes=True)
    dislike = relationship('Dislikes', backref='author', passive_deletes=True)
