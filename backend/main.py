from fastapi import FastAPI, HTTPException, status, Request, Depends
from schemas import UserCreate, UserResponse, PostResponse, PostCreate, PostUpdate, UserUpdate
from typing import Annotated
from sqlalchemy import select
from database import Base, get_db, engine
import models
from contextlib import asynccontextmanager
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/users", response_model = list[UserResponse])
async def get_all_users(db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).options(selectinload(models.User.posts)))
    users = result.scalars().all()
    return users


@app.get("/users/{id}", response_model = UserResponse)
async def get_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@app.patch("/users/{id}", response_model = UserResponse)
async def update_user(id: int, db: Annotated[AsyncSession, Depends(get_db)], update_request: UserUpdate):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    if update_request.email is not None and update_request.email != user.email:
        result = await db.execute(select(models.User).where(models.User.email == update_request.email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        
    if update_request.name is not None:
        user.name = update_request.name

    if update_request.last_name is not None:
        user.last_name = update_request.last_name

    if update_request.age is not None:
        user.age = update_request.age
    
    if update_request.email is not None:
        user.email = update_request.email

    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    await db.delete(user)
    await db.commit()



@app.post("/CreateUser", response_model= UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db : Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.email == user.email))
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
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.get("/", response_model=list[PostResponse])
@app.get("/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts


@app.get("/posts/{id}", response_model=PostResponse)
async def get_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
     

@app.put("/posts/{id}", response_model=PostResponse)
async def update_post(id: int, db: Annotated[AsyncSession, Depends(get_db)], update_request: PostCreate):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    if post.user_id != update_request.user_id:

        result = await db.execute(select(models.User).where(models.User.id == update_request.user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        
        post.author = user
    
    post.title = update_request.title
    post.content = update_request.content
    post.user_id = update_request.user_id
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@app.patch("/posts/{id}", response_model=PostResponse)
async def update_post_partial(id: int, db: Annotated[AsyncSession, Depends(get_db)], update_request: PostUpdate):
    result = await db.execute(select(models.Post).where(models.Post.id == id).options(selectinload(models.Post.author)))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    
    update_data = update_request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    return post
    

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    await db.delete(post)
    await db.commit()

@app.get("/users/{id}/posts", response_model=list[PostResponse])    
async def get_user_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id).options(selectinload(models.User.posts).selectinload(models.Post.author)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    return user.posts


@app.post("/postcreate", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()


    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id,
        author = user
    )
    db.add(new_post)
    await db.commit()
    return new_post
