import fastapi
from fastapi import Depends, HTTPException,Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from db.config import get_db
from db.crud import add_new_user_in_db, fetch_user_from_db
from db.models import User
from db.schemas import Token, UserCreate, UserInDB
from services.auth import verify_user_password, create_token

router = fastapi.APIRouter()


@router.post("/singup", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def create_user(request: Request, obj_in: UserCreate, db: Session = Depends(get_db)) -> User:
    """
    Create new user:
    - **username**: Username must contain only [a-z] or/and [A-Z] or/and [0-9] and length between 4-15.
    - **password**:Password must contain at least 1 character [A-Z and 0-9] and min length 8 characters.
    - **email**: Must be valid
    - username and email **must be unique**
    """
    new_user = add_new_user_in_db(db=db, obj_in=obj_in, request=request)
    return new_user


@router.post('/login', response_model=Token, status_code=status.HTTP_200_OK)
def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    username = fetch_user_from_db(db, form_data)
    if not username:
        raise HTTPException(status_code=401, detail='Bad credentials')

    user_password = verify_user_password(db=db, user_credentials=form_data)
    if not user_password:
        raise HTTPException(status_code=401, detail='Bad credentials')

    return {
        "access_token": create_token(sub=form_data.username),
        "token_type": "bearer"
    }
