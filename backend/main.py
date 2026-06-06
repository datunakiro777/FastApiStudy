from fastapi import FastAPI, HTTPException, status, Request, Depends
from schemas import UserCreate, UserResponse, PostResponse, PostCreate, PostUpdate, UserUpdate
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


@app.patch("/users/{id}", response_model = UserResponse)
def update_user(id: int, db: Annotated[Session, Depends(get_db)], update_request: UserUpdate):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    if update_request.email is not None and update_request.email != user.email:
        result = db.execute(select(models.User).where(models.User.email == update_request.email))
        if result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        
    if update_request.name is not None:
        user.name = update_request.name

    if update_request.last_name is not None:
        user.last_name = update_request.last_name

    if update_request.age is not None:
        user.age = update_request.age
    
    if update_request.email is not None:
        user.email = update_request.email

    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    db.delete(user)
    db.commit()



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


@app.get("/", response_model=list[PostResponse])
@app.get("/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.get("/posts/{id}")
def get_post(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if post:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
     

@app.put("/posts/{id}", response_model=PostResponse)
def update_post(id: int, db: Annotated[Session, Depends(get_db)], update_request: PostCreate):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    if post.user_id != update_request.user_id:

        result = db.execute(select(models.User).where(models.User.id == update_request.user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    post.title = update_request.title
    post.content = update_request.content
    post.user_id = update_request.user_id
    db.commit()
    db.refresh(post)
    return post


@app.patch("/posts/{id}", response_model=PostResponse)
def update_post_partial(id: int, db: Annotated[Session, Depends(get_db)], update_request: PostUpdate):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    
    update_data = update_request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post
    

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    db.delete(post)
    db.commit()

@app.get("/users/{id}/posts", response_model=list[PostResponse])    
def get_user_post(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    return user.posts


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
