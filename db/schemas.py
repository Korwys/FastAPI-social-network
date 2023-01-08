from pydantic import BaseModel, EmailStr, validator


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

	@validator('username')
	def check_on_numbers_and_letters(cls, value: str):
		if not value.isalnum():
			raise ValueError('Username must contains only letters or/and digits.')
		elif len(value) < 5:
			raise ValueError('Password must be longer than 5 characters')
		else:
			return value

	@validator('password')
	def check_password(cls, value):
		if not value.isalnum():
			raise ValueError('Password must contains only letters and digits.')
		elif len(value) < 8:
			raise ValueError('Password must be longer than 8 characters')
		else:
			return value


class UserInDB(UserBase):
	class Config:
		orm_mode = True


class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: str | None


class Like(BaseModel):
	post_id: int


class Dislike(BaseModel):
	post_id: int
