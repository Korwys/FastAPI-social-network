import re

from pydantic import BaseModel, EmailStr, validator


class PostBase(BaseModel):
    title: str
    description: str


class PostCreate(PostBase):
    ...

    @validator('title')
    def check_title(cls, value: str):
        if len(value.strip()) == 0:
            raise ValueError('Title must contains letters or/and digits but not only spaces.')
        elif len(value) == 0 or len(value) > 150:
            raise ValueError('Title must be less than 150  but more than 0 characters')
        else:
            return value

    @validator('description')
    def check_description(cls, value):
        if len(value.strip()) == 0:
            raise ValueError('Description must contains letters or/and digits, but not only spaces.')
        elif len(value) == 0 or len(value) > 5000:
            raise ValueError('Description must over 0 and less 5000 characters')
        else:
            return value


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
    def check_username(cls, value: str) -> str:
        """Вадиладация логина. Логин должен содержать буквы и/или цифры. длина от 5 до 15 символов."""

        pattern_username = re.compile(r'^[A-Za-z0-9]{4,15}$')

        if not bool(pattern_username.match(value)):
            raise ValueError('Username must contain only [a-z] or [A-Z] or [0-9] and at least 4 characters')
        return value

    @validator('password')
    def check_password(cls, value: str) -> str:
        """Валидация пароля. Пароль должен содеражать минимум 1 цифру, 1 заглавную букву и быть длинее 8 символов"""

        pattern_password = re.compile(r'^(?=.*[0-9].*)(?=.*[a-z].*)(?=.*[A-Z].*)[0-9a-zA-Z]{8,}$')

        if not bool(pattern_password.match(value)):
            raise ValueError('Password must contain at least 1 character [A-Z and 0-9] and min length 8 characters ')
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
