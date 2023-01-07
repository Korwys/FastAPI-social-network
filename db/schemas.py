from pydantic import BaseModel, EmailStr


class PostBase(BaseModel):
	title: str
	description: str


class PostCreate(PostBase):
	...


class PostUpdate(PostBase):
	title: str | None
	description: str | None


class PostInDB(PostBase):
	id: int
	likes: int | None
	dislikes: int | None
	author: int

	class Config:
		orm_mode = True


class UserBase(BaseModel):
	username: str
	email: EmailStr


class UserCreate(UserBase):
	password: str


class UserInDB(UserBase):
	class Config:
		orm_mode = True


class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: str | None
