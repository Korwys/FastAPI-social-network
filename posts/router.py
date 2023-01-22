import fastapi
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from config.db import get_db
from posts.cache import fetch_posts_from_cache, fetch_post_from_cache, change_count_of_users_emotions
from posts.models import Post, Likes, Dislikes
from posts.schemas import PostInDB, PostCreate, PostUpdate
from posts.services import add_new_post_in_db, update_post, remove_post_from_db, check_post_author
from users.schemas import UserInDB
from users.utils import get_current_user

post_router = fastapi.APIRouter()


@post_router.post('/', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(get_db),
                    user: UserInDB = Depends(get_current_user)) -> Post:
    return add_new_post_in_db(db=db, obj_in=post, user=user)


@post_router.get('/', response_model=list[PostInDB], status_code=status.HTTP_200_OK)
def get_all_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Post]:
    return fetch_posts_from_cache(quantity=limit, db=db)


@post_router.get('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def get_post(post_id: int, db: Session = Depends(get_db)) -> dict | JSONResponse:
    return fetch_post_from_cache(db=db, post_id=post_id)


@post_router.patch('/{post_id}', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def edit_post(post_id: int, obj_in: PostUpdate, db: Session = Depends(get_db)
              , user: UserInDB = Depends(get_current_user)) -> Post:
    if check_post_author(db, post_id, user):
        return update_post(db=db, post_id=post_id, obj_in=obj_in)
    else:
        raise HTTPException(status_code=400, detail="You can't edit this post. Permission denied.")


@post_router.delete('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def delete_post(post_id: int, db: Session = Depends(get_db),
                user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    if check_post_author(db, post_id, user):
        return remove_post_from_db(db, post_id)
    else:
        raise HTTPException(status_code=400, detail="You can't delete this post. Permission denied.")


@post_router.post('/like/{post_id}')
def add_or_remove_like(post_id: int, db: Session = Depends(get_db),
                       user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    if not check_post_author(db, post_id, user):
        return change_count_of_users_emotions(db=db, user=user, post_id=post_id, users='like_user',model=Likes)
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own posts")


@post_router.post('/dislike/{post_id}')
def add_or_remove_dislike(post_id: int, db: Session = Depends(get_db),
                          user: UserInDB = Depends(get_current_user)) -> JSONResponse:
    if not check_post_author(db, post_id, user):
        return change_count_of_users_emotions(db=db, user=user, post_id=post_id,users='dislike_user',model=Dislikes)
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own posts")
