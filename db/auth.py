import os
from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from .config import get_db
from .models import User
from jose import jwt, JWTError

from .schemas import TokenData

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

ACCESS = int(os.getenv('ACCESS'))
ALGORITHM = os.getenv('ALGORITHM')
SECRET = os.getenv('SECRET')


def create_hashed_user_password(password: str) -> str:
	"""Хэширует пароль"""
	hashed_password = pwd_context.hash(password)
	return hashed_password


def verify_user_password(user_credentials, db: Session = Depends(get_db)):
	""" Сравнивает пароль который юзер ввел при входе с тем хэшированным паролем в базе"""
	hashed_pass = get_user_hashed_password_from_db(username=user_credentials.username, db=db)
	if not pwd_context.verify(user_credentials.password, hashed_pass):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Bad Credentials')
	return user_credentials


def get_user_hashed_password_from_db(username: int, db: Session = Depends(get_db)):
	"""Возвращает хэшированный пароль из БД"""
	user = db.query(User).filter(User.username == username).first()
	return user.hashed_password


def create_token(sub: str):
	"""Создает JWT токен"""
	token_type = "access_token"
	lifetime = timedelta(minutes=ACCESS)
	payload = {'token': token_type, 'exp': datetime.utcnow() + lifetime, 'sub': sub}

	return jwt.encode(payload, SECRET, ALGORITHM)


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
	"""Декодирует JWT и если все ок, то возвращает текущего юзера"""
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)

	try:
		payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
		username = payload.get('sub')
		if username is None:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

		token_data = TokenData(username=username)
	except JWTError:
		raise credentials_exception
	user = db.query(User).filter(User.email == token_data.username).first()
	if user is None:
		raise credentials_exception

	return user
