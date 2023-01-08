import fastapi
from fastapi import Depends
from sqlalchemy.orm import Session

from db.config import get_db
from db.crud import change_likes_or_dislikes
from db.models import Likes, Dislikes
from db.schemas import UserInDB
from services.auth import get_current_user

router = fastapi.APIRouter()


@router.post('/api/like/{post_id}')
def add_or_remove_like(post_id: int, db: Session = Depends(get_db),
                       user: UserInDB = Depends(get_current_user)):
	return change_likes_or_dislikes(db, post_id, user, model=Likes)

@router.post('/api/dislike/{post_id}')
def add_or_remove_dislike(post_id: int, db: Session = Depends(get_db),
                       user: UserInDB = Depends(get_current_user)):
	return change_likes_or_dislikes(db, post_id, user, model=Dislikes)
