import fastapi
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import Json
from sqlalchemy.orm import Session

from db.config import get_db
from db.crud import add_new_user_in_db
from db.models import User
from db.schemas import Token, UserCreate, UserInDB
from sevices.auth import verify_user_password, create_token

router = fastapi.APIRouter()


@router.post("/singup", response_model=UserInDB)
async def create_user(obj_in: UserCreate, db: Session = Depends(get_db)) -> User:
	new_user = add_new_user_in_db(db=db, obj_in=obj_in)
	return new_user


@router.post('/login', response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Json:
	username = db.query(User).where(User.username == form_data.username)
	if not username:
		raise HTTPException(status_code=401, detail='Bad credentials')
	user_password = verify_user_password(db=db, user_credentials=form_data)
	if not user_password:
		raise HTTPException(status_code=401, detail='Bad credentials')

	return {
		"access_token": create_token(sub=form_data.username),
		"token_type": "bearer"
	}
