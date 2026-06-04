from fastapi import FastAPI, HTTPException, status, Request, Depends
from schemas import UserCreate, UserResponse, PostResponse, PostCreate
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import Base, engine, get_db
import models
app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/users", response_model = list[UserResponse])
def get_all_users(db : Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User))
    users = result.scalars().all()
    return users


@app.get("/users/{id}", response_model = UserResponse)
def get_user(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    

@app.post("/CreateUser", response_model= UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db : Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='email already exists')
    
    new_user = models.User(
        name = user.name,
        last_name = user.last_name,
        email = user.email,
        age = user.age,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/")
@app.get("/posts", response_model=PostResponse)
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.get("/posts/{id}")
def get_post(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")


@app.post("/postcreate", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()


    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post