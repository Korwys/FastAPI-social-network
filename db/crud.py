from sqlalchemy.orm import Session

from db.auth import create_hashed_user_password
from db.models import User
from db.schemas import UserCreate


def add_new_user_in_db(db: Session, obj_in: UserCreate):
	new_data = obj_in.dict()
	new_data.pop('password')
	db_obj = User(**new_data)
	db_obj.hashed_password = create_hashed_user_password(obj_in.password)
	db.add(db_obj)
	db.commit()
	return db_obj
