import fastapi
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from db.config import get_db
from services.auth import get_current_user

from db.crud import add_new_post_in_db, update_post, remove_post_from_db, check_post_author
from db.models import Post
from db.schemas import PostInDB, PostCreate, UserInDB, PostUpdate
from services.cache import fetch_post_from_cache, fetch_posts_from_cache, change_count_of_users_emotions

router = fastapi.APIRouter()


@router.post('/', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(get_db),
                    user: UserInDB = Depends(get_current_user)) -> Post:
    return add_new_post_in_db(db=db, obj_in=post, user=user)


@router.get('/', response_model=list[PostInDB], status_code=status.HTTP_200_OK)
def get_all_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Post]:
    return fetch_posts_from_cache(quantity=limit, db=db)


@router.get('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def get_post(post_id: int, db: Session = Depends(get_db)) -> Post:
    return fetch_post_from_cache(db=db, post_id=post_id)


@router.patch('/{post_id}', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def edit_post(post_id: int, obj_in: PostUpdate, db: Session = Depends(get_db)
              , user: UserInDB = Depends(get_current_user)) -> Post:
    return update_post(db=db, post_id=post_id, obj_in=obj_in)


@router.delete('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def delete_post(post_id: int, db: Session = Depends(get_db),
                user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    return remove_post_from_db(db, post_id)


@router.post('/like/{post_id}')
def add_or_remove_like(post_id: int, db: Session = Depends(get_db),
                       user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    if check_post_author(db, post_id, user):
        return change_count_of_users_emotions(db=db, user=user, post_id=post_id, table='likes', users='like_user')
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own post")


@router.post('/dislike/{post_id}')
def add_or_remove_dislike(post_id: int, db: Session = Depends(get_db),
                          user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    if check_post_author(db, post_id, user):
        return change_count_of_users_emotions(db=db, user=user, post_id=post_id, table='dislikes', users='dislike_user')
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own post")
