from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .config import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True)
	email = Column(String, unique=True, index=True)
	hashed_password = Column(String)

	items = relationship("Item", back_populates="owner")


class Item(Base):
	__tablename__ = "posts"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String, nullable=False)
	description = Column(String, nullable=False)
	likes = Column(Integer, nullable=True)
	dislikes = Column(Integer, nullable=True)
	owner_id = Column(Integer, ForeignKey("users.id"))

	owner = relationship("User", back_populates="items")
