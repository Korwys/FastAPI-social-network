import re

from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @validator('username')
    def check_username(cls, value: str) -> str:
        """Валидация логина. Логин должен содержать буквы и/или цифры. Длина от 5 до 15 символов."""

        pattern_username = re.compile(r'^[A-Za-z0-9]{4,15}$')

        if not bool(pattern_username.match(value)):
            raise ValueError('Username must contain only [a-z] or [A-Z] or [0-9] and at least 4 characters')
        return value

    @validator('password')
    def check_password(cls, value: str) -> str:
        """Валидация пароля. Пароль должен содержать минимум 1 цифру, 1 заглавную букву и быть более 8 символов"""

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
