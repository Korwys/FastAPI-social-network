import fastapi
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from db.config import get_db
from services.auth import get_current_user

from db.crud import add_new_post_in_db, fetch_all_posts_from_db, fetch_one_post, update_post, remove_post_from_db, \
    check_post_author, change_likes_or_dislikes
from db.models import Post, Likes, Dislikes
from db.schemas import PostInDB, PostCreate, UserInDB, PostUpdate

router = fastapi.APIRouter()


@router.post('/', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def create_new_post(post: PostCreate, db: Session = Depends(get_db),
                    user: UserInDB = Depends(get_current_user)) -> Post:
    return add_new_post_in_db(db=db, obj_in=post, user=user)


@router.get('/', response_model=list[PostInDB], status_code=status.HTTP_200_OK)
def get_all_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Post]:
    return fetch_all_posts_from_db(db, skip, limit)


@router.get('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def get_post(post_id: int, db: Session = Depends(get_db)) -> Post:
    return fetch_one_post(db=db, post_id=post_id)


@router.patch('/{post_id}', response_model=PostInDB, status_code=status.HTTP_201_CREATED)
def edit_post(post_id: int, obj_in: PostUpdate, db: Session = Depends(get_db)
              , user: UserInDB = Depends(get_current_user)) -> Post:
    return update_post(db=db, db_obj=get_post(post_id, db), obj_in=obj_in)


@router.delete('/{post_id}', response_model=PostInDB, status_code=status.HTTP_200_OK)
def delete_post(post_id: int, db: Session = Depends(get_db),
                user: UserInDB = Depends(get_current_user)) -> Post:
    return remove_post_from_db(db, post_id, user)


@router.post('/like/{post_id}')
def add_or_remove_like(post_id: int, db: Session = Depends(get_db), user: UserInDB = Depends(get_current_user)) -> None:
    if check_post_author(db, post_id, user):
        change_likes_or_dislikes(db, post_id, user, model=Likes)
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own post")


@router.post('/dislike/{post_id}')
def add_or_remove_dislike(post_id: int, db: Session = Depends(get_db),
                          user: UserInDB = Depends(get_current_user)) -> None:
    if check_post_author(db, post_id, user):
        change_likes_or_dislikes(db, post_id, user, model=Dislikes)
    else:
        raise HTTPException(status_code=400, detail="You can't like or dislike your own post")
