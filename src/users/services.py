import logging

from fastapi import HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from users.models import User
from users.schemas import UserCreate
from users.utils import create_hashed_user_password
from users.validators import clearbit_new_user_score_checker, hunter_user_email_checker

logger = logging.getLogger('app.users.services')


async def add_new_user_in_db(db: Session, obj_in: UserCreate, request: Request) -> User:
    """Добавляет новую запись в БД при регистрации пользователя. Если проверка на уникальность логина или емайла не
    проходит, то возвращает код 400 и описание проблемы. Если от clearbit приходит высокий score,
    предполагается логика с капчей и подтверждением емейла,
    но в данной версии эта фича(капча и подтверждение емейла) не реализована еще."""
    clearbit_user_score = await clearbit_new_user_score_checker(user_data=obj_in, request=request)
    hunter_status_score = await hunter_user_email_checker(user_data=obj_in)
    user_in_db = user_uniqueness_check(db=db, user_data=obj_in)

    if not user_in_db and clearbit_user_score != 'high' and not hunter_status_score:
        new_data = obj_in.dict()
        new_data.pop('password')
        db_obj = User(**new_data)
        db_obj.hashed_password = create_hashed_user_password(obj_in.password)
        try:
            db.add(db_obj)
            db.commit()
            return db_obj
        except SQLAlchemyError as err:
            logger.exception(err)
    elif clearbit_user_score == 'high':
        print('Please enter the captcha and confirm your email')
    elif hunter_status_score:
        raise HTTPException(status_code=400, detail='Email is invalid')

    if user_in_db.username == obj_in.username:
        raise HTTPException(status_code=400, detail='Username already exists')

    if user_in_db.email == obj_in.email:
        raise HTTPException(status_code=400, detail='Email already exists')


def user_uniqueness_check(db: Session, user_data: UserCreate):
    """Возвращает из бд юзера(если он есть) для проверки на уникальность данных при регистрации"""
    try:
        user_query = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
        user_db_request = db.execute(user_query)
        return user_db_request.scalar()
    except SQLAlchemyError as err:
        logger.exception(err)


def fetch_user_from_db(db: Session, data):
    """Возвращает юзера по указанному логину"""
    try:
        return db.query(User).where(User.username == data.username).first()
    except SQLAlchemyError as err:
        logger.exception(err)
