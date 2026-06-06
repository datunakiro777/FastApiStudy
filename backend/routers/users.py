from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from typing import Annotated
from sqlalchemy import select
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate
from fastapi import HTTPException, status, Depends, APIRouter

router = APIRouter()



@router.get("", response_model=list[UserResponse])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).options(selectinload(models.User.posts)))
    users = result.scalars().all()
    return users


@router.get("/{id}", response_model=UserResponse)
async def get_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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


@router.patch("/{id}", response_model=UserResponse)
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


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    await db.delete(user)
    await db.commit()


@router.get("/{id}/posts", response_model=list[PostResponse])
async def get_user_post(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == id)
        .options(selectinload(models.User.posts).selectinload(models.Post.author))
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    return user.posts
