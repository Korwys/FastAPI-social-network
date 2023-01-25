from pydantic import BaseModel, validator


class PostBase(BaseModel):
    title: str
    description: str

    @validator('title')
    def check_title(cls, value: str) -> str:
        """Валидация заголовка поста. Требования: длина более 0, но не более 150 знаков"""
        if len(value.strip()) == 0:
            raise ValueError('Title must contains letters or/and digits but not only spaces.')
        elif len(value) == 0 or len(value) > 150:
            raise ValueError('Title must be less than 150  but more than 0 characters')
        else:
            return value

    @validator('description')
    def check_description(cls, value: str) -> str:
        """Валидация описания. Требования: длина более 0, но не более 5000 знаков"""
        if len(value.strip()) == 0:
            raise ValueError('Description must contains letters or/and digits, but not only spaces.')
        elif len(value) == 0 or len(value) > 5000:
            raise ValueError('Description must over 0 and less 5000 characters')
        else:
            return value


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


class Like(BaseModel):
    post_id: int


class Dislike(BaseModel):
    post_id: int
